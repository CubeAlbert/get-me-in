"""Hub-and-Spoke session transitions with call-id-safe handoff closure."""

from collections.abc import Mapping
from dataclasses import dataclass, replace

from src.get_me_in.application.commands import CompleteHandoff, FailHandoff, RuntimeCommand, UserMessage
from src.get_me_in.application.events import Cancelled, Failed, HandoffRequested, RuntimeEvent, ToolFinished
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.domain.agents import AgentKey
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


class Orchestrator:
    """The sole component permitted to switch an active agent."""

    def __init__(self, runtimes: Mapping[AgentKey, AgentRuntime]) -> None:
        self._runtimes = dict(runtimes)

    def handle(self, session: SessionState, command: RuntimeCommand) -> SessionTransition:
        source = session.active_agent
        runtime = self._runtimes[source]
        transition = runtime.advance(session.agents[source], command, session_id=session.session_id)
        session = self._replace_agent(session, source, transition.state)
        event = transition.event
        if not isinstance(event, HandoffRequested):
            if isinstance(event, Failed) and session.handoff_stack:
                return self._close_active_handoff(session, event)
            return SessionTransition(session, event)
        return self._handoff(session, event)

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

    def _handoff(self, session: SessionState, event: HandoffRequested) -> SessionTransition:
        if event.target not in self._runtimes or event.target not in session.agents:
            return self._close_failure(session, event, "unknown_agent", f"Unknown agent: {event.target.value}")
        if event.target is not AgentKey.MAIN:
            return self._start_subagent(session, event)
        return self._return_to_main(session, event)

    def _start_subagent(self, session: SessionState, event: HandoffRequested) -> SessionTransition:
        if session.active_agent is not AgentKey.MAIN or session.handoff_stack:
            return self._close_failure(session, event, "nested_handoff", "Only main may start one sub-agent handoff")
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
        )

    def _close_active_handoff(self, session: SessionState, event: Cancelled | Failed) -> SessionTransition:
        frame = session.handoff_stack[-1]
        if session.active_agent is not frame.target:
            return SessionTransition(session, event)
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
            return SessionTransition(session, transition.event)
        session = self._clear_closed_subagent(session, frame)
        return SessionTransition(
            replace(session, active_agent=frame.source, handoff_stack=session.handoff_stack[:-1]),
            transition.event,
            closed_agent=frame.target,
        )

    def _return_to_main(self, session: SessionState, event: HandoffRequested) -> SessionTransition:
        if not session.handoff_stack:
            return self._close_failure(session, event, "unexpected_return", "No handoff is active")
        frame = session.handoff_stack[-1]
        if event.source is not frame.target or event.target is not frame.source:
            return self._close_failure(session, event, "invalid_return", "Handoff return does not match active frame")
        source_runtime = self._runtimes[frame.source]
        source_transition = source_runtime.advance(
            session.agents[frame.source], CompleteHandoff(frame.call_id, event.context), session_id=session.session_id
        )
        session = self._replace_agent(session, frame.source, source_transition.state)
        if not isinstance(source_transition.event, ToolFinished):
            return SessionTransition(session, source_transition.event)
        session = self._clear_closed_subagent(session, frame)
        return SessionTransition(
            replace(session, active_agent=frame.source, handoff_stack=session.handoff_stack[:-1]),
            source_transition.event,
            closed_agent=frame.target,
        )

    def _close_failure(self, session: SessionState, event: HandoffRequested, code: str, message: str) -> SessionTransition:
        runtime = self._runtimes[event.source]
        transition = runtime.advance(
            session.agents[event.source],
            FailHandoff(event.call_id, code, message),
            session_id=session.session_id,
        )
        return SessionTransition(self._replace_agent(session, event.source, transition.state), transition.event)

    @staticmethod
    def _replace_agent(session: SessionState, key: AgentKey, state: AgentSessionState) -> SessionState:
        agents = dict(session.agents)
        agents[key] = state
        return replace(session, agents=agents)

    @staticmethod
    def _clear_closed_subagent(session: SessionState, frame: HandoffFrame) -> SessionState:
        return Orchestrator._replace_agent(session, frame.target, AgentSessionState())
