"""Rich presentation for CLI data; never chooses the next command."""

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
    ProgressKind,
    RuntimeEvent,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.app_results import (
    ApplicationResult,
    KnowledgeReloaded,
    MemoryBuildScheduled,
)
from src.get_me_in.domain.plans import Plan, PlanStatus
from src.get_me_in.domain.sessions import SessionView
from src.get_me_in.cli.localization import Translator


_SENSITIVE_ARGUMENT_NAMES = frozenset({"api_key", "authorization", "credential", "password", "secret", "token"})


class Renderer:
    """Renders typed events and frontend projections without business decisions."""

    def __init__(
        self,
        console: Console | None = None,
        *,
        translator: Translator,
        show_thinking: bool = False,
        result_preview_chars: int | None = None,
        argument_preview_chars: int | None = None,
    ) -> None:
        self._console = console or Console(force_terminal=True)
        self._translator = translator
        self._show_thinking = show_thinking
        self._result_preview_chars = result_preview_chars
        self._argument_preview_chars = argument_preview_chars

    def render_welcome(self) -> None:
        """Render the stable product identity before the first input prompt."""
        self._console.print()
        title = escape(self._translator.text("welcome.title"))
        help_hint = escape(self._translator.text("welcome.help_hint"))
        self._console.print(Panel.fit(f"[bold green]{title}[/]"))
        self._console.print(f"[dim]{help_hint}[/]")
        self._console.print()

    def render_event(self, event: RuntimeEvent) -> None:
        if isinstance(event, Progress):
            progress_keys = {
                ProgressKind.CALLING_MODEL: "progress.calling_model",
                ProgressKind.REPAIRING_MODEL_RESPONSE: "progress.repairing_model_response",
                ProgressKind.WAITING_FOR_TOOL_RESULT: "progress.waiting_for_tool_result",
            }
            key = progress_keys.get(event.kind)
            message = (
                self._translator.text(key)
                if key is not None
                else self._translator.text(
                    "progress.unknown",
                    kind=escape(str(event.kind)),
                )
            )
            self._console.print(f"[dim]🔄 {escape(message)}[/]")
        elif isinstance(event, ToolStarted):
            self._render_thinking(event.thinking)
            self._console.print(Markdown(event.message))
            tool = self._translator.text(
                "tool.started",
                tool_name=escape(event.tool_name),
            )
            self._console.print(f"[dim]{tool}{self._arguments_summary(event.arguments)}[/]")
        elif isinstance(event, ToolFinished):
            self._console.print(
                f"[dim]{self._translator.text('tool.finished', tool_name=escape(event.tool_name))}[/]"
            )
            if event.plan is not None:
                self._render_plan(event.plan)
            elif event.output:
                self._console.print(
                    Panel(
                        Text(self._preview(event.output, limit=self._result_preview_chars)),
                        title=self._translator.text(
                            "tool.result_title",
                            tool_name=escape(event.tool_name),
                        ),
                        border_style="dim",
                    )
                )
        elif isinstance(event, ApprovalRequested):
            self._console.print(
                f"[yellow]{self._translator.text('approval.required', tool_name=escape(event.tool_name))}[/]"
            )
        elif isinstance(event, SelectionRequested):
            self._console.print(
                f"[yellow]{self._translator.text('selection.required', prompt=escape(event.prompt))}[/]"
            )
        elif isinstance(event, HandoffRequested):
            self._console.print(
                f"[dim]{self._translator.text('handoff.to', target=escape(str(event.target)))}[/]"
            )
        elif isinstance(event, Completed):
            self._render_thinking(event.message.thinking)
            self._console.print(Markdown(event.message.content))
        elif isinstance(event, Failed):
            self.render_error(f"{event.code}: {event.message}")
        elif isinstance(event, Paused):
            self.render_notice(f"{event.code}: {event.message}")
            self.render_notice(self._translator.text("paused.resume_hint"))
        elif isinstance(event, Cancelled):
            self.render_notice(
                self._translator.text("cancelled.by_user", reason=event.reason)
            )

    def render_session(self, view: SessionView) -> None:
        recap = Table.grid(padding=(0, 1))
        recap.add_row(self._translator.text("session.label"), Text(view.session_id))
        recap.add_row(self._translator.text("session.agent"), Text(str(view.active_agent)))
        recap.add_row(self._translator.text("session.status"), Text(str(view.phase)))
        recap.add_row(
            self._translator.text("session.rewind_points"),
            Text(str(len(view.rewind_points))),
        )
        self._console.print(
            Panel(
                recap,
                title=self._translator.text("session.title"),
                border_style="dim",
            )
        )

    def render_help(self, entries: tuple[tuple[str, str], ...]) -> None:
        table = Table(show_header=False, box=None, padding=(0, 1))
        for command, description in entries:
            table.add_row(Text(command, style="bold"), Text(description, style="dim"))
        self._console.print(table)

    def render_application_result(self, result: ApplicationResult) -> None:
        """Render an already-computed application result without choosing follow-up work."""
        if isinstance(result, KnowledgeReloaded):
            report = result.report
            content = self._translator.text(
                "application.knowledge_reloaded",
                added=len(report.added),
                updated=len(report.updated),
                deleted=len(report.deleted),
                failures=len(report.failures),
            )
        elif isinstance(result, MemoryBuildScheduled):
            content = self._translator.text(
                "application.memory_scheduled",
                job_id=escape(result.receipt.job_id),
            )
        else:
            content = str(result)
        self._console.print(
            Panel(
                Text(content),
                title=self._translator.text("application.result_title"),
                border_style="dim",
            )
        )

    def _render_plan(self, plan: Plan) -> None:
        table = Table(
            title=self._translator.text("plan.title"),
            show_header=True,
            header_style="bold",
            box=None,
        )
        table.add_column(self._translator.text("plan.index"), justify="right", width=4)
        table.add_column(self._translator.text("plan.item"))
        table.add_column(self._translator.text("plan.status"), width=8)
        labels = {
            PlanStatus.PENDING: self._translator.text("plan.status.pending"),
            PlanStatus.IN_PROGRESS: self._translator.text("plan.status.in_progress"),
            PlanStatus.COMPLETED: self._translator.text("plan.status.completed"),
            PlanStatus.CANCELLED: self._translator.text("plan.status.cancelled"),
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
            self._console.print(
                Panel(
                    Text(thinking),
                    title=self._translator.text("thinking.title"),
                    border_style="dim",
                )
            )

    def status(self, message: str) -> AbstractContextManager[Any]:
        return self._console.status(Text(message))

    def _arguments_summary(self, arguments: Mapping[str, object]) -> str:
        if not arguments:
            return ""
        values: list[str] = []
        for name, value in arguments.items():
            rendered = "***" if name.casefold() in _SENSITIVE_ARGUMENT_NAMES else self._preview(
                value, limit=self._argument_preview_chars
            )
            values.append(f"{escape(str(name))}={escape(rendered)}")
        return f" ({', '.join(values)})"

    @staticmethod
    def _preview(value: object, *, limit: int | None = None) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
        text = " ".join(text.split())
        limit = len(text) if limit is None else limit
        return text if len(text) <= limit else f"{text[:limit - 1]}…"
