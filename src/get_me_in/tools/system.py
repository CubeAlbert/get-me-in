"""Stateless system tool definitions."""

from pathlib import Path
from typing import Mapping, Protocol

from src.get_me_in.domain.tools import (
    ToolDefinition,
    ToolFailure,
    ToolHandlerContext,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.workspace import WorkspacePort


class SystemToolContext(ToolHandlerContext, Protocol):
    """Context required by the workspace-root system tool."""

    workspace: WorkspacePort | None


def build_system_tools(clock: Clock) -> tuple[ToolDefinition, ...]:
    """Build v2 system tools without registration side effects."""
    return (
        ToolDefinition(
            name="get_current_datetime",
            description="获取当前带时区的日期与时间。",
            schema=ToolSchema(properties={}),
            policy=ToolPolicy(),
            handler=lambda arguments, context: _get_current_datetime(clock, arguments, context),
        ),
        ToolDefinition(
            name="get_working_dir",
            description="获取当前受限工作区的绝对根目录。",
            schema=ToolSchema(properties={}),
            policy=ToolPolicy(),
            handler=_get_working_dir,
        ),
    )


def _get_current_datetime(
    clock: Clock,
    arguments: Mapping[str, object],
    context: ToolHandlerContext,
) -> ToolSuccess:
    del arguments, context
    return ToolSuccess(clock.now().strftime("%Y-%m-%d %H:%M:%S %z"))


def _get_working_dir(
    arguments: Mapping[str, object],
    context: SystemToolContext,
) -> ToolSuccess | ToolFailure:
    del arguments
    if context.workspace is None:
        return ToolFailure(
            "workspace_unavailable",
            "This tool requires a configured workspace",
        )
    return ToolSuccess(str(context.workspace.resolve(Path("."))))
