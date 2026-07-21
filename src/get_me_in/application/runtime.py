"""Synchronous, typed state machine for one declarative agent."""

from dataclasses import dataclass
from enum import StrEnum

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import Cancel, RuntimeCommand, UserMessage
from src.get_me_in.application.events import (
    Cancelled,
    Completed,
    Failed,
    Progress,
    RuntimeEvent,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.model_reply import ModelReplyParseError, ModelReplyParser
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.domain.agents import AgentSpec
from src.get_me_in.domain.messages import ConversationEvent, EventKind, Role
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.llm import LLMPort, LLMRequest, ModelProfile


class RuntimePhase(StrEnum):
    """The single active phase of an R2 runtime instance."""

    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class AgentState:
    """Internal runtime state; R4 moves its ownership into SessionState."""

    phase: RuntimePhase = RuntimePhase.READY
    history: tuple[ConversationEvent, ...] = ()
    rounds: int = 0


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
        self._state = AgentState()

    def handle(self, command: RuntimeCommand) -> tuple[RuntimeEvent, ...]:
        """Apply one command and return deterministic typed events."""
        if isinstance(command, Cancel):
            self._cancellation.cancel()
            self._state = AgentState(
                phase=RuntimePhase.CANCELLED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (Cancelled(command.reason),)
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
            self._state = AgentState(
                phase=RuntimePhase.FAILED,
                history=self._state.history,
                rounds=self._state.rounds,
            )
            return (
                *events,
                ToolStarted(call_id=call_id, tool_name=reply.tool_name),
                ToolFinished(
                    call_id=call_id,
                    tool_name=reply.tool_name,
                    output="R2 has no ToolCatalog",
                ),
                Failed(
                    code="unknown_tool",
                    message=f"Tool {reply.tool_name!r} is not available in R2",
                ),
            )

        assistant_event = self._conversation_event(Role.ASSISTANT, reply.content)
        self._state = AgentState(
            phase=RuntimePhase.COMPLETED,
            history=(*self._state.history, assistant_event),
            rounds=self._state.rounds,
        )
        return (*events, Completed(assistant_event))

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

    def _conversation_event(self, role: Role, content: str) -> ConversationEvent:
        return ConversationEvent(
            event_id=self._id_generator.new_id(),
            role=role,
            kind=EventKind.MESSAGE,
            content=content,
            timestamp=self._clock.now(),
        )
