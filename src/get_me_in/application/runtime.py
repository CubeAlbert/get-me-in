"""Synchronous, pull-driven state machine for one declarative agent."""

import json
import logging
from dataclasses import dataclass, replace

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import (
    Approve,
    Cancel,
    CancelSelection,
    CompleteHandoff,
    Continue,
    FailHandoff,
    Reject,
    RuntimeCommand,
    SubmitSelection,
    ToolResult,
    UserMessage,
)
from src.get_me_in.application.conversation_codec import ConversationCodec
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
from src.get_me_in.application.model_reply import ModelReplyParseError, ModelReplyParser
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentSpec
from src.get_me_in.domain.messages import (
    ConversationRecord,
    MessageRecord,
    Role,
    ToolCallRecord,
    ToolResultRecord,
)
from src.get_me_in.domain.plans import Plan
from src.get_me_in.domain.sessions import AgentSessionState, PendingToolCall, RuntimePhase
from src.get_me_in.domain.tools import (
    ToolFailure,
    ToolHandoff,
    ToolInteraction,
    ToolOutcome,
    ToolSuccess,
)
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.llm import LLMPort, LLMRequest, ModelProfile


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeTransition:
    state: AgentSessionState
    event: RuntimeEvent


class AgentRuntime:
    """Advance exactly one externally observable state transition per command."""

    def __init__(
        self,
        *,
        spec: AgentSpec,
        prompt_renderer: PromptRenderer,
        llm: LLMPort,
        clock: Clock,
        id_generator: IdGenerator,
        cancellation: CancellationToken,
        agent_catalog: AgentCatalog,
        tool_catalog: ToolCatalog,
        conversation_codec: ConversationCodec | None = None,
        max_model_calls: int = 100,
        model_timeout_seconds: float = 60,
        tool_executor: ToolExecutor | None = None,
        tool_context: ToolContext | None = None,
    ) -> None:
        if max_model_calls < 1:
            raise ValueError("max_model_calls must be at least one")
        if model_timeout_seconds <= 0:
            raise ValueError("model_timeout_seconds must be positive")
        self._spec = spec
        self._prompt_renderer = prompt_renderer
        self._llm = llm
        self._clock = clock
        self._id_generator = id_generator
        self._cancellation = cancellation
        self._agent_catalog = agent_catalog
        self._tool_catalog = tool_catalog
        self._conversation_codec = conversation_codec or ConversationCodec()
        self._max_model_calls = max_model_calls
        self._model_timeout_seconds = model_timeout_seconds
        self._tool_executor = tool_executor
        self._tool_context = tool_context
        self._state: AgentSessionState | None = None
        self._session_id: str | None = None
        self._requested_cancel_reason = "Cancelled by user"

    def advance(
        self,
        state: AgentSessionState,
        command: RuntimeCommand,
        *,
        session_id: str,
    ) -> RuntimeTransition:
        """Advance caller-owned state once, without retaining a state copy."""
        self._state = state
        self._session_id = session_id
        try:
            event = self._handle(command)
            assert self._state is not None
            return RuntimeTransition(self._state, event)
        finally:
            self._state = None
            self._session_id = None

    def _handle(self, command: RuntimeCommand) -> RuntimeEvent:
        if isinstance(command, Cancel):
            return self._cancel(command.reason)
        if isinstance(command, UserMessage):
            return self._start(command)
        if isinstance(command, Continue):
            return self._continue()
        if isinstance(command, ToolResult):
            return self._resume_external_tool(command)
        if isinstance(command, CompleteHandoff):
            return self._complete_handoff(command)
        if isinstance(command, FailHandoff):
            return self._fail_handoff(command)
        if isinstance(command, Approve):
            return self._approve(command)
        if isinstance(command, Reject):
            return self._reject(command)
        if isinstance(command, SubmitSelection):
            return self._submit_selection(command)
        if isinstance(command, CancelSelection):
            return self._cancel_selection(command)
        return Failed("unsupported_command", f"Unsupported command: {type(command).__name__}")

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        """Thread-safe side channel used while a blocking Continue is active."""
        self._requested_cancel_reason = reason
        self._cancellation.cancel()

    def close(self) -> None:
        self._cancellation.cancel()
        self._llm.close()

    def _start(self, command: UserMessage) -> RuntimeEvent:
        if self._state.phase not in {
            RuntimePhase.READY,
            RuntimePhase.COMPLETED,
            RuntimePhase.CANCELLED,
            RuntimePhase.FAILED,
            RuntimePhase.WAITING_FOR_USER,
        }:
            return Failed("run_in_progress", "Finish or cancel the active run before sending a new message")
        if not command.text.strip():
            return Failed("invalid_input", "User message must not be blank")
        self._cancellation.reset()
        self._requested_cancel_reason = "Cancelled by user"
        turn_id = self._id_generator.new_id()
        user_record = self._message(Role.USER, command.text, turn_id)
        self._state = AgentSessionState(
            phase=RuntimePhase.MODEL_PENDING,
            history=(*self._state.history, user_record),
            turn_id=turn_id,
            plan=self._state.plan,
        )
        return Progress("Calling model")

    def _continue(self) -> RuntimeEvent:
        if self._state.phase is RuntimePhase.MODEL_PENDING:
            return self._complete_model()
        if self._state.phase is RuntimePhase.MODEL_QUEUED:
            self._state = replace(self._state, phase=RuntimePhase.MODEL_PENDING)
            return Progress("Calling model")
        if self._state.phase is RuntimePhase.TOOL_READY:
            return self._execute_pending()
        if self._state.phase is RuntimePhase.CANCELLED_NOTICE:
            self._state = replace(self._state, phase=RuntimePhase.CANCELLED)
            return Cancelled(self._state.cancel_reason)
        return Failed("continue_not_allowed", f"Continue is not allowed in phase {self._state.phase.value}")

    def _complete_model(self) -> RuntimeEvent:
        if self._cancellation.is_cancelled:
            self._state = replace(self._state, phase=RuntimePhase.CANCELLED)
            return Cancelled(self._requested_cancel_reason)
        if self._state.model_calls >= self._max_model_calls:
            self._state = replace(self._state, phase=RuntimePhase.FAILED)
            return Failed(
                "max_model_calls_exceeded",
                f"Runtime exceeded {self._max_model_calls} model calls",
            )

        tools = self._tool_catalog.list_for_capabilities(self._spec.capabilities)
        prompt = self._prompt_renderer.render(
            self._spec,
            tools=tools,
            agents=self._agent_catalog.list_descriptors(),
        )
        request = LLMRequest(
            messages=self._conversation_codec.encode(prompt, self._state.history),
            profile=ModelProfile(self._spec.model_profile),
            timeout_seconds=self._model_timeout_seconds,
            temperature=self._spec.temperature,
        )
        self._state = replace(self._state, model_calls=self._state.model_calls + 1)
        logger.debug(
            "Calling model: agent=%s turn=%s call=%d profile=%s messages=%d",
            self._spec.key.value,
            self._state.turn_id,
            self._state.model_calls,
            request.profile.value,
            len(request.messages),
        )
        try:
            result = self._llm.complete(request, self._cancellation)
        except TimeoutError:
            logger.warning(
                "Model completion timed out: agent=%s turn=%s timeout=%ss",
                self._spec.key.value,
                self._state.turn_id,
                self._model_timeout_seconds,
            )
            self._state = replace(self._state, phase=RuntimePhase.FAILED)
            return Failed("timeout", "Model completion timed out")
        except InterruptedError:
            logger.info(
                "Model completion cancelled: agent=%s turn=%s",
                self._spec.key.value,
                self._state.turn_id,
            )
            self._state = replace(self._state, phase=RuntimePhase.CANCELLED)
            return Cancelled(self._requested_cancel_reason)
        except Exception as error:
            if self._cancellation.is_cancelled:
                self._state = replace(self._state, phase=RuntimePhase.CANCELLED)
                return Cancelled(self._requested_cancel_reason)
            logger.warning(
                "Model provider failure: agent=%s turn=%s error=%s: %s",
                self._spec.key.value,
                self._state.turn_id,
                type(error).__name__,
                error,
            )
            self._state = replace(self._state, phase=RuntimePhase.FAILED)
            return Failed("provider_failure", str(error))
        if self._cancellation.is_cancelled:
            self._state = replace(self._state, phase=RuntimePhase.CANCELLED)
            return Cancelled(self._requested_cancel_reason)

        logger.debug(
            "Model raw reply: agent=%s turn=%s chars=%d\n%s",
            self._spec.key.value,
            self._state.turn_id,
            len(result.content),
            result.content,
        )
        try:
            reply = ModelReplyParser().parse(result.content)
        except ModelReplyParseError as error:
            logger.warning(
                "Invalid model reply: agent=%s turn=%s repair_attempted=%s error=%s "
                "chars=%d raw_reply=%r",
                self._spec.key.value,
                self._state.turn_id,
                self._state.repair_attempted,
                error,
                len(result.content),
                result.content,
            )
            if self._state.repair_attempted:
                self._state = replace(self._state, phase=RuntimePhase.WAITING_FOR_USER)
                return Paused(
                    "invalid_model_reply",
                    "Model response remained invalid after one repair attempt",
                )
            repair = self._message(
                Role.SYSTEM,
                (
                    f"The previous response violated the required output format: {error}\n\n"
                    "Follow this output format exactly:\n"
                    f"{self._prompt_renderer.render_output_format()}"
                ),
                self._state.turn_id,
            )
            self._state = replace(
                self._state,
                phase=RuntimePhase.MODEL_PENDING,
                history=(*self._state.history, repair),
                repair_attempted=True,
            )
            return Progress("Repairing model response format")
        if reply.repair_kind is not None:
            logger.info(
                "Model reply normalized locally: agent=%s turn=%s kind=%s",
                self._spec.key.value,
                self._state.turn_id,
                reply.repair_kind,
            )

        if reply.tool_name is not None:
            call_id = self._id_generator.new_id()
            tool_call = ToolCallRecord(
                event_id=self._id_generator.new_id(),
                call_id=call_id,
                tool_name=reply.tool_name,
                arguments=dict(reply.tool_arguments or {}),
                timestamp=self._clock.now(),
                turn_id=self._state.turn_id,
                thinking=reply.thinking,
                plan=self._state.plan,
                content=reply.content,
            )
            self._state = replace(
                self._state,
                phase=RuntimePhase.TOOL_READY,
                history=(*self._state.history, tool_call),
                pending_tool=PendingToolCall(call_id, reply.tool_name, dict(reply.tool_arguments or {})),
            )
            return ToolStarted(
                call_id,
                reply.tool_name,
                dict(reply.tool_arguments or {}),
                reply.thinking,
            )

        assistant = self._message(
            Role.ASSISTANT,
            reply.content,
            self._state.turn_id,
            thinking=reply.thinking,
        )
        self._state = replace(
            self._state,
            phase=RuntimePhase.COMPLETED,
            history=(*self._state.history, assistant),
            pending_tool=None,
        )
        return Completed(assistant)

    def _execute_pending(self, *, approved: bool = False, rejected: bool = False) -> RuntimeEvent:
        pending = self._state.pending_tool
        if pending is None:
            return Failed("pending_tool_missing", "Runtime has no pending tool call")
        if self._tool_executor is None or self._tool_context is None:
            self._state = replace(self._state, phase=RuntimePhase.WAITING_FOR_TOOL_RESULT)
            return Progress("Waiting for external tool result")
        if self._session_id is None:
            raise RuntimeError("Tool execution requires an active session scope")
        context = replace(
            self._tool_context,
            session_id=self._session_id,
            approved=approved,
            rejected=rejected,
        )
        outcome = self._tool_executor.execute(
            pending.call_id,
            pending.tool_name,
            pending.arguments,
            context,
            self._spec.capabilities,
        )
        return self._handle_tool_outcome(pending, outcome)

    def _handle_tool_outcome(self, pending: PendingToolCall, outcome: ToolOutcome) -> RuntimeEvent:
        if isinstance(outcome, ToolInteraction):
            if outcome.kind == "approval":
                self._state = replace(self._state, phase=RuntimePhase.WAITING_FOR_APPROVAL)
                return ApprovalRequested(pending.call_id, outcome.prompt)
            if outcome.kind == "selection":
                self._state = replace(self._state, phase=RuntimePhase.WAITING_FOR_SELECTION)
                return SelectionRequested(pending.call_id, outcome.prompt, outcome.choices)
            return Failed("unsupported_interaction", f"Unsupported interaction: {outcome.kind}")
        if isinstance(outcome, ToolHandoff):
            self._state = replace(self._state, phase=RuntimePhase.WAITING_FOR_HANDOFF)
            return HandoffRequested(
                pending.call_id,
                self._spec.key,
                outcome.target,
                outcome.context,
            )
        if isinstance(outcome, ToolSuccess):
            return self._finish_tool(
                pending,
                outcome.output,
                plan=self._plan_projection(pending.tool_name),
            )
        assert isinstance(outcome, ToolFailure)
        return self._finish_tool(
            pending,
            {"code": outcome.code, "message": outcome.message, "suggestion": outcome.suggestion},
        )

    def _finish_tool(
        self,
        pending: PendingToolCall,
        output: object,
        *,
        plan: Plan | None = None,
    ) -> RuntimeEvent:
        record_plan = plan if plan is not None else self._state.plan
        record = ToolResultRecord(
            event_id=self._id_generator.new_id(),
            call_id=pending.call_id,
            tool_name=pending.tool_name,
            output=output,
            timestamp=self._clock.now(),
            turn_id=self._state.turn_id,
            plan=record_plan,
        )
        rendered = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False, sort_keys=True)
        self._state = replace(
            self._state,
            phase=RuntimePhase.MODEL_QUEUED,
            history=(*self._state.history, record),
            pending_tool=None,
            plan=record_plan,
        )
        return ToolFinished(pending.call_id, pending.tool_name, rendered, plan)

    def _plan_projection(self, tool_name: str) -> Plan | None:
        if tool_name not in {"create_plan", "update_plan_status", "cancel_all_plans", "replan"}:
            return None
        if self._tool_context is None or self._tool_context.plan is None:
            return None
        return self._tool_context.plan.snapshot()

    def _approve(self, command: Approve) -> RuntimeEvent:
        failure = self._validate_pending(command.call_id, RuntimePhase.WAITING_FOR_APPROVAL)
        return failure or self._execute_pending(approved=True)

    def _reject(self, command: Reject) -> RuntimeEvent:
        failure = self._validate_pending(command.call_id, RuntimePhase.WAITING_FOR_APPROVAL)
        if failure is not None:
            return failure

        pending = self._state.pending_tool
        assert pending is not None
        reason = command.reason or f"Tool call {pending.tool_name} was rejected"
        output = {"code": "rejected", "message": reason}
        record = ToolResultRecord(
            event_id=self._id_generator.new_id(),
            call_id=pending.call_id,
            tool_name=pending.tool_name,
            output=output,
            timestamp=self._clock.now(),
            turn_id=self._state.turn_id,
            plan=self._state.plan,
        )
        self._state = replace(
            self._state,
            phase=RuntimePhase.WAITING_FOR_USER,
            history=(*self._state.history, record),
            pending_tool=None,
        )
        return Paused("approval_rejected", reason)

    def _submit_selection(self, command: SubmitSelection) -> RuntimeEvent:
        failure = self._validate_pending(command.request_id, RuntimePhase.WAITING_FOR_SELECTION)
        if failure is not None:
            return failure
        assert self._state.pending_tool is not None
        return self._finish_tool(self._state.pending_tool, {"selected": command.value})

    def _cancel_selection(self, command: CancelSelection) -> RuntimeEvent:
        failure = self._validate_pending(
            command.request_id,
            RuntimePhase.WAITING_FOR_SELECTION,
        )
        if failure is not None:
            return failure
        assert self._state.pending_tool is not None
        return self._finish_tool(
            self._state.pending_tool,
            {"code": "cancelled", "message": command.reason},
        )

    def _resume_external_tool(self, command: ToolResult) -> RuntimeEvent:
        failure = self._validate_pending(command.call_id, RuntimePhase.WAITING_FOR_TOOL_RESULT)
        if failure is not None:
            return failure
        assert self._state.pending_tool is not None
        return self._finish_tool(self._state.pending_tool, command.output)

    def _complete_handoff(self, command: CompleteHandoff) -> RuntimeEvent:
        failure = self._validate_pending(command.call_id, RuntimePhase.WAITING_FOR_HANDOFF)
        if failure is not None:
            return failure
        assert self._state.pending_tool is not None
        return self._finish_tool(self._state.pending_tool, {"summary": command.summary})

    def _fail_handoff(self, command: FailHandoff) -> RuntimeEvent:
        failure = self._validate_pending(command.call_id, RuntimePhase.WAITING_FOR_HANDOFF)
        if failure is not None:
            return failure
        assert self._state.pending_tool is not None
        result = self._finish_tool(
            self._state.pending_tool,
            {"code": command.code, "message": command.message},
        )
        if not command.terminal:
            return result
        self._state = replace(self._state, phase=RuntimePhase.FAILED)
        return Failed(command.code, command.message)

    def _validate_pending(self, call_id: str, phase: RuntimePhase) -> Failed | None:
        if self._state.phase is not phase:
            return Failed("command_not_allowed", f"Command is not allowed in phase {self._state.phase.value}")
        if self._state.pending_tool is None or self._state.pending_tool.call_id != call_id:
            return Failed("tool_call_mismatch", "Command does not match the pending tool call")
        return None

    def _cancel(self, reason: str) -> RuntimeEvent:
        self._cancellation.cancel()
        pending = self._state.pending_tool
        if pending is not None and self._state.phase in {
            RuntimePhase.TOOL_READY,
            RuntimePhase.WAITING_FOR_TOOL_RESULT,
            RuntimePhase.WAITING_FOR_APPROVAL,
            RuntimePhase.WAITING_FOR_SELECTION,
            RuntimePhase.WAITING_FOR_HANDOFF,
        }:
            output = {"code": "cancelled", "message": reason}
            record = ToolResultRecord(
                event_id=self._id_generator.new_id(),
                call_id=pending.call_id,
                tool_name=pending.tool_name,
                output=output,
                timestamp=self._clock.now(),
                turn_id=self._state.turn_id,
                plan=self._state.plan,
            )
            self._state = replace(
                self._state,
                phase=RuntimePhase.CANCELLED_NOTICE,
                history=(*self._state.history, record),
                pending_tool=None,
                cancel_reason=reason,
            )
            return ToolFinished(
                pending.call_id,
                pending.tool_name,
                json.dumps(output, ensure_ascii=False, sort_keys=True),
            )
        self._state = replace(self._state, phase=RuntimePhase.CANCELLED, cancel_reason=reason)
        return Cancelled(reason)

    def _message(
        self,
        role: Role,
        content: str,
        turn_id: str,
        *,
        thinking: str | None = None,
    ) -> MessageRecord:
        return MessageRecord(
            event_id=self._id_generator.new_id(),
            role=role,
            content=content,
            timestamp=self._clock.now(),
            turn_id=turn_id,
            thinking=thinking if role is Role.ASSISTANT else None,
            plan=self._state.plan,
        )
