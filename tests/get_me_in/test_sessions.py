"""Session aggregate domain tests."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import unittest

from src.get_me_in.application.llm_usage import LLMUsageService, LLMPricing, ProfileTokenPricing
from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.commands import Continue, UserMessage
from src.get_me_in.application.events import Progress, ProgressKind, ToolFinished
from src.get_me_in.application.orchestration import SessionTransition
from src.get_me_in.application.session_service import SessionService
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.llm_usage import (
    CostEstimateBasis,
    CostUnavailable,
    CostUnavailableReason,
    EstimatedCost,
    LLMAttemptOutcome,
    LLMAttemptPurpose,
    LLMAttemptReason,
    LLMAttemptRecord,
    LLMAttemptScope,
    ModelProfile,
    ReportedUsage,
    TokenUsage,
)
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
        subagent_record = MessageRecord("event-sub", Role.ASSISTANT, "old episode", _now(), "turn-sub")
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
                AgentKey.RESUME: AgentSessionState(
                    phase=RuntimePhase.MODEL_PENDING,
                    history=(subagent_record,),
                    turn_id="turn-sub",
                    plan=plan,
                ),
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
        self.assertEqual((), snapshot.session.agents[AgentKey.RESUME].history)
        self.assertEqual(["session-1"], access.cleared)
        self.assertIs(snapshot, repository.saved)

    def test_rewind_preserves_lifetime_llm_attempt_ledger(self) -> None:
        session = replace(
            _session("session-1"),
            agents={
                AgentKey.MAIN: AgentSessionState(
                    history=(MessageRecord("event-1", Role.USER, "hello", _now(), "turn-1"),)
                )
            },
            llm_attempts=(_attempt(),),
        )
        service, _, _ = _service(session)

        service.rewind("turn-1")
        snapshot = service.snapshot()

        self.assertEqual((_attempt(),), snapshot.session.llm_attempts)

    def test_session_append_allows_exact_replay_but_rejects_conflict(self) -> None:
        attempt = _attempt()

        self.assertEqual(
            (attempt,),
            SessionService._append_attempt((), attempt),
        )
        self.assertEqual(
            (attempt,),
            SessionService._append_attempt((attempt,), attempt),
        )
        with self.assertRaisesRegex(ValueError, "Conflicting replay"):
            SessionService._append_attempt(
                (attempt,),
                replace(attempt, response_model="different-model"),
            )

    def test_restore_reconciles_known_usage_without_pricing(self) -> None:
        historical = replace(
            _attempt(),
            cost=CostUnavailable(CostUnavailableReason.NO_PRICING),
        )
        restored = SessionSnapshot(
            replace(_session("restored"), llm_attempts=(historical,)),
            _now(),
        )
        pricing = LLMPricing(
            "USD",
            ProfileTokenPricing(Decimal("1"), Decimal("0.5"), Decimal("2")),
            ProfileTokenPricing(Decimal("1"), Decimal("0.5"), Decimal("2")),
        )
        service, _, _ = _service(
            _session("current"),
            restored,
            usage_service=LLMUsageService(pricing),
        )

        service.restore("restored")
        snapshot = service.snapshot()

        self.assertIsInstance(snapshot.session.llm_attempts[0].cost, EstimatedCost)
        self.assertEqual("USD", snapshot.session.llm_attempts[0].cost.unit)

    def test_restore_keeps_known_cost_when_pricing_unit_is_unchanged(self) -> None:
        restored = SessionSnapshot(
            replace(_session("restored"), llm_attempts=(_attempt(),)),
            _now(),
        )
        pricing = LLMPricing(
            "USD",
            ProfileTokenPricing(Decimal("1"), Decimal("0.5"), Decimal("2")),
            ProfileTokenPricing(Decimal("1"), Decimal("0.5"), Decimal("2")),
        )
        service, _, _ = _service(
            _session("current"),
            restored,
            usage_service=LLMUsageService(pricing),
        )

        service.restore("restored")

        cost = service.snapshot().session.llm_attempts[0].cost
        self.assertIsInstance(cost, EstimatedCost)
        self.assertEqual(Decimal("0.001"), cost.amount)
        self.assertEqual("USD", cost.unit)

    def test_restore_reprices_known_cost_when_pricing_unit_changes(self) -> None:
        restored = SessionSnapshot(
            replace(_session("restored"), llm_attempts=(_attempt(),)),
            _now(),
        )
        pricing = LLMPricing(
            "EUR",
            ProfileTokenPricing(Decimal("1"), Decimal("0.5"), Decimal("2")),
            ProfileTokenPricing(Decimal("1"), Decimal("0.5"), Decimal("2")),
        )
        service, _, _ = _service(
            _session("current"),
            restored,
            usage_service=LLMUsageService(pricing),
        )

        service.restore("restored")

        cost = service.snapshot().session.llm_attempts[0].cost
        self.assertIsInstance(cost, EstimatedCost)
        self.assertEqual(Decimal("0.000135"), cost.amount)
        self.assertEqual("EUR", cost.unit)

    def test_restore_clears_old_and_restored_workspace_grants(self) -> None:
        restored = SessionSnapshot(_session("restored"), _now())
        service, _, access = _service(_session("current"), restored)

        view = service.restore("restored")

        self.assertEqual("restored", view.session_id)
        self.assertEqual(["current", "restored"], access.cleared)

    def test_consecutive_restore_clears_each_real_session_scope(self) -> None:
        first = SessionSnapshot(_session("first"), _now())
        second = SessionSnapshot(_session("second"), _now())
        service, repository, access = _service(_session("current"), first)

        service.restore("first")
        repository.loaded = second
        service.restore("second")

        self.assertEqual(["current", "first", "first", "second"], access.cleared)

    def test_restore_clears_inactive_plan_services_before_restoring_active_plan(self) -> None:
        stale_plan = Plan("stale", (PlanItem("item", "stale", PlanStatus.IN_PROGRESS),))
        current = SessionState(
            session_id="current",
            active_agent=AgentKey.MAIN,
            agents={
                AgentKey.MAIN: AgentSessionState(),
                AgentKey.RESUME: AgentSessionState(plan=stale_plan),
            },
            handoff_stack=(),
            created_at=_now(),
            updated_at=_now(),
        )
        restored = SessionSnapshot(_session("restored"), _now())
        service, _, _ = _service(current, restored)

        service.restore("restored")

        self.assertIsNone(service._plans[AgentKey.RESUME].plan)

    def test_typed_start_and_close_signals_clear_plan_service_and_target_state(self) -> None:
        main_plan = Plan("main", (PlanItem("item", "main", PlanStatus.IN_PROGRESS),))
        stale_plan = Plan("stale", (PlanItem("item", "stale", PlanStatus.IN_PROGRESS),))
        frame = HandoffFrame(AgentKey.MAIN, AgentKey.RESUME, "call-1", "turn-1", "context")
        session = SessionState(
            session_id="session-1",
            active_agent=AgentKey.MAIN,
            agents={
                AgentKey.MAIN: AgentSessionState(plan=main_plan),
                AgentKey.RESUME: AgentSessionState(plan=stale_plan),
            },
            handoff_stack=(),
            created_at=_now(),
            updated_at=_now(),
        )
        started_session = replace(
            session,
            active_agent=AgentKey.RESUME,
            agents={AgentKey.MAIN: AgentSessionState(plan=main_plan), AgentKey.RESUME: AgentSessionState()},
            handoff_stack=(frame,),
        )
        closed_session = replace(
            started_session,
            active_agent=AgentKey.MAIN,
            agents={AgentKey.MAIN: AgentSessionState(plan=main_plan), AgentKey.RESUME: AgentSessionState(plan=stale_plan)},
            handoff_stack=(),
        )
        orchestrator = _QueuedOrchestrator(
            [
                SessionTransition(started_session, Progress(ProgressKind.CALLING_MODEL), started_agent=AgentKey.RESUME),
                SessionTransition(closed_session, ToolFinished("call-1", "switch_to_subagent", "done"), closed_agent=AgentKey.RESUME),
            ]
        )
        service, _, _ = _service(session, orchestrator=orchestrator)

        service.handle(UserMessage("delegate"))
        self.assertIsNone(service._plans[AgentKey.RESUME].plan)
        service.handle(Continue())

        self.assertEqual(AgentSessionState(), service._session.agents[AgentKey.RESUME])
        self.assertIsNone(service._plans[AgentKey.RESUME].plan)
        self.assertEqual(main_plan, service._session.agents[AgentKey.MAIN].plan)


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


def _service(
    session: SessionState,
    loaded: SessionSnapshot | None = None,
    *,
    orchestrator=None,
    usage_service: LLMUsageService | None = None,
):
    repository = _Repository(loaded)
    access = _WorkspaceAccess()
    plans = {key: _PlanService() for key in session.agents}
    if loaded is not None:
        plans.update({key: _PlanService() for key in loaded.session.agents if key is not AgentKey.JOB_SEARCH})
    service = SessionService(
        session,
        orchestrator=orchestrator or _Orchestrator(),
        plans=plans,
        repository=repository,
        clock=_Clock(),
        id_generator=_Ids(),
        workspace_access=access,
        usage_service=usage_service,
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


class _QueuedOrchestrator(_Orchestrator):
    def __init__(self, transitions: list[SessionTransition]) -> None:
        self.transitions = transitions

    def handle(self, session: SessionState, command: object) -> SessionTransition:
        del session, command
        return self.transitions.pop(0)


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


def _attempt() -> LLMAttemptRecord:
    return LLMAttemptRecord(
        "attempt-1",
        "call-1",
        1,
        LLMAttemptScope(AgentKey.MAIN, "turn-1", LLMAttemptPurpose.RUNTIME_DECISION),
        LLMAttemptReason.PRIMARY,
        ModelProfile.PRO,
        "provider-model",
        LLMAttemptOutcome.COMPLETED,
        ReportedUsage(TokenUsage(100, 20, cached_input_tokens=10)),
        EstimatedCost(Decimal("0.001"), "USD", CostEstimateBasis.REPORTED_BREAKDOWN),
        _now(),
    )
