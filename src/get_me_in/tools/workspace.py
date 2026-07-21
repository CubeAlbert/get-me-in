"""Workspace tool definitions backed solely by WorkspacePort."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.tools import (
    ConfirmationMode,
    ToolDefinition,
    ToolFailure,
    ToolHandlerContext,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)
from src.get_me_in.ports.workspace import WorkspaceError, WorkspacePort


class WorkspaceToolContext(ToolHandlerContext, Protocol):
    workspace: WorkspacePort | None


def build_workspace_tools() -> tuple[ToolDefinition, ...]:
    """Build the read-only v2 workspace tools."""
    return (
        ToolDefinition(
            name="workspace_read",
            description="读取工作区文本文件，返回一基行号与文件 revision。",
            schema=ToolSchema({"path": str, "offset": int, "limit": int}, frozenset({"path"})),
            policy=ToolPolicy(),
            handler=_read,
        ),
        ToolDefinition(
            name="workspace_list",
            description="列出工作区目录的单层文件与子目录。",
            schema=ToolSchema({"path": str}),
            policy=ToolPolicy(),
            handler=_list,
        ),
        ToolDefinition(
            name="workspace_grep",
            description="在受限工作区中搜索文本，可按路径、glob 和正则表达式过滤。",
            schema=ToolSchema(
                {"pattern": str, "path": str, "glob": str, "regex": bool, "max_matches": int},
                frozenset({"pattern"}),
            ),
            policy=ToolPolicy(),
            handler=_grep,
        ),
        ToolDefinition(
            name="workspace_search_file",
            description="按文件名 glob 递归搜索受限工作区文件。",
            schema=ToolSchema({"pattern": str, "path": str, "max_results": int}, frozenset({"pattern"})),
            policy=ToolPolicy(),
            handler=_search_file,
        ),
        ToolDefinition(
            name="workspace_replace",
            description="原子替换文件内全部匹配文本。",
            schema=ToolSchema({"path": str, "old_str": str, "new_str": str}, frozenset({"path", "old_str", "new_str"})),
            policy=ToolPolicy(confirmation=ConfirmationMode.ALWAYS),
            handler=_replace,
        ),
        ToolDefinition(
            name="workspace_write",
            description="创建新的工作区文本文件，拒绝覆盖已有文件。",
            schema=ToolSchema({"path": str, "content": str}, frozenset({"path", "content"})),
            policy=ToolPolicy(confirmation=ConfirmationMode.ALWAYS),
            handler=_write,
        ),
        ToolDefinition(
            name="workspace_delete",
            description="批量删除工作区文件或空目录，并返回逐路径结果。",
            schema=ToolSchema({"paths": list}, frozenset({"paths"})),
            policy=ToolPolicy(confirmation=ConfirmationMode.ALWAYS),
            handler=_delete,
        ),
        ToolDefinition(
            name="workspace_move",
            description="移动或重命名工作区路径，拒绝覆盖已有目标。",
            schema=ToolSchema({"src": str, "dst": str}, frozenset({"src", "dst"})),
            policy=ToolPolicy(confirmation=ConfirmationMode.ALWAYS),
            handler=_move,
        ),
    )


def _read(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    path = Path(arguments["path"])
    offset = arguments.get("offset", 1)
    limit = arguments.get("limit", 100)
    if offset < 1 or limit < 1:
        return ToolFailure("invalid_range", "offset and limit must be positive")
    try:
        snapshot = workspace.read(path)
        lines = workspace.read_lines(path, offset=offset - 1, limit=limit)
    except (OSError, UnicodeError, WorkspaceError, ValueError) as error:
        return ToolFailure("workspace_read_failed", str(error))
    return ToolSuccess(
        {
            "path": str(snapshot.path),
            "revision": snapshot.revision,
            "total_lines": len(snapshot.content.splitlines()),
            "offset": offset,
            "limit": limit,
            "truncated": offset - 1 + len(lines) < len(snapshot.content.splitlines()),
            "lines": tuple((line.number, line.content) for line in lines),
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


def _grep(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    max_matches = arguments.get("max_matches", 50)
    try:
        matches = workspace.search(
            arguments["pattern"], path=Path(arguments.get("path", ".")),
            glob=arguments.get("glob", "**/*"), regex=arguments.get("regex", False), max_matches=max_matches,
        )
    except (OSError, ValueError, WorkspaceError) as error:
        return ToolFailure("workspace_search_failed", str(error))
    files: dict[str, list[tuple[int, str]]] = {}
    for match in matches:
        files.setdefault(str(match.path), []).append((match.line.number, match.line.content))
    return ToolSuccess({"pattern": arguments["pattern"], "total_matches": len(matches), "files": files,
                        "truncated": len(matches) >= max_matches})


def _search_file(arguments: Mapping[str, object], context: WorkspaceToolContext) -> ToolSuccess | ToolFailure:
    workspace = _workspace(context)
    if isinstance(workspace, ToolFailure):
        return workspace
    max_results = arguments.get("max_results", 50)
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
        if workspace.exists(path):
            return ToolFailure("workspace_path_exists", f"File already exists: {path}")
        workspace.write(path, arguments["content"])
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


def _workspace(context: WorkspaceToolContext) -> WorkspacePort | ToolFailure:
    if context.workspace is None:
        return ToolFailure("workspace_unavailable", "This tool requires a configured workspace")
    return context.workspace
