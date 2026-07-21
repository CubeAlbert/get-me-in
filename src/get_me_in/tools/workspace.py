"""Workspace tool definitions backed solely by WorkspacePort."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.tools import (
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


def _workspace(context: WorkspaceToolContext) -> WorkspacePort | ToolFailure:
    if context.workspace is None:
        return ToolFailure("workspace_unavailable", "This tool requires a configured workspace")
    return context.workspace
