"""Stateless system tool definitions."""

from pathlib import Path
from typing import Mapping, Protocol

from src.get_me_in.domain.tools import (
    ToolDefinition,
    ToolFailure,
    ToolHandlerContext,
    ToolPolicy,
    ToolParameter,
    ToolSchema,
    ToolSuccess,
)
from src.get_me_in.domain.agents import Capability
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
            purpose="获取当前的日期和时间（含时区），相信该工具的输出是准确的。",
            use_when="需要知道当前时间时",
            do_not_use_when="",
            expected_output="YYYY-MM-DD HH:mm:ss ±HHMM 格式的带时区日期时间字符串",
            schema=ToolSchema(properties={}),
            policy=ToolPolicy(frozenset({Capability.SYSTEM})),
            handler=lambda arguments, context: _get_current_datetime(clock, arguments, context),
        ),
        ToolDefinition(
            name="get_working_dir",
            purpose="获取当前受限工作区的绝对根目录，该目录用于存放临时文件和输出文件。",
            use_when="需要在磁盘上读写文件时，文件路径都应以此目录为根目录。",
            do_not_use_when="",
            expected_output="工作目录的绝对路径字符串",
            schema=ToolSchema(properties={}),
            policy=ToolPolicy(frozenset({Capability.SYSTEM})),
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
