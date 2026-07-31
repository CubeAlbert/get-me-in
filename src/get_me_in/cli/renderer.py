"""Rich presentation for v2 CLI data; never chooses the next command."""

import json
from contextlib import AbstractContextManager
from typing import Any, Mapping

from rich.console import Console
from rich.markup import escape
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.get_me_in.application.events import (
    ApprovalRequested,
    Cancelled,
    Completed,
    Failed,
    HandoffRequested,
    Paused,
    Progress,
    RuntimeEvent,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.app_results import ApplicationResult
from src.get_me_in.domain.plans import Plan, PlanStatus
from src.get_me_in.domain.sessions import SessionView


_SENSITIVE_ARGUMENT_NAMES = frozenset({"api_key", "authorization", "credential", "password", "secret", "token"})
_PREVIEW_LIMIT = 500


class Renderer:
    """Renders typed events and frontend projections without business decisions."""

    def __init__(self, console: Console | None = None, *, show_thinking: bool = False) -> None:
        self._console = console or Console(force_terminal=True)
        self._show_thinking = show_thinking

    def render_welcome(self) -> None:
        """Render the stable product identity before the first input prompt."""
        self._console.print()
        self._console.print(Panel.fit("[bold green]get-me-in[/] — AI 求职助手"))
        self._console.print("[dim]输入 /help 查看所有命令[/]")
        self._console.print()

    def render_event(self, event: RuntimeEvent) -> None:
        if isinstance(event, Progress):
            self._console.print(f"[dim]🔄 {escape(event.message)}[/]")
        elif isinstance(event, ToolStarted):
            self._console.print(f"[dim]正在执行工具：{escape(event.tool_name)}{self._arguments_summary(event.arguments)}[/]")
            self._render_thinking(event.thinking)
        elif isinstance(event, ToolFinished):
            self._console.print(f"[dim]工具完成：{escape(event.tool_name)}[/]")
            if event.plan is not None:
                self._render_plan(event.plan)
            elif event.output:
                self._console.print(
                    Panel(
                        Text(self._preview(event.output)),
                        title=f"工具结果 · {escape(event.tool_name)}",
                        border_style="dim",
                    )
                )
        elif isinstance(event, ApprovalRequested):
            self._console.print(f"[yellow]需要审批：{escape(event.summary)}[/]")
        elif isinstance(event, SelectionRequested):
            self._console.print(f"[yellow]需要选择：{escape(event.prompt)}[/]")
        elif isinstance(event, HandoffRequested):
            self._console.print(f"[dim]正在转交给 {escape(str(event.target))}[/]")
        elif isinstance(event, Completed):
            self._render_thinking(event.message.thinking)
            self._console.print(Markdown(event.message.content))
        elif isinstance(event, Failed):
            self.render_error(f"{event.code}: {event.message}")
        elif isinstance(event, Paused):
            self.render_notice(f"{event.code}: {event.message}")
            self.render_notice("当前 Agent 已暂停；请直接输入下一条消息继续当前会话。")
        elif isinstance(event, Cancelled):
            self.render_notice(f"已取消：{event.reason}")

    def render_session(self, view: SessionView) -> None:
        recap = Table.grid(padding=(0, 1))
        recap.add_row("会话", Text(view.session_id))
        recap.add_row("当前 Agent", Text(str(view.active_agent)))
        recap.add_row("状态", Text(str(view.phase)))
        recap.add_row("可回退回合", Text(str(len(view.rewind_points))))
        self._console.print(Panel(recap, title="会话摘要", border_style="dim"))

    def render_help(self, entries: tuple[tuple[str, str], ...]) -> None:
        table = Table(show_header=False, box=None, padding=(0, 1))
        for command, description in entries:
            table.add_row(Text(command, style="bold"), Text(description, style="dim"))
        self._console.print(table)

    def render_application_result(self, result: ApplicationResult) -> None:
        """Render an already-computed application result without choosing follow-up work."""
        self._console.print(Panel(Text(str(result)), title="应用命令结果", border_style="dim"))

    def _render_plan(self, plan: Plan) -> None:
        table = Table(title="执行计划", show_header=True, header_style="bold", box=None)
        table.add_column("序号", justify="right", width=4)
        table.add_column("事项")
        table.add_column("状态", width=8)
        labels = {
            PlanStatus.PENDING: "待执行",
            PlanStatus.IN_PROGRESS: "进行中",
            PlanStatus.COMPLETED: "已完成",
            PlanStatus.CANCELLED: "已取消",
        }
        for index, item in enumerate(plan.items, start=1):
            description = Text(item.description)
            if item.status is PlanStatus.IN_PROGRESS:
                description.stylize("bold")
            table.add_row(Text(str(index)), description, Text(labels[item.status]))
        self._console.print(table)

    def render_error(self, message: str) -> None:
        self._console.print(f"[red]{escape(message)}[/]")

    def render_notice(self, message: str) -> None:
        self._console.print(f"[dim]{escape(message)}[/]")

    def _render_thinking(self, thinking: str | None) -> None:
        if self._show_thinking and thinking and thinking.strip():
            self._console.print(Panel(Text(thinking), title="思考摘要", border_style="dim"))

    def status(self, message: str) -> AbstractContextManager[Any]:
        return self._console.status(Text(message))

    @staticmethod
    def _arguments_summary(arguments: Mapping[str, object]) -> str:
        if not arguments:
            return ""
        values: list[str] = []
        for name, value in arguments.items():
            rendered = "***" if name.casefold() in _SENSITIVE_ARGUMENT_NAMES else Renderer._preview(value, limit=160)
            values.append(f"{escape(str(name))}={escape(rendered)}")
        return f" ({', '.join(values)})"

    @staticmethod
    def _preview(value: object, *, limit: int = _PREVIEW_LIMIT) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
        text = " ".join(text.split())
        return text if len(text) <= limit else f"{text[:limit - 1]}…"
