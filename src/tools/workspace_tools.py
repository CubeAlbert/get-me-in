"""工作区工具 — 沙箱约束 + 文件操作。

所有路径仅接受相对路径，resolve() 后必须在 WORKING_DIR 下。
"""

import shutil

from pathlib import Path

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
