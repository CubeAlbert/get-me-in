"""Hub-and-Spoke session transitions with call-id-safe handoff closure."""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from src.get_me_in.application.commands import CompleteHandoff, Continue, FailHandoff, RuntimeCommand, UserMessage
from src.get_me_in.application.events import Cancelled, Failed, HandoffRequested, RuntimeEvent, ToolFinished
from src.get_me_in.application.llm_usage import ContextEstimate
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.llm_usage import LLMAttemptPurpose, LLMAttemptRecord, LLMAttemptScope
from src.get_me_in.domain.sessions import AgentSessionState, HandoffFrame, SessionState


_EXIT_SUBAGENT_SUMMARY_PROMPT = (
    "用户请求主动退出当前子 Agent。请整理本次会话做了什么、结论、关键发现和需要主 Agent 继续跟进的事项，"
    "然后调用 switch_to_mainagent，并将这份总结作为 summary 返回。"
)


@dataclass(frozen=True)
class SessionTransition:
    session: SessionState
    event: RuntimeEvent
    started_agent: AgentKey | None = None
    closed_agent: AgentKey | None = None
    attempt: LLMAttemptRecord | None = None


class Orchestrator:
    """The sole component permitted to switch an active agent."""

    def __init__(self, runtimes: Mapping[AgentKey, AgentRuntime]) -> None:
        self._runtimes = dict(runtimes)

    def handle(self, session: SessionState, command: RuntimeCommand) -> SessionTransition:
        source = session.active_agent
        runtime = self._runtimes[source]
        transition = runtime.advance(
            session.agents[source],
            command,
            session_id=session.session_id,
            attempt_scope=self._attempt_scope(session, command),
        )
        session = self._replace_agent(session, source, transition.state)
        event = transition.event
        if not isinstance(event, HandoffRequested):
            if isinstance(event, Failed) and session.handoff_stack:
                return self._close_active_handoff(session, event, transition.attempt)
            return SessionTransition(session, event, attempt=transition.attempt)
        return self._handoff(session, event, transition.attempt)

    def context_estimate(self, session: SessionState) -> ContextEstimate:
        runtime = self._runtimes[session.active_agent]
        return runtime.context_estimate(session.agents[session.active_agent])

    def exit_subagent(self, session: SessionState, summarize: bool = True) -> SessionTransition:
        """Return from the active sub-agent, optionally asking it to summarize first."""
        if not session.handoff_stack or session.active_agent is AgentKey.MAIN:
            raise ValueError("No sub-agent handoff is active")
        if summarize:
            return self.handle(session, UserMessage(_EXIT_SUBAGENT_SUMMARY_PROMPT))
        frame = session.handoff_stack[-1]
        runtime = self._runtimes[frame.source]
        transition = runtime.advance(
            session.agents[frame.source],
            FailHandoff(frame.call_id, "subagent_exited", "用户主动退出"),
            session_id=session.session_id,
        )
        session = self._replace_agent(session, frame.source, transition.state)
        if not isinstance(transition.event, ToolFinished):
            return SessionTransition(session, transition.event)
        session = self._clear_closed_subagent(session, frame)
        return SessionTransition(
            replace(session, active_agent=frame.source, handoff_stack=session.handoff_stack[:-1]),
            transition.event,
            closed_agent=frame.target,
        )

    def request_cancel(self, session: SessionState, reason: str = "Cancelled by user") -> None:
        self._runtimes[session.active_agent].request_cancel(reason)

    def close(self) -> None:
        for runtime in self._runtimes.values():
            runtime.close()

    def _handoff(
        self,
        session: SessionState,
        event: HandoffRequested,
        attempt: LLMAttemptRecord | None,
    ) -> SessionTransition:
        if event.target not in self._runtimes or event.target not in session.agents:
            return self._close_failure(session, event, "unknown_agent", f"Unknown agent: {event.target.value}", attempt)
        if event.target is not AgentKey.MAIN:
            return self._start_subagent(session, event, attempt)
        return self._return_to_main(session, event, attempt)

    def _start_subagent(
        self,
        session: SessionState,
        event: HandoffRequested,
        attempt: LLMAttemptRecord | None,
    ) -> SessionTransition:
        if session.active_agent is not AgentKey.MAIN or session.handoff_stack:
            return self._close_failure(session, event, "nested_handoff", "Only main may start one sub-agent handoff", attempt)
        source_state = session.agents[event.source]
        frame = HandoffFrame(event.source, event.target, event.call_id, source_state.turn_id, event.context)
        target_runtime = self._runtimes[event.target]
        target_transition = target_runtime.advance(
            AgentSessionState(),
            UserMessage(event.context or "Continue the delegated task."),
            session_id=session.session_id,
        )
        if isinstance(target_transition.event, Failed):
            return self._close_failure(
                session,
                event,
                "handoff_start_failed",
                target_transition.event.message,
            )
        session = self._replace_agent(session, event.target, target_transition.state)
        return SessionTransition(
            replace(session, active_agent=event.target, handoff_stack=(*session.handoff_stack, frame)),
            event,
            started_agent=event.target,
            attempt=attempt,
        )

    def _close_active_handoff(
        self,
        session: SessionState,
        event: Cancelled | Failed,
        attempt: LLMAttemptRecord | None,
    ) -> SessionTransition:
        frame = session.handoff_stack[-1]
        if session.active_agent is not frame.target:
            return SessionTransition(session, event, attempt=attempt)
        code = "subagent_cancelled" if isinstance(event, Cancelled) else "subagent_failed"
        message = event.reason if isinstance(event, Cancelled) else event.message
        runtime = self._runtimes[frame.source]
        transition = runtime.advance(
            session.agents[frame.source],
            FailHandoff(frame.call_id, code, message, terminal=isinstance(event, Failed)),
            session_id=session.session_id,
        )
        session = self._replace_agent(session, frame.source, transition.state)
        if not isinstance(transition.event, Failed):
            return SessionTransition(session, transition.event, attempt=attempt)
        session = self._clear_closed_subagent(session, frame)
        return SessionTransition(
            replace(session, active_agent=frame.source, handoff_stack=session.handoff_stack[:-1]),
            transition.event,
            closed_agent=frame.target,
            attempt=attempt,
        )

    def _return_to_main(
        self,
        session: SessionState,
        event: HandoffRequested,
        attempt: LLMAttemptRecord | None,
    ) -> SessionTransition:
        if not session.handoff_stack:
            return self._close_failure(session, event, "unexpected_return", "No handoff is active", attempt)
        frame = session.handoff_stack[-1]
        if event.source is not frame.target or event.target is not frame.source:
            return self._close_failure(session, event, "invalid_return", "Handoff return does not match active frame", attempt)
        source_runtime = self._runtimes[frame.source]
        source_transition = source_runtime.advance(
            session.agents[frame.source], CompleteHandoff(frame.call_id, event.context), session_id=session.session_id
        )
        session = self._replace_agent(session, frame.source, source_transition.state)
        if not isinstance(source_transition.event, ToolFinished):
            return SessionTransition(session, source_transition.event, attempt=attempt)
        session = self._clear_closed_subagent(session, frame)
        return SessionTransition(
            replace(session, active_agent=frame.source, handoff_stack=session.handoff_stack[:-1]),
            source_transition.event,
            closed_agent=frame.target,
            attempt=attempt,
        )

    def _close_failure(
        self,
        session: SessionState,
        event: HandoffRequested,
        code: str,
        message: str,
        attempt: LLMAttemptRecord | None,
    ) -> SessionTransition:
        runtime = self._runtimes[event.source]
        transition = runtime.advance(
            session.agents[event.source],
            FailHandoff(event.call_id, code, message),
            session_id=session.session_id,
        )
        return SessionTransition(
            self._replace_agent(session, event.source, transition.state),
            transition.event,
            attempt=attempt,
        )

    @staticmethod
    def _attempt_scope(session: SessionState, command: RuntimeCommand) -> LLMAttemptScope | None:
        if not isinstance(command, Continue):
            return None
        frame = session.handoff_stack[-1] if session.handoff_stack else None
        return LLMAttemptScope(
            agent=session.active_agent,
            turn_id=session.agents[session.active_agent].turn_id,
            purpose=LLMAttemptPurpose.RUNTIME_DECISION,
            handoff_episode_id=frame.call_id if frame is not None else None,
        )

    @staticmethod
    def _replace_agent(session: SessionState, key: AgentKey, state: AgentSessionState) -> SessionState:
        agents = dict(session.agents)
        agents[key] = state
        return replace(session, agents=agents)

    @staticmethod
    def _clear_closed_subagent(session: SessionState, frame: HandoffFrame) -> SessionState:
        return Orchestrator._replace_agent(session, frame.target, AgentSessionState())
