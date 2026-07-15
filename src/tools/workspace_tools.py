"""工作区工具 — 沙箱约束 + 文件操作。

所有路径仅接受相对路径，resolve() 后必须在 WORKING_DIR 下。
"""

import shutil

from pathlib import Path

from charset_normalizer import from_path

from src.agents.registry import RESUME_AGENT_KEY
from src.config import config
from src.tools.registry import ConfirmMode, tool
from src.tools.exceptions import ToolCallException
from src.utils.file_reader import list_directory, read_text, search_text


def _validate_path(relative_path: str) -> Path:
    """校验相对路径并返回沙箱内的绝对路径。

    Raises:
        ToolCallException: 绝对路径 或 路径穿越。
    """
    p = Path(relative_path)
    if p.is_absolute():
        raise ToolCallException(
            f"path must be relative, got: {relative_path}",
            suggestion="请使用相对路径，基于工作区根目录",
        )

    working_dir = Path(config.WORKING_DIR).resolve()
    resolved = (working_dir / p).resolve()
    if not str(resolved).startswith(str(working_dir)):
        raise ToolCallException(
            f"path escapes workspace: {relative_path}",
            suggestion="路径超出工作区范围，请检查后重试",
        )

    return resolved


# ═══════════════════════════════════════════════════════════════════
# 免审批工具（读操作）
# ═══════════════════════════════════════════════════════════════════


@tool(
    purpose="读取工作区内的文本文件，返回带行号的结构化内容。行号可后续用于 workspace_edit 精确替换。",
    use_when="需要查看工作区内某个文件的内容时",
    do_not_use_when="文件不存在 或 path 是目录时",
    expected_output='{"path": "...", "total_lines": N, "offset": 1, "limit": 100, "truncated": false, "lines": [[1, "..."], ...]}',
    input_schema={
        "path": {
            "description": "文件相对路径，基于工作区根目录。例如 'output/main.tex'",
        },
        "offset": {
            "description": "起始行号（1-indexed），默认从第 1 行开始",
            "default": 1,
        },
        "limit": {
            "description": "最多返回的行数，默认 100 行",
            "default": 100,
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.NEVER,
)
def workspace_read(path: str, offset: int = 1, limit: int = 100) -> dict:
    full = _validate_path(path)
    return read_text(full, offset=offset, limit=limit)


@tool(
    purpose="列出工作区内目录的内容（仅单层，不递归子目录）。",
    use_when="需要了解工作区某个目录下有哪些文件和子目录时",
    do_not_use_when="path 不是目录时",
    expected_output='{"path": ".", "entries": [{"name": "main.tex", "type": "file"}, {"name": "sections", "type": "dir"}]}',
    input_schema={
        "path": {
            "description": "目录相对路径，默认 '.' 即工作区根目录",
            "default": ".",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.NEVER,
)
def workspace_list(path: str = ".") -> dict:
    full = _validate_path(path)
    return list_directory(full)


@tool(
    purpose="在工作区内搜索文件内容（类似 grep），返回匹配的行号和内容。不提供上下文行，需要时自行调 workspace_read。",
    use_when="需要查找包含特定内容的文件时；先用 workspace_search_file 定位文件再用 grep 搜索内容效率更高",
    do_not_use_when="不确定搜索范围时 — 先用 workspace_list 了解目录结构",
    expected_output='{"pattern": "...", "regex": false, "total_matches": N, "files": [{"path": "...", "matches": [[line, content], ...]}]}',
    input_schema={
        "pattern": {
            "description": "搜索字符串（或正则表达式，当 regex=true 时）",
        },
        "path": {
            "description": "搜索范围（相对路径）。可以是文件或目录，默认 '.' 即整个工作区",
            "default": ".",
        },
        "glob": {
            "description": "文件名过滤 glob 模式，如 '*.tex'、'*.md'，不填则搜索所有文本文件",
            "default": None,
        },
        "regex": {
            "description": "是否将 pattern 作为正则表达式解析，默认 false",
            "default": False,
        },
        "max_matches": {
            "description": "匹配结果上限，达到后截断，默认 50",
            "default": 50,
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.NEVER,
)
def workspace_grep(
    pattern: str,
    path: str = ".",
    glob: str | None = None,
    regex: bool = False,
    max_matches: int = 50,
) -> dict:
    full = _validate_path(path)
    return search_text(
        Path(config.WORKING_DIR).resolve(),
        pattern,
        path=path,
        glob=glob,
        regex=regex,
        max_matches=max_matches,
    )


@tool(
    purpose="按文件名搜索工作区内的文件（fnmatch glob），返回匹配的文件相对路径列表。",
    use_when="需要查找特定名称模式的文件时，如 '*.tex'、'resume*'",
    do_not_use_when="需要搜索文件内容时 — 用 workspace_grep",
    expected_output='{"pattern": "*.tex", "path": ".", "total_results": N, "files": ["main.tex", "sections/skills.tex"]}',
    input_schema={
        "pattern": {
            "description": "文件名匹配模式（fnmatch glob），如 '*.tex'、'main*'",
        },
        "path": {
            "description": "搜索范围（相对路径）。目录时递归搜索子目录，默认 '.' 即整个工作区",
            "default": ".",
        },
        "max_results": {
            "description": "结果上限，达到后截断，默认 50",
            "default": 50,
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.NEVER,
)
def workspace_search_file(
    pattern: str,
    path: str = ".",
    max_results: int = 50,
) -> dict:
    import fnmatch

    full = _validate_path(path)

    if full.is_file():
        files = [full]
    else:
        files = []
        for f in full.rglob("*"):
            if f.is_file() and fnmatch.fnmatch(f.name, pattern):
                files.append(f)
                if len(files) >= max_results:
                    break

    working_dir = Path(config.WORKING_DIR).resolve()
    results = [str(f.relative_to(working_dir)) for f in sorted(files, key=lambda p: str(p))]

    return {
        "pattern": pattern,
        "path": path,
        "total_results": len(results),
        "truncated": len(results) >= max_results,
        "max_results": max_results,
        "files": results[:max_results],
    }


# ═══════════════════════════════════════════════════════════════════
# 审批工具（写操作）
# ═══════════════════════════════════════════════════════════════════


@tool(
    purpose="将文件中所有匹配的字符串全部替换为新字符串，返回替换次数。",
    use_when="需要对工作区文件做简单字符串替换时，如全局替换名称、关键字等",
    do_not_use_when="需要精确的行级修改时 — 用 workspace_edit；需要新建文件时 — 用 workspace_write",
    expected_output='{"path": "...", "replacements": N}',
    input_schema={
        "path": {
            "description": "文件相对路径，基于工作区根目录",
        },
        "old_str": {
            "description": "要被替换的字符串（匹配所有出现处）",
        },
        "new_str": {
            "description": "替换后的新字符串",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def workspace_replace(path: str, old_str: str, new_str: str) -> dict:
    full = _validate_path(path)
    if not full.is_file():
        raise ToolCallException(
            f"file not found or is a directory: {path}",
            suggestion="用 workspace_list 确认目标路径",
        )

    detected = from_path(full)
    content = str(detected.best())
    count = content.count(old_str)
    if count > 0:
        content = content.replace(old_str, new_str)
        full.write_text(content, encoding="utf-8", newline="")
    return {"path": path, "replacements": count}


@tool(
    purpose="在工作区内创建新文件（不含父目录自动创建）。目标已存在时拒绝覆盖。",
    use_when="需要新建文件时",
    do_not_use_when="目标文件已存在时 — 用 workspace_edit 或 workspace_replace 修改；需要覆盖时先 workspace_delete 再 write",
    expected_output='{"path": "...", "written": true}',
    input_schema={
        "path": {
            "description": "新文件相对路径，基于工作区根目录。父目录不存在时自动创建",
        },
        "content": {
            "description": "要写入文件的完整文本内容",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def workspace_write(path: str, content: str) -> dict:
    full = _validate_path(path)
    if full.exists():
        raise ToolCallException(
            f"file already exists: {path}",
            suggestion="用 workspace_edit 或 workspace_replace 修改已有文件，或先 workspace_delete 删除后再创建",
        )

    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8", newline="")
    return {"path": path, "written": True}


@tool(
    purpose="删除工作区内的文件或空目录。目录非空时拒绝删除。",
    use_when="需要删除工作区文件或清理空目录时",
    do_not_use_when="目录非空时 — 需先逐文件删除再删目录",
    expected_output='{"path": "...", "deleted": true}',
    input_schema={
        "path": {
            "description": "要删除的文件或空目录相对路径",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def workspace_delete(path: str) -> dict:
    full = _validate_path(path)
    if not full.exists():
        raise ToolCallException(
            f"path not found: {path}",
            suggestion="用 workspace_list 确认目标路径",
        )
    if full.is_dir():
        try:
            full.rmdir()
        except OSError as e:
            raise ToolCallException(
                f"directory not empty: {path}",
                suggestion="先用 workspace_delete 删除目录中的文件，再删除空目录",
            ) from e
    else:
        full.unlink()
    return {"path": path, "deleted": True}


@tool(
    purpose="移动或重命名工作区内的文件或目录。目标已存在时拒绝覆盖，目标父目录自动创建。",
    use_when="需要重命名文件/目录、移动到子目录或跨目录整理文件时",
    do_not_use_when="目标路径已存在时",
    expected_output='{"src": "...", "dst": "...", "moved": true}',
    input_schema={
        "src": {
            "description": "源文件或目录的相对路径",
        },
        "dst": {
            "description": "目标相对路径。dst 已存在时报错；dst 父目录不存在时自动创建",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def workspace_move(src: str, dst: str) -> dict:
    src_full = _validate_path(src)
    dst_full = _validate_path(dst)

    if not src_full.exists():
        raise ToolCallException(
            f"src not found: {src}",
            suggestion="用 workspace_list 确认源路径",
        )
    if dst_full.exists():
        raise ToolCallException(
            f"dst already exists: {dst}",
            suggestion="删除目标路径后再移动，或选择不同的目标路径",
        )

    dst_full.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_full), str(dst_full))
    return {"src": src, "dst": dst, "moved": True}


@tool(
    purpose=(
        "精确编辑工作区文件中的指定行。支持 replace（替换当行）和 insert_after（行后插入），"
        "可一次提交多行编辑。系统内部按行号降序处理，所有编辑引用修改前的原始行号。"
        "old_content 必须与当前行内容完全一致（line=0 且 insert_after 时除外），任何一条校验失败全部回滚。"
    ),
    use_when="需要精确修改文件的特定行时 — 必须先调 workspace_read 获取精确的行号和内容",
    do_not_use_when="简单字符串替换用 workspace_replace；新建文件用 workspace_write",
    expected_output='{"path": "...", "edits_applied": N, "edits": [{"action": "...", "line": N, "status": "applied"}]}',
    input_schema={
        "path": {
            "description": "要编辑的文件相对路径",
        },
        "edits": {
            "description": (
                "编辑操作列表，按原始行号引用（任意顺序均可），系统自动从高行号到低行号倒序处理。\n"
                "每个条目包含：\n"
                "  action: 'replace'（替换该行）| 'insert_after'（该行后插入）\n"
                "  line: 行号（1-indexed）；insert_after 时 0=文件开头\n"
                "  old_content: 当前行内容（精确校验）；line=0 + insert_after 时不校验\n"
                "  content: replace→新行内容；insert_after→插入内容（\\n 分隔多行）"
            ),
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def workspace_edit(path: str, edits: list) -> dict:
    full = _validate_path(path)
    if not full.is_file():
        raise ToolCallException(
            f"file not found or is a directory: {path}",
            suggestion="用 workspace_list 确认目标路径",
        )

    # 读取原始内容
    detected = from_path(full)
    original = str(detected.best())
    lines = original.split("\n")

    # 按行号降序排列，从后往前处理避免行号漂移
    sorted_edits = sorted(edits, key=lambda e: e.get("line", 0), reverse=True)
    results: list[dict] = []

    for edit in sorted_edits:
        action = edit.get("action", "")
        line = edit.get("line", 0)
        old_content = edit.get("old_content", "")
        content = edit.get("content", "")

        if action == "replace":
            if line < 1 or line > len(lines):
                raise ToolCallException(
                    f"replace: line {line} out of range (1..{len(lines)})",
                    suggestion="用 workspace_read 确认有效行号",
                )
            actual = lines[line - 1]
            if actual != old_content:
                raise ToolCallException(
                    f"line {line} content mismatch: expected {old_content!r} got {actual!r}",
                    suggestion=f"用 workspace_read offset={line} limit=1 获取该行准确内容后重试",
                )
            lines[line - 1] = content
            results.append({"action": "replace", "line": line, "status": "applied"})

        elif action == "insert_after":
            if line == 0:
                # 插入文件开头，不校验 old_content
                insert_lines = content.split("\n")
                for i in reversed(range(len(insert_lines))):
                    lines.insert(0, insert_lines[i])
                results.append({"action": "insert_after", "line": 0, "status": "applied"})
            else:
                if line < 1 or line > len(lines):
                    raise ToolCallException(
                        f"insert_after: line {line} out of range (1..{len(lines)})",
                        suggestion="用 workspace_read 确认有效行号",
                    )
                actual = lines[line - 1]
                if actual != old_content:
                    raise ToolCallException(
                        f"line {line} content mismatch: expected {old_content!r} got {actual!r}",
                        suggestion=f"用 workspace_read offset={line} limit=1 获取该行准确内容后重试",
                    )
                insert_lines = content.split("\n")
                for i in reversed(range(len(insert_lines))):
                    lines.insert(line, insert_lines[i])
                results.append({"action": "insert_after", "line": line, "status": "applied"})

        else:
            raise ToolCallException(
                f"unknown action: {action}",
                suggestion="action 只支持 'replace' 或 'insert_after'",
            )

    # 写回文件
    full.write_text("\n".join(lines), encoding="utf-8", newline="")
    return {"path": path, "edits_applied": len(results), "edits": results}
