"""Rich presentation for v2 CLI data; never chooses the next command."""

from contextlib import AbstractContextManager
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from src.get_me_in.application.events import (
    ApprovalRequested,
    Cancelled,
    Completed,
    Failed,
    HandoffRequested,
    Progress,
    RuntimeEvent,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.domain.sessions import SessionView


class Renderer:
    """Renders typed events and frontend projections without business decisions."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console(force_terminal=True)

    def render_event(self, event: RuntimeEvent) -> None:
        if isinstance(event, Progress):
            self._console.print(f"[dim]🔄 {event.message}[/]")
        elif isinstance(event, ToolStarted):
            self._console.print(f"[dim]正在执行工具：{event.tool_name}[/]")
        elif isinstance(event, ToolFinished):
            self._console.print(f"[dim]工具完成：{event.tool_name}[/]")
        elif isinstance(event, ApprovalRequested):
            self._console.print(f"[yellow]需要审批：{event.summary}[/]")
        elif isinstance(event, SelectionRequested):
            self._console.print(f"[yellow]需要选择：{event.prompt}[/]")
        elif isinstance(event, HandoffRequested):
            self._console.print(f"[dim]正在转交给 {event.target}[/]")
        elif isinstance(event, Completed):
            self._console.print(Markdown(event.message.content))
        elif isinstance(event, Failed):
            self.render_error(f"{event.code}: {event.message}")
        elif isinstance(event, Cancelled):
            self.render_notice(f"已取消：{event.reason}")

    def render_session(self, view: SessionView) -> None:
        recap = Table.grid(padding=(0, 1))
        recap.add_row("会话", view.session_id)
        recap.add_row("当前 Agent", str(view.active_agent))
        recap.add_row("状态", str(view.phase))
        recap.add_row("可回退回合", str(len(view.rewind_points)))
        self._console.print(Panel(recap, title="会话概览", border_style="dim"))

    def render_help(self, entries: tuple[tuple[str, str], ...]) -> None:
        table = Table(show_header=False, box=None, padding=(0, 1))
        for command, description in entries:
            table.add_row(f"[bold]{command}[/]", f"[dim]{description}[/]")
        self._console.print(table)

    def render_error(self, message: str) -> None:
        self._console.print(f"[red]{message}[/]")

    def render_notice(self, message: str) -> None:
        self._console.print(f"[dim]{message}[/]")

    def status(self, message: str) -> AbstractContextManager[Any]:
        return self._console.status(message)
