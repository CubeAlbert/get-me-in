"""Session aggregate domain tests."""

from datetime import datetime, timezone
from pathlib import Path
import unittest

from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.session_service import SessionService
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus
from src.get_me_in.domain.sessions import AgentSessionState, HandoffFrame, PendingToolCall, RuntimePhase, SessionState


class SessionDomainTests(unittest.TestCase):
    def test_session_owns_agent_state_without_runtime_imports(self) -> None:
        record = MessageRecord("event-1", Role.USER, "hello", _now(), "turn-1")
        agent_state = AgentSessionState(history=(record,))
        session = SessionState(
            session_id="session-1",
            active_agent=AgentKey.MAIN,
            agents={AgentKey.MAIN: agent_state},
            handoff_stack=(),
            created_at=_now(),
            updated_at=_now(),
        )

        self.assertEqual(RuntimePhase.READY, session.agents[AgentKey.MAIN].phase)
        self.assertEqual("turn-1", session.agents[AgentKey.MAIN].history[0].turn_id)

    def test_restore_rejects_unavailable_agents_without_replacing_active_session(self) -> None:
        current = _session("current")
        unavailable = SessionSnapshot(
            SessionState(
                session_id="unavailable",
                active_agent=AgentKey.JOB_SEARCH,
                agents={AgentKey.JOB_SEARCH: AgentSessionState()},
                handoff_stack=(),
                created_at=_now(),
                updated_at=_now(),
            ),
            _now(),
        )
        service, _, _ = _service(current, unavailable)

        with self.assertRaisesRegex(ValueError, "unavailable agents"):
            service.restore("unavailable")

        self.assertEqual("current", service.view().session_id)

    def test_rewind_clears_plan_pending_handoff_and_workspace_grants(self) -> None:
        user = MessageRecord("event-1", Role.USER, "delegate", _now(), "turn-1")
        call = ToolCallRecord("event-2", "call-1", "switch_to_subagent", {}, _now(), "turn-1")
        plan = Plan("plan-1", (PlanItem("item-1", "delegate", PlanStatus.IN_PROGRESS),))
        session = SessionState(
            session_id="session-1",
            active_agent=AgentKey.RESUME,
            agents={
                AgentKey.MAIN: AgentSessionState(
                    phase=RuntimePhase.WAITING_FOR_HANDOFF,
                    history=(user, call),
                    pending_tool=PendingToolCall("call-1", "switch_to_subagent", {}),
                    turn_id="turn-1",
                    plan=plan,
                ),
                AgentKey.RESUME: AgentSessionState(phase=RuntimePhase.MODEL_PENDING, turn_id="turn-sub", plan=plan),
            },
            handoff_stack=(HandoffFrame(AgentKey.MAIN, AgentKey.RESUME, "call-1", "turn-1", "context"),),
            created_at=_now(),
            updated_at=_now(),
        )
        service, repository, access = _service(session)

        view = service.rewind("turn-1")
        snapshot = service.snapshot()

        self.assertEqual(AgentKey.MAIN, view.active_agent)
        self.assertEqual(RuntimePhase.READY, view.phase)
        self.assertIsNone(view.plan)
        self.assertEqual((), snapshot.session.handoff_stack)
        self.assertTrue(all(state.pending_tool is None and state.plan is None for state in snapshot.session.agents.values()))
        self.assertEqual(["session-1"], access.cleared)
        self.assertIs(snapshot, repository.saved)

    def test_restore_clears_old_and_restored_workspace_grants(self) -> None:
        restored = SessionSnapshot(_session("restored"), _now())
        service, _, access = _service(_session("current"), restored)

        view = service.restore("restored")

        self.assertEqual("restored", view.session_id)
        self.assertEqual(["current", "restored"], access.cleared)


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)


def _session(session_id: str) -> SessionState:
    return SessionState(
        session_id=session_id,
        active_agent=AgentKey.MAIN,
        agents={AgentKey.MAIN: AgentSessionState()},
        handoff_stack=(),
        created_at=_now(),
        updated_at=_now(),
    )


def _service(session: SessionState, loaded: SessionSnapshot | None = None):
    repository = _Repository(loaded)
    access = _WorkspaceAccess()
    plans = {key: _PlanService() for key in session.agents}
    if loaded is not None:
        plans.update({key: _PlanService() for key in loaded.session.agents if key is not AgentKey.JOB_SEARCH})
    service = SessionService(
        session,
        orchestrator=_Orchestrator(),
        plans=plans,
        repository=repository,
        clock=_Clock(),
        id_generator=_Ids(),
        workspace_access=access,
    )
    return service, repository, access


class _Repository:
    def __init__(self, loaded: SessionSnapshot | None) -> None:
        self.loaded = loaded
        self.saved: SessionSnapshot | None = None

    def save(self, snapshot: SessionSnapshot) -> None:
        self.saved = snapshot

    def load(self, session_id: str) -> SessionSnapshot:
        del session_id
        assert self.loaded is not None
        return self.loaded

    def list(self):
        return ()

    def dump(self, snapshot: SessionSnapshot) -> Path:
        del snapshot
        return Path("dump.json")

    def close(self) -> None:
        pass


class _Orchestrator:
    def close(self) -> None:
        pass


class _PlanService:
    def __init__(self) -> None:
        self.plan = None

    def restore(self, plan) -> None:
        self.plan = plan

    def snapshot(self):
        return self.plan


class _WorkspaceAccess:
    def __init__(self) -> None:
        self.cleared: list[str] = []

    def clear_session(self, session_id: str) -> None:
        self.cleared.append(session_id)


class _Clock:
    def now(self):
        return _now()


class _Ids:
    def new_id(self) -> str:
        return "new-id"
