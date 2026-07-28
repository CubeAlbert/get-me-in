"""Hub-and-Spoke orchestration tests using a dedicated test sub-agent."""

from dataclasses import replace
from datetime import datetime, timezone
import unittest

from src.get_me_in.application.commands import Cancel, CancelSelection, CompleteHandoff, Continue, FailHandoff, UserMessage
from src.get_me_in.application.events import Cancelled, Failed, HandoffRequested, Paused, Progress, RuntimeEvent, ToolFinished
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

    def test_subagent_failure_returns_to_main_without_queuing_another_model_call(self) -> None:
        orchestrator = Orchestrator(
            {
                AgentKey.MAIN: _FakeRuntime(AgentKey.MAIN),
                AgentKey.RESUME: _FakeRuntime(
                    AgentKey.RESUME,
                    failure=Failed("provider_failure", "provider is unavailable"),
                ),
            }
        )
        started = orchestrator.handle(_session(), UserMessage("delegate"))

        failed = orchestrator.handle(started.session, Continue())

        self.assertIsInstance(failed.event, Failed)
        self.assertEqual("subagent_failed", failed.event.code)
        self.assertEqual(AgentKey.MAIN, failed.session.active_agent)
        self.assertEqual((), failed.session.handoff_stack)
        self.assertEqual(RuntimePhase.FAILED, failed.session.agents[AgentKey.MAIN].phase)

    def test_model_reply_parse_failure_pauses_subagent_for_user_continuation(self) -> None:
        resume = _FakeRuntime(
            AgentKey.RESUME,
            failure=Paused("invalid_model_reply", "complete raw failure is in the log"),
        )
        orchestrator = Orchestrator(
            {
                AgentKey.MAIN: _FakeRuntime(AgentKey.MAIN),
                AgentKey.RESUME: resume,
            }
        )
        started = orchestrator.handle(_session(), UserMessage("delegate"))

        paused = orchestrator.handle(started.session, Continue())
        continued = orchestrator.handle(paused.session, UserMessage("继续当前简历任务"))

        self.assertIsInstance(paused.event, Paused)
        self.assertEqual("invalid_model_reply", paused.event.code)
        self.assertEqual(AgentKey.RESUME, paused.session.active_agent)
        self.assertEqual(1, len(paused.session.handoff_stack))
        self.assertEqual(RuntimePhase.WAITING_FOR_USER, paused.session.agents[AgentKey.RESUME].phase)
        self.assertEqual(AgentKey.RESUME, continued.session.active_agent)
        self.assertEqual(1, len(continued.session.handoff_stack))
        self.assertEqual(UserMessage("继续当前简历任务"), resume.commands[-1])

    def test_selection_cancellation_keeps_subagent_handoff_active(self) -> None:
        orchestrator = Orchestrator(
            {
                AgentKey.MAIN: _FakeRuntime(AgentKey.MAIN),
                AgentKey.RESUME: _FakeRuntime(AgentKey.RESUME),
            }
        )
        session = _active_selection_handoff_session()

        result = orchestrator.handle(
            session,
            CancelSelection("choice-call"),
        )

        self.assertIsInstance(result.event, ToolFinished)
        self.assertEqual("choice-call", result.event.call_id)
        self.assertEqual(AgentKey.RESUME, result.session.active_agent)
        self.assertEqual(1, len(result.session.handoff_stack))
        self.assertEqual(
            RuntimePhase.MODEL_QUEUED,
            result.session.agents[AgentKey.RESUME].phase,
        )

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
    def __init__(self, key: AgentKey, *, target: AgentKey | None = None, failure: RuntimeEvent | None = None) -> None:
        self._key = key
        self._target = target
        self._failure = failure
        self.session_ids: list[str] = []
        self.cancel_reasons: list[str] = []
        self.commands: list[object] = []

    def advance(self, state: AgentSessionState, command: object, *, session_id: str) -> RuntimeTransition:
        self.commands.append(command)
        self.session_ids.append(session_id)
        if isinstance(command, CompleteHandoff):
            return RuntimeTransition(replace(state, phase=RuntimePhase.MODEL_QUEUED, pending_tool=None), ToolFinished(command.call_id, "switch_to_subagent", command.summary))
        if isinstance(command, FailHandoff):
            if command.terminal:
                return RuntimeTransition(
                    replace(state, phase=RuntimePhase.FAILED, pending_tool=None),
                    Failed(command.code, command.message),
                )
            return RuntimeTransition(replace(state, phase=RuntimePhase.MODEL_QUEUED, pending_tool=None), ToolFinished(command.call_id, "switch_to_subagent", command.message))
        if isinstance(command, Cancel):
            return RuntimeTransition(replace(state, phase=RuntimePhase.CANCELLED), Cancelled(command.reason))
        if isinstance(command, CancelSelection):
            return RuntimeTransition(
                replace(
                    state,
                    phase=RuntimePhase.MODEL_QUEUED,
                    pending_tool=None,
                ),
                ToolFinished(
                    command.request_id,
                    "provide_choices",
                    command.reason,
                ),
            )
        if self._key is AgentKey.MAIN:
            target = self._target or AgentKey.RESUME
            state = replace(state, phase=RuntimePhase.WAITING_FOR_HANDOFF, pending_tool=PendingToolCall("call-main", "switch_to_subagent", {}), turn_id="turn-main")
            return RuntimeTransition(state, HandoffRequested("call-main", AgentKey.MAIN, target, "context"))
        if isinstance(command, UserMessage):
            return RuntimeTransition(replace(state, phase=RuntimePhase.MODEL_PENDING, turn_id="turn-sub"), Progress("Calling model"))
        if self._failure is not None:
            return RuntimeTransition(
                replace(
                    state,
                    phase=RuntimePhase.WAITING_FOR_USER
                    if isinstance(self._failure, Paused)
                    else RuntimePhase.FAILED,
                    pending_tool=None,
                ),
                self._failure,
            )
        if self._target is not None:
            state = replace(state, phase=RuntimePhase.WAITING_FOR_HANDOFF, pending_tool=PendingToolCall("call-sub", "switch_to_subagent", {}), turn_id="turn-sub")
            return RuntimeTransition(state, HandoffRequested("call-sub", self._key, self._target, "nested"))
        state = replace(state, phase=RuntimePhase.WAITING_FOR_HANDOFF, pending_tool=PendingToolCall("call-sub", "switch_to_mainagent", {}), turn_id="turn-sub")
        return RuntimeTransition(state, HandoffRequested("call-sub", AgentKey.RESUME, AgentKey.MAIN, "summary"))

    def request_cancel(self, reason: str) -> None:
        self.cancel_reasons.append(reason)


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


def _active_selection_handoff_session() -> SessionState:
    session = _active_handoff_session()
    resume = AgentSessionState(
        phase=RuntimePhase.WAITING_FOR_SELECTION,
        pending_tool=PendingToolCall("choice-call", "provide_choices", {}),
        turn_id="turn-sub",
    )
    return replace(
        session,
        agents={
            AgentKey.MAIN: session.agents[AgentKey.MAIN],
            AgentKey.RESUME: resume,
            AgentKey.JOB_SEARCH: session.agents[AgentKey.JOB_SEARCH],
        },
    )


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
