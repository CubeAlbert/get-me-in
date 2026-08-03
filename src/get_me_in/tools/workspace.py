"""Workspace tool definitions backed solely by WorkspacePort."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.tools import (
    ConfirmationMode,
    ToolDefinition,
    ToolFailure,
    ToolHandlerContext,
    ToolParameter,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)
from src.get_me_in.domain.agents import Capability
from src.get_me_in.ports.workspace import RevisionMismatchError, WorkspaceError, WorkspacePort
from src.get_me_in.ports.frontend import FrontendPort


class WorkspaceToolContext(ToolHandlerContext, Protocol):
    workspace: WorkspacePort | None
    frontend: FrontendPort | None
    workspace_access: object | None


def build_workspace_tools(
    read_default_limit: int,
    search_max_matches: int,
    file_search_max_results: int,
) -> tuple[ToolDefinition, ...]:
    """Build the capability-scoped workspace tools."""
    def workspace_read(
        arguments: Mapping[str, object], context: WorkspaceToolContext
    ) -> ToolSuccess | ToolFailure:
        return _read(arguments, context, default_limit=read_default_limit)

    def workspace_grep(
        arguments: Mapping[str, object], context: WorkspaceToolContext
    ) -> ToolSuccess | ToolFailure:
        return _grep(arguments, context, default_max_matches=search_max_matches)

    def workspace_search_file(
        arguments: Mapping[str, object], context: WorkspaceToolContext
    ) -> ToolSuccess | ToolFailure:
        return _search_file(
            arguments, context, default_max_results=file_search_max_results
        )

    return (
        ToolDefinition(
            name="workspace_read",
            purpose="读取工作区内的文本文件，返回带行号的结构化内容和 revision。行号、内容与 revision 可用于 workspace_edit 精确修改。",
            use_when="需要查看工作区内某个文件的内容时",
            do_not_use_when="文件不存在或 path 是目录时",
            expected_output=f'{{"path": "...", "revision": "...", "total_lines": N, "offset": 1, "limit": {read_default_limit}, "truncated": false, "lines": [[1, "..."], ...]}}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "文件相对路径，基于工作区根目录。例如 'output/main.tex'",
                    ),
                    "offset": ToolParameter(
                        int,
                        "起始行号（1-indexed），默认从第 1 行开始",
                        default=1,
                    ),
                    "limit": ToolParameter(
                        int,
                        f"最多返回的行数，默认 {read_default_limit} 行",
                        default=read_default_limit,
                    ),
                },
                frozenset({"path"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_READ})),
            handler=workspace_read,
        ),
        ToolDefinition(
            name="workspace_list",
            purpose="列出工作区内目录的内容（仅单层，不递归子目录）。",
            use_when="需要了解工作区某个目录下有哪些文件和子目录时",
            do_not_use_when="path 不是目录时",
            expected_output='{"path": ".", "entries": [{"name": "main.tex", "type": "file"}, {"name": "sections", "type": "dir"}]}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "目录相对路径，默认 '.' 即工作区根目录",
                        default=".",
                    )
                }
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_READ})),
            handler=_list,
        ),
        ToolDefinition(
            name="workspace_grep",
            purpose="在工作区内搜索文件内容（类似 grep），返回匹配的行号和内容。不提供上下文行，需要时自行调用 workspace_read。",
            use_when="需要查找包含特定内容的文件时；先用 workspace_search_file 定位文件再用 grep 搜索内容效率更高",
            do_not_use_when="不确定搜索范围时 — 先用 workspace_list 了解目录结构",
            expected_output='{"pattern": "...", "total_matches": N, "files": {"path": [[line, content]]}, "truncated": false}',
            schema=ToolSchema(
                {
                    "pattern": ToolParameter(
                        str,
                        "搜索字符串（或正则表达式，当 regex=true 时）",
                    ),
                    "path": ToolParameter(
                        str,
                        "搜索范围（相对路径）。可以是文件或目录，默认 '.' 即整个工作区",
                        default=".",
                    ),
                    "glob": ToolParameter(
                        str,
                        "文件名过滤 glob 模式，如 '*.tex'、'*.md'，不填则搜索所有文本文件",
                        default=None,
                        nullable=True,
                    ),
                    "regex": ToolParameter(
                        bool,
                        "是否将 pattern 作为正则表达式解析，默认 false",
                        default=False,
                    ),
                    "max_matches": ToolParameter(
                        int,
                        f"匹配结果上限，达到后截断，默认 {search_max_matches}",
                        default=search_max_matches,
                    ),
                },
                frozenset({"pattern"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_READ})),
            handler=workspace_grep,
        ),
        ToolDefinition(
            name="workspace_search_file",
            purpose="按文件名搜索工作区内的文件（fnmatch glob），返回匹配的文件相对路径列表。",
            use_when="需要查找特定名称模式的文件时，如 '*.tex'、'resume*'",
            do_not_use_when="需要搜索文件内容时 — 用 workspace_grep",
            expected_output='{"pattern": "*.tex", "total_results": N, "files": ["main.tex", "sections/skills.tex"], "truncated": false}',
            schema=ToolSchema(
                {
                    "pattern": ToolParameter(
                        str,
                        "文件名匹配模式（fnmatch glob），如 '*.tex'、'main*'",
                    ),
                    "path": ToolParameter(
                        str,
                        "搜索范围（相对路径）。目录时递归搜索子目录，默认 '.' 即整个工作区",
                        default=".",
                    ),
                    "max_results": ToolParameter(
                        int,
                        f"结果上限，达到后截断，默认 {file_search_max_results}",
                        default=file_search_max_results,
                    ),
                },
                frozenset({"pattern"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_READ})),
            handler=workspace_search_file,
        ),
        ToolDefinition(
            name="workspace_replace",
            purpose="将文件中所有匹配的字符串全部替换为新字符串，返回替换次数。前置条件：必须先通过 workspace_read 读完完整文件或 workspace_grep 确认全部匹配位置；未掌握全部匹配项时应使用 workspace_edit 逐处精确修改。",
            use_when="需要对工作区文件做全局替换，且已通过 workspace_read 全文或 workspace_grep 确认了所有匹配位置时",
            do_not_use_when="未读完文件完整内容、未确认所有匹配位置时 — 必须用 workspace_edit；需要精确的行级修改时 — 用 workspace_edit；需要新建文件时 — 用 workspace_write",
            expected_output='{"path": "...", "replacements": N}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "文件相对路径，基于工作区根目录",
                    ),
                    "old_str": ToolParameter(
                        str,
                        "要被替换的字符串（匹配所有出现处）",
                    ),
                    "new_str": ToolParameter(str, "替换后的新字符串"),
                },
                frozenset({"path", "old_str", "new_str"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_WRITE}), ConfirmationMode.ALWAYS),
            handler=_replace,
        ),
        ToolDefinition(
            name="workspace_write",
            purpose="在工作区内创建新文件，自动创建父目录；目标已存在时拒绝覆盖。",
            use_when="需要新建文件时",
            do_not_use_when="目标文件已存在时 — 用 workspace_edit 或 workspace_replace 修改；需要覆盖时先 workspace_delete 再 write",
            expected_output='{"path": "...", "written": true}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "新文件相对路径，基于工作区根目录。父目录不存在时自动创建",
                    ),
                    "content": ToolParameter(str, "要写入文件的完整文本内容"),
                },
                frozenset({"path", "content"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_WRITE}), ConfirmationMode.ALWAYS),
            handler=_write,
        ),
        ToolDefinition(
            name="workspace_delete",
            purpose="批量删除工作区内的文件或空目录。目录非空时拒绝删除。支持一次删除多个路径。",
            use_when="需要删除工作区文件或清理空目录时，可一次删除多个",
            do_not_use_when="目录非空时 — 需先逐文件删除再删目录",
            expected_output='{"deleted": ["...", "..."], "errors": []}',
            schema=ToolSchema(
                {
                    "paths": ToolParameter(
                        list,
                        "要删除的文件或空目录相对路径列表，如 ['main.aux', 'main.log']",
                        items=str,
                    )
                },
                frozenset({"paths"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_WRITE}), ConfirmationMode.ALWAYS),
            handler=_delete,
        ),
        ToolDefinition(
            name="workspace_move",
            purpose="移动或重命名工作区内的文件或目录。目标已存在时拒绝覆盖，目标父目录自动创建。",
            use_when="需要重命名文件/目录、移动到子目录或跨目录整理文件时",
            do_not_use_when="目标路径已存在时",
            expected_output='{"src": "...", "dst": "...", "moved": true}',
            schema=ToolSchema(
                {
                    "src": ToolParameter(str, "源文件或目录的相对路径"),
                    "dst": ToolParameter(
                        str,
                        "目标相对路径。dst 已存在时报错；dst 父目录不存在时自动创建",
                    ),
                },
                frozenset({"src", "dst"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_WRITE}), ConfirmationMode.ALWAYS),
            handler=_move,
        ),
        ToolDefinition(
            name="workspace_edit",
            purpose="基于 workspace_read 返回的 revision 精确编辑工作区文件。用新内容替换指定行，可一次提交多行编辑；所有行号引用修改前的原始文件，任一 revision、行号或原内容校验失败则不写入。",
            use_when="需要精确修改文件的特定行、插入新行或删除行时；每次成功 edit 后都必须先调用 workspace_read 获取最新 revision、行号和内容",
            do_not_use_when="已确认全部匹配位置的全局替换用 workspace_replace；新建文件用 workspace_write；没有当前 revision 或文件可能已变化时必须重新 workspace_read",
            expected_output='{"path": "...", "revision": "...", "edits_applied": N, "edits": [{"line": N, "status": "applied"}]}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "要编辑的文件相对路径",
                    ),
                    "revision": ToolParameter(
                        str,
                        "最近一次 workspace_read 返回的文件 revision；每次成功 workspace_edit 后必须重新 workspace_read，不能直接复用 edit 返回的 revision",
                    ),
                    "edits": ToolParameter(
                        list,
                        "编辑操作列表，按原始行号引用。每项包含 {line, old_content, content}：line 是 1-indexed 行号；old_content 必须与当前行完全一致；content 是替换内容，可含换行，空字符串表示删除该行。",
                        items=dict,
                    ),
                },
                frozenset({"path", "revision", "edits"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_WRITE}), ConfirmationMode.ALWAYS),
            handler=_edit,
        ),
        ToolDefinition(
            name="workspace_open",
            purpose="用系统默认工具打开工作区中的文件（如 PDF 预览）。",
            use_when="需要让用户预览生成的文件（如 PDF）时",
            do_not_use_when="文件不存在时",
            expected_output='{"path": "...", "opened": true}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "要打开的文件相对路径，基于工作区根目录",
                    )
                },
                frozenset({"path"}),
            ),
            policy=ToolPolicy(frozenset({Capability.WORKSPACE_OPEN}), ConfirmationMode.ALWAYS),
            handler=_open,
        ),
    )


def _read(
    arguments: Mapping[str, object],
    context: WorkspaceToolContext,
    *,
    default_limit: int,
) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    path = Path(arguments["path"])
    offset = arguments.get("offset", 1)
    limit = arguments.get("limit", default_limit)
    if offset < 1 or limit < 1:
        return ToolFailure("invalid_range", "offset and limit must be positive")
    try:
        snapshot = workspace.read(path)
        all_lines = snapshot.content.splitlines()
        lines = tuple(
            (index + 1, value)
            for index, value in enumerate(
                all_lines[offset - 1 : offset - 1 + limit], offset - 1
            )
        )
        if context.workspace_access is not None:
            context.workspace_access.authorize_read(
                context.session_id, snapshot.path, snapshot.revision
            )
    except (OSError, UnicodeError, WorkspaceError, ValueError) as error:
        return ToolFailure("workspace_read_failed", str(error))
    return ToolSuccess(
        {
            "path": str(snapshot.path),
            "revision": snapshot.revision,
            "total_lines": len(all_lines),
            "offset": offset,
            "limit": limit,
            "truncated": offset - 1 + len(lines) < len(all_lines),
            "lines": lines,
        }
    )


def _list(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    path = Path(arguments.get("path", "."))
    try:
        entries = workspace.list(path)
    except (OSError, WorkspaceError) as error:
        return ToolFailure("workspace_list_failed", str(error))
    return ToolSuccess(
        {
            "path": str(path),
            "entries": tuple(
                {"name": entry.path.name, "type": "dir" if entry.is_directory else "file"}
                for entry in entries
            ),
        }
    )


def _grep(
    arguments: Mapping[str, object],
    context: WorkspaceToolContext,
    *,
    default_max_matches: int,
) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    max_matches = arguments.get("max_matches", default_max_matches)
    try:
        matches = workspace.search(
            arguments["pattern"], path=Path(arguments.get("path", ".")),
            glob=arguments.get("glob") or "**/*", regex=arguments.get("regex", False), max_matches=max_matches,
        )
    except (OSError, ValueError, WorkspaceError) as error:
        return ToolFailure("workspace_search_failed", str(error))
    files: dict[str, list[tuple[int, str]]] = {}
    for match in matches:
        files.setdefault(str(match.path), []).append((match.line.number, match.line.content))
    return ToolSuccess({"pattern": arguments["pattern"], "total_matches": len(matches), "files": files,
                        "truncated": len(matches) >= max_matches})


def _search_file(
    arguments: Mapping[str, object],
    context: WorkspaceToolContext,
    *,
    default_max_results: int,
) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    max_results = arguments.get("max_results", default_max_results)
    try:
        files = workspace.find_files(arguments["pattern"], path=Path(arguments.get("path", ".")), max_results=max_results)
    except (OSError, ValueError, WorkspaceError) as error:
        return ToolFailure("workspace_search_failed", str(error))
    return ToolSuccess({"pattern": arguments["pattern"], "files": tuple(str(file) for file in files),
                        "total_results": len(files), "truncated": len(files) >= max_results})


def _replace(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure): return workspace
    path = Path(arguments["path"])
    try:
        snapshot = workspace.read(path)
        replacements = snapshot.content.count(arguments["old_str"])
        if replacements:
            workspace.write(path, snapshot.content.replace(arguments["old_str"], arguments["new_str"]))
    except (OSError, UnicodeError, WorkspaceError) as error:
        return ToolFailure("workspace_replace_failed", str(error))
    return ToolSuccess({"path": str(path), "replacements": replacements})


def _write(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure): return workspace
    path = Path(arguments["path"])
    try:
        workspace.write(path, arguments["content"], replace=False)
    except FileExistsError:
        return ToolFailure("workspace_path_exists", f"File already exists: {path}")
    except (OSError, WorkspaceError) as error:
        return ToolFailure("workspace_write_failed", str(error))
    return ToolSuccess({"path": str(path), "written": True})


def _delete(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure): return workspace
    try:
        result = workspace.delete_many(tuple(Path(path) for path in arguments["paths"]))
    except (TypeError, WorkspaceError) as error:
        return ToolFailure("workspace_delete_failed", str(error))
    return ToolSuccess({"deleted": tuple(str(path) for path in result.deleted),
                        "errors": tuple({"path": str(item.path), "error": item.message} for item in result.failures)})


def _move(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure): return workspace
    try:
        workspace.move(Path(arguments["src"]), Path(arguments["dst"]))
    except (OSError, WorkspaceError) as error:
        return ToolFailure("workspace_move_failed", str(error))
    return ToolSuccess({"src": arguments["src"], "dst": arguments["dst"], "moved": True})


def _edit(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure): return workspace
    path = Path(arguments["path"])
    try:
        if context.workspace_access is None:
            return ToolFailure(
                "workspace_access_unavailable",
                "Revision-aware edit requires session-scoped workspace access state",
            )
        snapshot = workspace.read(path)
        context.workspace_access.require_revision(
            context.session_id, snapshot.path, arguments["revision"]
        )
        if snapshot.revision != arguments["revision"]:
            return ToolFailure("workspace_revision_mismatch", "Read the file again before editing")
        lines = snapshot.content.splitlines()
        applied: list[dict[str, object]] = []
        for edit in sorted(arguments["edits"], key=lambda item: item["line"], reverse=True):
            line, old_content, content = edit["line"], edit["old_content"], edit["content"]
            if not isinstance(line, int) or line < 1 or line > len(lines):
                return ToolFailure("workspace_edit_invalid_line", f"Line {line} is out of range")
            if lines[line - 1] != old_content:
                return ToolFailure("workspace_edit_content_mismatch", f"Line {line} no longer matches")
            lines[line - 1 : line] = content.split("\n") if content else []
            applied.append({"line": line, "status": "applied"})
        updated = workspace.edit(path, snapshot.revision, "\n".join(lines))
        context.workspace_access.consume_revision(
            context.session_id, updated.path, snapshot.revision
        )
    except RevisionMismatchError:
        return ToolFailure("workspace_revision_mismatch", "Read the file again before editing")
    except (KeyError, TypeError, OSError, WorkspaceError) as error:
        return ToolFailure("workspace_edit_failed", str(error))
    return ToolSuccess({"path": str(path), "revision": updated.revision, "edits_applied": len(applied), "edits": tuple(applied)})


def _open(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure): return workspace
    if context.frontend is None:
        return ToolFailure("frontend_unavailable", "This tool requires a configured frontend")
    path = Path(arguments["path"])
    try:
        resolved = workspace.resolve(path)
        if not resolved.is_file():
            return ToolFailure("workspace_file_not_found", f"File not found: {path}")
        context.frontend.open_file(resolved)
    except (OSError, WorkspaceError) as error:
        return ToolFailure("workspace_open_failed", str(error))
    return ToolSuccess({"path": str(path), "opened": True})


def _workspace(context: WorkspaceToolContext) -> WorkspacePort | ToolFailure:
    if context.workspace is None:
        return ToolFailure("workspace_unavailable", "This tool requires a configured workspace")
    return context.workspace
