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
from src.get_me_in.application.llm_usage import UsageView
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.plans import Plan, PlanStatus
from src.get_me_in.domain.sessions import RuntimePhase, SessionView
from src.get_me_in.cli.localization import LocaleCatalogError, Translator


_SENSITIVE_ARGUMENT_NAMES = frozenset({"api_key", "authorization", "credential", "password", "secret", "token"})
_AGENT_LOCALE_KEYS: Mapping[AgentKey, str] = {
    AgentKey.MAIN: "agent.main",
    AgentKey.RESUME: "agent.resume",
    AgentKey.JOB_SEARCH: "agent.job_search",
}
_PHASE_LOCALE_KEYS: Mapping[RuntimePhase, str] = {
    RuntimePhase.READY: "phase.ready",
    RuntimePhase.MODEL_PENDING: "phase.model_pending",
    RuntimePhase.MODEL_QUEUED: "phase.model_queued",
    RuntimePhase.TOOL_READY: "phase.tool_ready",
    RuntimePhase.WAITING_FOR_TOOL_RESULT: "phase.waiting_for_tool_result",
    RuntimePhase.WAITING_FOR_APPROVAL: "phase.waiting_for_approval",
    RuntimePhase.WAITING_FOR_SELECTION: "phase.waiting_for_selection",
    RuntimePhase.WAITING_FOR_HANDOFF: "phase.waiting_for_handoff",
    RuntimePhase.WAITING_FOR_USER: "phase.waiting_for_user",
    RuntimePhase.CANCELLED_NOTICE: "phase.cancelled_notice",
    RuntimePhase.COMPLETED: "phase.completed",
    RuntimePhase.CANCELLED: "phase.cancelled",
    RuntimePhase.FAILED: "phase.failed",
}


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
        title = Text(self._translator.text("welcome.title"), style="bold green")
        help_hint = Text(self._translator.text("welcome.help_hint"), style="dim")
        self._console.print(Panel.fit(title))
        self._console.print(help_hint)
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
                else self._translator.text("progress.unknown", kind=str(event.kind))
            )
            self._console.print(Text(f"🔄 {message}", style="dim"))
        elif isinstance(event, ToolStarted):
            self._render_thinking(event.thinking)
            self._console.print(Markdown(event.message))
            tool = self._translated_markup("tool.started", tool_name=event.tool_name)
            self._console.print(f"[dim]{tool}{self._arguments_summary(event.arguments)}[/]")
        elif isinstance(event, ToolFinished):
            self._console.print(
                f"[dim]{self._translated_markup('tool.finished', tool_name=event.tool_name)}[/]"
            )
            if event.plan is not None:
                self._render_plan(event.plan)
            elif event.output:
                self._console.print(
                    Panel(
                        Text(self._preview(event.output, limit=self._result_preview_chars)),
                        title=self._translated_text(
                            "tool.result_title",
                            tool_name=event.tool_name,
                        ),
                        border_style="dim",
                    )
                )
        elif isinstance(event, ApprovalRequested):
            self._console.print(
                f"[yellow]{self._translated_markup('approval.required', tool_name=event.tool_name)}[/]"
            )
        elif isinstance(event, SelectionRequested):
            self._console.print(
                f"[yellow]{self._translated_markup('selection.required', prompt=event.prompt)}[/]"
            )
        elif isinstance(event, HandoffRequested):
            target = self._enum_text(
                event.target,
                _AGENT_LOCALE_KEYS.get(event.target),
            ).plain
            self._console.print(
                f"[dim]{self._translated_markup('handoff.to', target=target)}[/]"
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
        recap.add_row(self._translated_text("session.label"), Text(view.session_id))
        recap.add_row(
            self._translated_text("session.agent"),
            self._enum_text(view.active_agent, _AGENT_LOCALE_KEYS.get(view.active_agent)),
        )
        recap.add_row(
            self._translated_text("session.status"),
            self._enum_text(view.phase, _PHASE_LOCALE_KEYS.get(view.phase)),
        )
        recap.add_row(
            self._translated_text("session.rewind_points"),
            Text(str(len(view.rewind_points))),
        )
        self._console.print(
            Panel(
                recap,
                title=self._translated_text("session.title"),
                border_style="dim",
            )
        )

    def render_usage(self, view: UsageView) -> None:
        summary = Table.grid(padding=(0, 1))
        summary.add_row(self._translated_text("usage.context"), Text(
            f"{view.context.estimated_input_tokens} / {view.context.usable_context_tokens}"
        ))
        summary.add_row(
            self._translated_text("usage.context_threshold"),
            Text(
                f"{view.context.threshold_tokens} ({view.context.threshold_ratio:.1%})"
            ),
        )
        summary.add_row(
            self._translated_text("usage.context_utilization"),
            Text(f"{view.context.utilization_ratio:.1%}"),
        )
        summary.add_row(self._translated_text("usage.context_status"), Text(view.context.status.value))
        summary.add_row(self._translated_text("usage.logical_calls"), Text(str(view.logical_calls)))
        summary.add_row(self._translated_text("usage.attempts"), Text(str(view.attempts)))
        summary.add_row(self._translated_text("usage.input_tokens"), Text(str(view.tokens.input_tokens)))
        summary.add_row(
            self._translated_text("usage.cached_input_tokens"),
            Text(str(view.tokens.cached_input_tokens)),
        )
        summary.add_row(
            self._translated_text("usage.uncached_input_tokens"),
            Text(str(view.tokens.uncached_input_tokens)),
        )
        summary.add_row(
            self._translated_text("usage.assumed_uncached_input_tokens"),
            Text(str(view.tokens.assumed_uncached_input_tokens)),
        )
        summary.add_row(self._translated_text("usage.output_tokens"), Text(str(view.tokens.output_tokens)))
        summary.add_row(
            self._translated_text("usage.reasoning_output_tokens"),
            Text(str(view.tokens.reasoning_output_tokens)),
        )
        summary.add_row(self._translated_text("usage.total_tokens"), Text(str(view.tokens.total_tokens)))
        summary.add_row(self._translated_text("usage.unknown_attempts"), Text(str(view.usage_unknown_attempts)))
        amount = format(view.costs.amount, "f")
        unit = view.costs.unit or "-"
        summary.add_row(self._translated_text("usage.estimated_cost"), Text(f"{amount} {unit}"))
        summary.add_row(self._translated_text("usage.cost_unknown_attempts"), Text(str(view.costs.unknown_attempts)))
        self._console.print(Panel(summary, title=self._translated_text("usage.title"), border_style="dim"))

        if view.groups:
            groups = Table(show_header=True, box=None, padding=(0, 1))
            groups.add_column(self._translated_text("usage.group_agent"))
            groups.add_column(self._translated_text("usage.group_purpose"))
            groups.add_column(self._translated_text("usage.group_attempts"), justify="right")
            groups.add_column(self._translated_text("usage.group_tokens"), justify="right")
            groups.add_column(self._translated_text("usage.group_cost"), justify="right")
            for group in view.groups:
                cost = f"{format(group.costs.amount, 'f')} {group.costs.unit or '-'}"
                groups.add_row(
                    self._enum_text(group.agent, _AGENT_LOCALE_KEYS.get(group.agent)),
                    Text(group.purpose.value),
                    Text(str(group.attempts)),
                    Text(str(group.tokens.total_tokens)),
                    Text(cost),
                )
            self._console.print(groups)

        if view.recent_attempts:
            recent = Table(show_header=True, box=None, padding=(0, 1))
            recent.add_column(self._translated_text("usage.recent_id"))
            recent.add_column(self._translated_text("usage.recent_agent"))
            recent.add_column(self._translated_text("usage.recent_outcome"))
            recent.add_column(self._translated_text("usage.recent_tokens"), justify="right")
            for attempt in view.recent_attempts:
                tokens = (
                    str(attempt.usage.value.total_tokens)
                    if hasattr(attempt.usage, "value")
                    else self._translator.text("usage.unknown")
                )
                recent.add_row(
                    Text(attempt.attempt_id),
                    self._enum_text(attempt.scope.agent, _AGENT_LOCALE_KEYS.get(attempt.scope.agent)),
                    Text(attempt.outcome.value),
                    Text(tokens),
                )
            self._console.print(recent)

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
                job_id=result.receipt.job_id,
            )
        else:
            content = str(result)
        self._console.print(
            Panel(
                Text(content),
                title=self._translated_text("application.result_title"),
                border_style="dim",
            )
        )

    def _render_plan(self, plan: Plan) -> None:
        table = Table(
            title=self._translated_text("plan.title"),
            show_header=True,
            header_style="bold",
            box=None,
        )
        table.add_column(self._translated_text("plan.index"), justify="right", width=4)
        table.add_column(self._translated_text("plan.item"))
        table.add_column(self._translated_text("plan.status"), width=8)
        labels = {
            PlanStatus.PENDING: self._translated_text("plan.status.pending"),
            PlanStatus.IN_PROGRESS: self._translated_text("plan.status.in_progress"),
            PlanStatus.COMPLETED: self._translated_text("plan.status.completed"),
            PlanStatus.CANCELLED: self._translated_text("plan.status.cancelled"),
        }
        for index, item in enumerate(plan.items, start=1):
            description = Text(item.description)
            if item.status is PlanStatus.IN_PROGRESS:
                description.stylize("bold")
            table.add_row(Text(str(index)), description, labels[item.status])
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
                    title=self._translated_text("thinking.title"),
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

    def _translated_markup(self, key: str, **values: object) -> str:
        """Translate plain catalog text before embedding it in Rich markup."""
        return escape(self._translator.text(key, **values))

    def _translated_text(self, key: str, **values: object) -> Text:
        """Render catalog text as Rich Text so catalog markup stays inert."""
        return Text(self._translator.text(key, **values))

    def _enum_text(self, value: AgentKey | RuntimePhase | str, locale_key: str | None) -> Text:
        """Translate a canonical enum value with an escaped-text fallback."""
        canonical = str(getattr(value, "value", value))
        if locale_key is None:
            return Text(canonical)
        try:
            return Text(self._translator.text(locale_key))
        except LocaleCatalogError:
            return Text(canonical)

    @staticmethod
    def _preview(value: object, *, limit: int | None = None) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
        text = " ".join(text.split())
        limit = len(text) if limit is None else limit
        return text if len(text) <= limit else f"{text[:limit - 1]}…"
