"""Synchronous, typed state machine for one declarative agent."""

import json
from dataclasses import dataclass, replace
from enum import StrEnum

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import (
    Approve,
    Cancel,
    Reject,
    SubmitSelection,
    RuntimeCommand,
    ToolResult,
    UserMessage,
)
from src.get_me_in.application.events import (
    ApprovalRequested,
    Handoff,
    SelectionRequested,
    Cancelled,
    Completed,
    Failed,
    Progress,
    RuntimeEvent,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.application.model_reply import ModelReplyParseError, ModelReplyParser
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.domain.agents import AgentSpec
from src.get_me_in.domain.messages import ConversationEvent, EventKind, Role
from src.get_me_in.domain.tools import ToolFailure, ToolHandoff, ToolInteraction, ToolOutcome, ToolSuccess
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.llm import LLMPort, LLMRequest, ModelProfile


class RuntimePhase(StrEnum):
    """The single active phase of an R2 runtime instance."""

    READY = "ready"
    WAITING_FOR_TOOL = "waiting_for_tool"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentState:
    """Internal runtime state; R4 moves its ownership into SessionState."""

    phase: RuntimePhase = RuntimePhase.READY
    history: tuple[ConversationEvent, ...] = ()
    rounds: int = 0
    pending_call_id: str | None = None
    pending_tool_name: str | None = None
    pending_tool_arguments: str | None = None
    pending_interaction: str | None = None


class AgentRuntime:
    """Run one agent without CLI coupling, tools, or magic control values."""

    def __init__(
        self,
        *,
        spec: AgentSpec,
        prompt_renderer: PromptRenderer,
        llm: LLMPort,
        clock: Clock,
        id_generator: IdGenerator,
        cancellation: CancellationToken,
        max_rounds: int = 2,
        tool_executor: ToolExecutor | None = None,
        tool_context: ToolContext | None = None,
    ) -> None:
        if max_rounds < 1:
            raise ValueError("max_rounds must be at least one")
        self._spec = spec
        self._prompt_renderer = prompt_renderer
        self._llm = llm
        self._clock = clock
        self._id_generator = id_generator
        self._cancellation = cancellation
        self._max_rounds = max_rounds
        self._tool_executor = tool_executor
        self._tool_context = tool_context
        self._state = AgentState()

    def handle(self, command: RuntimeCommand) -> tuple[RuntimeEvent, ...]:
        """Apply one command and return deterministic typed events."""
        if isinstance(command, Cancel):
            self._cancellation.cancel()
            self._state = AgentState(
                phase=RuntimePhase.CANCELLED,
                history=self._state.history,
                rounds=self._state.rounds,
                pending_call_id=self._state.pending_call_id,
                pending_tool_name=self._state.pending_tool_name,
            )
            return (Cancelled(command.reason),)
        if isinstance(command, ToolResult):
            return self._resume_after_tool(command)
        if isinstance(command, Approve):
            return self._approve_tool(command)
        if isinstance(command, Reject):
            return self._reject_tool(command)
        if isinstance(command, SubmitSelection):
            return self._submit_selection(command)
        if not isinstance(command, UserMessage):
            return (
                Failed(
                    code="unsupported_command",
                    message=f"R2 runtime cannot handle {type(command).__name__}",
                ),
            )
        if not command.text.strip():
            return (Failed(code="invalid_input", message="User message must not be blank"),)

        self._cancellation.reset()
        user_event = self._conversation_event(Role.USER, command.text)
        self._state = AgentState(
            phase=RuntimePhase.READY,
            history=(*self._state.history, user_event),
            rounds=0,
        )
        return self._complete_once()

    def close(self) -> None:
        """Cancel active work and release the request-scoped model adapter."""
        self._cancellation.cancel()
        self._llm.close()

    def _complete_once(self) -> tuple[RuntimeEvent, ...]:
        events: list[RuntimeEvent] = [Progress("Calling model")]
        raw_reply = self._request_reply()
        if isinstance(raw_reply, tuple):
            return (*events, *raw_reply)

        try:
            reply = ModelReplyParser().parse(raw_reply)
        except ModelReplyParseError:
            events.append(Progress("Repairing model response format"))
            repair_event = self._conversation_event(
                Role.SYSTEM,
                "Return exactly one JSON object with a string content field.",
            )
            raw_reply = self._request_reply(extra=(repair_event,))
            if isinstance(raw_reply, tuple):
                return (*events, *raw_reply)
            try:
                reply = ModelReplyParser().parse(raw_reply)
            except ModelReplyParseError:
                self._state = AgentState(
                    phase=RuntimePhase.FAILED,
                    history=self._state.history,
                    rounds=self._state.rounds,
                )
                return (
                    *events,
                    Failed(
                        code="invalid_model_reply",
                        message="Model response remained invalid after one repair attempt",
                    ),
                )

        if reply.tool_name is not None:
            call_id = self._id_generator.new_id()
            tool_call_event = self._conversation_event(
                Role.ASSISTANT,
                json.dumps(
                    {"name": reply.tool_name, "arguments": reply.tool_arguments or {}},
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                kind=EventKind.TOOL_CALL,
            )
            self._state = AgentState(
                phase=RuntimePhase.READY,
                history=(*self._state.history, tool_call_event),
                rounds=self._state.rounds,
            )
            if self._tool_executor is None or self._tool_context is None:
                return (
                    *events,
                    ToolStarted(call_id=call_id, tool_name=reply.tool_name),
                    ToolFinished(
                        call_id=call_id,
                        tool_name=reply.tool_name,
                        output="Tool execution is not configured",
                    ),
                    Failed(
                        code="tool_runtime_unconfigured",
                        message="AgentRuntime requires a ToolExecutor and ToolContext",
                    ),
                )
            outcome = self._tool_executor.execute(
                call_id,
                reply.tool_name,
                reply.tool_arguments or {},
                self._tool_context,
                self._spec.capabilities,
            )
            return (
                *events,
                ToolStarted(call_id=call_id, tool_name=reply.tool_name),
                *self._handle_tool_outcome(call_id, reply.tool_name, reply.tool_arguments or {}, outcome),
            )

        assistant_event = self._conversation_event(Role.ASSISTANT, reply.content)
        self._state = AgentState(
            phase=RuntimePhase.COMPLETED,
            history=(*self._state.history, assistant_event),
            rounds=self._state.rounds,
        )
        return (*events, Completed(assistant_event))

    def _resume_after_tool(self, command: ToolResult) -> tuple[RuntimeEvent, ...]:
        if self._state.phase is not RuntimePhase.WAITING_FOR_TOOL:
            return (
                Failed(
                    code="unexpected_tool_result",
                    message="Runtime is not waiting for a tool result",
                ),
            )
        if command.call_id != self._state.pending_call_id:
            return (
                Failed(
                    code="tool_call_mismatch",
                    message="Tool result does not match the pending call",
                ),
            )
        tool_name = self._state.pending_tool_name
        assert tool_name is not None
        tool_event = self._conversation_event(
            Role.TOOL,
            command.output,
            kind=EventKind.TOOL_RESULT,
        )
        self._state = AgentState(
            phase=RuntimePhase.READY,
            history=(*self._state.history, tool_event),
            rounds=self._state.rounds,
        )
        return (
            ToolFinished(
                call_id=command.call_id,
                tool_name=tool_name,
                output=command.output,
            ),
            *self._complete_once(),
        )

    def _approve_tool(self, command: Approve) -> tuple[RuntimeEvent, ...]:
        if command.call_id != self._state.pending_call_id:
            return (Failed(code="tool_call_mismatch", message="Approval does not match the pending call"),)
        return self._resume_pending_tool(approved=True)

    def _reject_tool(self, command: Reject) -> tuple[RuntimeEvent, ...]:
        if command.call_id != self._state.pending_call_id:
            return (Failed(code="tool_call_mismatch", message="Rejection does not match the pending call"),)
        return self._resume_pending_tool(rejected=True)

    def _resume_pending_tool(
        self,
        *,
        approved: bool = False,
        rejected: bool = False,
    ) -> tuple[RuntimeEvent, ...]:
        if self._state.phase is not RuntimePhase.WAITING_FOR_TOOL:
            return (Failed(code="unexpected_tool_decision", message="Runtime is not waiting for tool approval"),)
        if self._tool_executor is None or self._tool_context is None:
            return (Failed(code="tool_runtime_unconfigured", message="Tool execution is not configured"),)
        call_id = self._state.pending_call_id
        tool_name = self._state.pending_tool_name
        arguments = self._state.pending_tool_arguments
        assert call_id is not None and tool_name is not None and arguments is not None
        outcome = self._tool_executor.execute(
            call_id,
            tool_name,
            json.loads(arguments),
            replace(self._tool_context, approved=approved, rejected=rejected),
            self._spec.capabilities,
        )
        return self._handle_tool_outcome(call_id, tool_name, json.loads(arguments), outcome)

    def _submit_selection(self, command: SubmitSelection) -> tuple[RuntimeEvent, ...]:
        if self._state.phase is not RuntimePhase.WAITING_FOR_TOOL or self._state.pending_interaction != "selection":
            return (Failed(code="unexpected_selection", message="Runtime is not waiting for a selection"),)
        if command.request_id != self._state.pending_call_id:
            return (Failed(code="selection_mismatch", message="Selection does not match the pending request"),)
        assert self._state.pending_tool_name is not None
        return self._finish_tool(command.request_id, self._state.pending_tool_name, {"selected": command.value})

    def _handle_tool_outcome(
        self,
        call_id: str,
        tool_name: str,
        arguments: dict[str, object],
        outcome: ToolOutcome,
    ) -> tuple[RuntimeEvent, ...]:
        if isinstance(outcome, ToolInteraction):
            if outcome.kind == "selection":
                self._state = AgentState(
                    phase=RuntimePhase.WAITING_FOR_TOOL,
                    history=self._state.history,
                    rounds=self._state.rounds,
                    pending_call_id=call_id,
                    pending_tool_name=tool_name,
                    pending_interaction="selection",
                )
                return (SelectionRequested(call_id, outcome.prompt, outcome.choices),)
            if outcome.kind != "approval":
                return (Failed(code="unsupported_interaction", message=f"Unsupported tool interaction: {outcome.kind}"),)
            self._state = AgentState(
                phase=RuntimePhase.WAITING_FOR_TOOL,
                history=self._state.history,
                rounds=self._state.rounds,
                pending_call_id=call_id,
                pending_tool_name=tool_name,
                pending_tool_arguments=json.dumps(arguments, ensure_ascii=False, sort_keys=True),
                pending_interaction="approval",
            )
            return (ApprovalRequested(call_id, outcome.prompt),)
        if isinstance(outcome, ToolHandoff):
            self._state = AgentState(phase=RuntimePhase.COMPLETED, history=self._state.history, rounds=self._state.rounds)
            return (Handoff(self._spec.key, outcome.target, outcome.context),)
        if isinstance(outcome, ToolSuccess):
            return self._finish_tool(call_id, tool_name, outcome.output)
        assert isinstance(outcome, ToolFailure)
        return self._finish_tool(
            call_id,
            tool_name,
            {"code": outcome.code, "message": outcome.message, "suggestion": outcome.suggestion},
        )

    def _finish_tool(
        self,
        call_id: str,
        tool_name: str,
        output: object,
    ) -> tuple[RuntimeEvent, ...]:
        rendered = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False, sort_keys=True)
        tool_event = self._conversation_event(Role.TOOL, rendered, kind=EventKind.TOOL_RESULT)
        self._state = AgentState(
            phase=RuntimePhase.READY,
            history=(*self._state.history, tool_event),
            rounds=self._state.rounds,
        )
        return (ToolFinished(call_id, tool_name, rendered), *self._complete_once())

    def _request_reply(
        self,
        *,
        extra: tuple[ConversationEvent, ...] = (),
    ) -> str | tuple[RuntimeEvent, ...]:
        if self._cancellation.is_cancelled:
            self._state = AgentState(
                phase=RuntimePhase.CANCELLED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (Cancelled("Cancelled before model completion"),)
        if self._state.rounds >= self._max_rounds:
            self._state = AgentState(
                phase=RuntimePhase.FAILED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (
                Failed(
                    code="max_rounds_exceeded",
                    message=f"Runtime exceeded {self._max_rounds} model rounds",
                ),
            )

        system_prompt = self._prompt_renderer.render(self._spec)
        messages = (
            self._conversation_event(Role.SYSTEM, system_prompt),
            *self._state.history,
            *extra,
        )
        self._state = AgentState(
            phase=RuntimePhase.READY,
            history=self._state.history,
            rounds=self._state.rounds + 1,
        )
        try:
            result = self._llm.complete(
                LLMRequest(
                    messages=messages,
                    profile=ModelProfile(self._spec.model_profile),
                    timeout_seconds=60,
                ),
                self._cancellation,
            )
        except TimeoutError:
            self._state = AgentState(
                phase=RuntimePhase.FAILED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (Failed(code="timeout", message="Model completion timed out"),)
        except Exception as error:
            self._state = AgentState(
                phase=RuntimePhase.FAILED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (Failed(code="provider_failure", message=str(error)),)
        if self._cancellation.is_cancelled:
            self._state = AgentState(
                phase=RuntimePhase.CANCELLED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (Cancelled("Cancelled during model completion"),)
        return result.content

    def _conversation_event(
        self,
        role: Role,
        content: str,
        *,
        kind: EventKind = EventKind.MESSAGE,
    ) -> ConversationEvent:
        return ConversationEvent(
            event_id=self._id_generator.new_id(),
            role=role,
            kind=kind,
            content=content,
            timestamp=self._clock.now(),
        )
