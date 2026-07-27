"""Hub-and-Spoke orchestration tests using a dedicated test sub-agent."""

from dataclasses import replace
from datetime import datetime, timezone
import unittest

from src.get_me_in.application.commands import Cancel, CompleteHandoff, Continue, FailHandoff, UserMessage
from src.get_me_in.application.events import Cancelled, HandoffRequested, Progress, ToolFinished
from src.get_me_in.application.orchestration import Orchestrator
from src.get_me_in.application.runtime import RuntimeTransition
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.sessions import AgentSessionState, HandoffFrame, PendingToolCall, RuntimePhase, SessionState


class OrchestratorTests(unittest.TestCase):
    def test_main_sub_main_closes_original_call_id(self) -> None:
        main, resume = _FakeRuntime(AgentKey.MAIN), _FakeRuntime(AgentKey.RESUME)
        orchestrator = Orchestrator({AgentKey.MAIN: main, AgentKey.RESUME: resume})
        session = _session()

        started = orchestrator.handle(session, UserMessage("delegate"))
        returned = orchestrator.handle(started.session, Continue())

        self.assertIsInstance(started.event, HandoffRequested)
        self.assertEqual(AgentKey.RESUME, started.session.active_agent)
        self.assertEqual(RuntimePhase.MODEL_PENDING, started.session.agents[AgentKey.RESUME].phase)
        self.assertIsInstance(returned.event, ToolFinished)
        self.assertEqual("call-main", returned.event.call_id)
        self.assertEqual(AgentKey.MAIN, returned.session.active_agent)
        self.assertEqual((), returned.session.handoff_stack)
        self.assertEqual(["session-1", "session-1"], main.session_ids)
        self.assertEqual(["session-1", "session-1"], resume.session_ids)

    def test_unknown_target_closes_source_call_with_failure(self) -> None:
        runtime = _FakeRuntime(AgentKey.MAIN, target=AgentKey.JOB_SEARCH)
        orchestrator = Orchestrator({AgentKey.MAIN: runtime})
        result = orchestrator.handle(_session(agents=(AgentKey.MAIN,)), UserMessage("delegate"))

        self.assertIsInstance(result.event, ToolFinished)
        self.assertEqual("call-main", result.event.call_id)
        self.assertEqual(RuntimePhase.MODEL_QUEUED, result.session.agents[AgentKey.MAIN].phase)

    def test_exit_subagent_closes_original_call_id(self) -> None:
        orchestrator = Orchestrator({AgentKey.MAIN: _FakeRuntime(AgentKey.MAIN), AgentKey.RESUME: _FakeRuntime(AgentKey.RESUME)})
        started = orchestrator.handle(_session(), UserMessage("delegate"))

        exited = orchestrator.exit_subagent(started.session)

        self.assertIsInstance(exited.event, ToolFinished)
        self.assertEqual("call-main", exited.event.call_id)
        self.assertEqual(AgentKey.MAIN, exited.session.active_agent)
        self.assertEqual((), exited.session.handoff_stack)

    def test_subagent_cancellation_closes_original_handoff_call(self) -> None:
        orchestrator = Orchestrator({AgentKey.MAIN: _FakeRuntime(AgentKey.MAIN), AgentKey.RESUME: _FakeRuntime(AgentKey.RESUME)})
        started = orchestrator.handle(_session(), UserMessage("delegate"))

        cancelled = orchestrator.handle(started.session, Cancel("stop delegated work"))

        self.assertIsInstance(cancelled.event, ToolFinished)
        self.assertEqual("call-main", cancelled.event.call_id)
        self.assertEqual(AgentKey.MAIN, cancelled.session.active_agent)
        self.assertEqual((), cancelled.session.handoff_stack)
        self.assertEqual(RuntimePhase.MODEL_QUEUED, cancelled.session.agents[AgentKey.MAIN].phase)

    def test_nested_subagent_handoff_is_rejected_and_source_call_is_closed(self) -> None:
        runtimes = {
            AgentKey.MAIN: _FakeRuntime(AgentKey.MAIN),
            AgentKey.RESUME: _FakeRuntime(AgentKey.RESUME, target=AgentKey.JOB_SEARCH),
            AgentKey.JOB_SEARCH: _FakeRuntime(AgentKey.JOB_SEARCH),
        }
        orchestrator = Orchestrator(runtimes)
        session = _active_handoff_session()

        result = orchestrator.handle(session, Continue())

        self.assertIsInstance(result.event, ToolFinished)
        self.assertEqual("call-sub", result.event.call_id)
        self.assertEqual(AgentKey.RESUME, result.session.active_agent)
        self.assertEqual(1, len(result.session.handoff_stack))


class _FakeRuntime:
    def __init__(self, key: AgentKey, *, target: AgentKey | None = None) -> None:
        self._key = key
        self._target = target
        self.session_ids: list[str] = []

    def advance(self, state: AgentSessionState, command: object, *, session_id: str) -> RuntimeTransition:
        self.session_ids.append(session_id)
        if isinstance(command, CompleteHandoff):
            return RuntimeTransition(replace(state, phase=RuntimePhase.MODEL_QUEUED, pending_tool=None), ToolFinished(command.call_id, "switch_to_subagent", command.summary))
        if isinstance(command, FailHandoff):
            return RuntimeTransition(replace(state, phase=RuntimePhase.MODEL_QUEUED, pending_tool=None), ToolFinished(command.call_id, "switch_to_subagent", command.message))
        if isinstance(command, Cancel):
            return RuntimeTransition(replace(state, phase=RuntimePhase.CANCELLED), Cancelled(command.reason))
        if self._key is AgentKey.MAIN:
            target = self._target or AgentKey.RESUME
            state = replace(state, phase=RuntimePhase.WAITING_FOR_HANDOFF, pending_tool=PendingToolCall("call-main", "switch_to_subagent", {}), turn_id="turn-main")
            return RuntimeTransition(state, HandoffRequested("call-main", AgentKey.MAIN, target, "context"))
        if isinstance(command, UserMessage):
            return RuntimeTransition(replace(state, phase=RuntimePhase.MODEL_PENDING, turn_id="turn-sub"), Progress("Calling model"))
        if self._target is not None:
            state = replace(state, phase=RuntimePhase.WAITING_FOR_HANDOFF, pending_tool=PendingToolCall("call-sub", "switch_to_subagent", {}), turn_id="turn-sub")
            return RuntimeTransition(state, HandoffRequested("call-sub", self._key, self._target, "nested"))
        state = replace(state, phase=RuntimePhase.WAITING_FOR_HANDOFF, pending_tool=PendingToolCall("call-sub", "switch_to_mainagent", {}), turn_id="turn-sub")
        return RuntimeTransition(state, HandoffRequested("call-sub", AgentKey.RESUME, AgentKey.MAIN, "summary"))


def _session(*, agents: tuple[AgentKey, ...] = (AgentKey.MAIN, AgentKey.RESUME)) -> SessionState:
    return SessionState(
        session_id="session-1",
        active_agent=AgentKey.MAIN,
        agents={key: AgentSessionState() for key in agents},
        handoff_stack=(),
        created_at=_now(),
        updated_at=_now(),
    )


def _active_handoff_session() -> SessionState:
    main = AgentSessionState(
        phase=RuntimePhase.WAITING_FOR_HANDOFF,
        pending_tool=PendingToolCall("call-main", "switch_to_subagent", {}),
        turn_id="turn-main",
    )
    return SessionState(
        session_id="session-1",
        active_agent=AgentKey.RESUME,
        agents={
            AgentKey.MAIN: main,
            AgentKey.RESUME: AgentSessionState(phase=RuntimePhase.MODEL_PENDING, turn_id="turn-sub"),
            AgentKey.JOB_SEARCH: AgentSessionState(),
        },
        handoff_stack=(HandoffFrame(AgentKey.MAIN, AgentKey.RESUME, "call-main", "turn-main", "context"),),
        created_at=_now(),
        updated_at=_now(),
    )


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
