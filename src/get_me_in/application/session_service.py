"""Application service owning exactly one active session aggregate."""

from dataclasses import replace
from pathlib import Path

from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.llm_usage import LLMUsageService, UsageView
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.orchestration import Orchestrator, SessionTransition
from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.llm_usage import LLMAttemptRecord
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord, ToolResultRecord
from src.get_me_in.domain.memories import MemoryBuildSource
from src.get_me_in.domain.sessions import RuntimePhase
from src.get_me_in.domain.sessions import (
    AgentSessionState,
    SessionPreview,
    SessionState,
    SessionTurnView,
    SessionView,
)
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.sessions import SessionRepository


class SessionService:
    """Coordinates runtime transitions while retaining the only SessionState copy."""

    def __init__(
        self,
        session: SessionState,
        *,
        orchestrator: Orchestrator,
        plans: dict[AgentKey, PlanService],
        repository: SessionRepository,
        clock: Clock,
        id_generator: IdGenerator,
        workspace_access: WorkspaceAccessState,
        usage_service: LLMUsageService | None = None,
    ) -> None:
        self._session = session
        self._orchestrator = orchestrator
        self._plans = plans
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator
        self._workspace_access = workspace_access
        self._usage_service = usage_service or LLMUsageService(None)

    def handle(self, command: RuntimeCommand) -> RuntimeEvent:
        active_key = self._session.active_agent
        self._restore_active_plan()
        transition = self._orchestrator.handle(self._session, command)
        self._session = self._apply_transition(active_key, transition)
        return transition.event

    def view(self) -> SessionView:
        active = self._session.agents[self._session.active_agent]
        rewind_points = tuple(
            SessionTurnView(record.turn_id, key, record.content, record.timestamp)
            for key, state in self._session.agents.items()
            for record in state.history
            if key is AgentKey.MAIN
            and isinstance(record, MessageRecord)
            and record.role is Role.USER
            and record.turn_id
        )
        return SessionView(
            self._session.session_id,
            self._session.active_agent,
            active.phase,
            active.plan,
            tuple(sorted(rewind_points, key=lambda item: item.timestamp)),
        )

    def snapshot(self) -> SessionSnapshot:
        self._session = self._normalise_snapshot_state(self._session)
        snapshot = SessionSnapshot(self._session, self._clock.now())
        self._repository.save(snapshot)
        return snapshot

    def restore(self, session_id: str) -> SessionView:
        snapshot = self._repository.load(session_id)
        if not isinstance(snapshot, SessionSnapshot):
            raise TypeError("Session repository returned an invalid snapshot")
        unavailable = set(snapshot.session.agents) - set(self._plans)
        if unavailable:
            names = ", ".join(sorted(key.value for key in unavailable))
            raise ValueError(f"Session requires unavailable agents: {names}")
        self._workspace_access.clear_session(self._session.session_id)
        self._workspace_access.clear_session(snapshot.session.session_id)
        self._session = replace(
            snapshot.session,
            llm_attempts=self._usage_service.reconcile_restored(snapshot.session.llm_attempts),
        )
        self._restore_active_plan()
        return self.view()

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return self._repository.list()

    def usage_view(self) -> UsageView:
        context = self._orchestrator.context_estimate(self._session)
        return self._usage_service.usage_view(self._session.llm_attempts, context)

    def dump(self) -> Path:
        snapshot = self.snapshot()
        return self._repository.dump(snapshot)

    def rewind(self, turn_id: str) -> SessionView:
        matching = [
            record.timestamp
            for state in self._session.agents.values()
            for record in state.history
            if record.turn_id == turn_id
        ]
        if not matching:
            raise KeyError(turn_id)
        boundary = min(matching)
        agents = {
            key: AgentSessionState(
                history=tuple(record for record in state.history if record.timestamp < boundary)
            ) if key is AgentKey.MAIN else AgentSessionState()
            for key, state in self._session.agents.items()
        }
        self._workspace_access.clear_session(self._session.session_id)
        self._session = replace(
            self._session,
            agents=agents,
            active_agent=AgentKey.MAIN,
            handoff_stack=(),
            updated_at=self._clock.now(),
        )
        for plan in self._plans.values():
            plan.restore(None)
        return self.view()

    def exit_subagent(self, summarize: bool = True) -> RuntimeEvent:
        active_key = self._session.active_agent
        self._restore_active_plan()
        transition = self._orchestrator.exit_subagent(self._session, summarize)
        self._session = self._apply_transition(active_key, transition)
        return transition.event

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        self._orchestrator.request_cancel(self._session, reason)

    def memory_source(self) -> MemoryBuildSource:
        state = self._session.agents[self._session.active_agent]
        records = tuple(
            replace(record, thinking=None) if isinstance(record, (MessageRecord, ToolCallRecord)) else record
            for record in state.history
        )
        return MemoryBuildSource(self._session.session_id, self._session.active_agent, records)

    def close(self) -> None:
        self._orchestrator.close()
        self._repository.close()

    def _normalise_snapshot_state(self, session: SessionState) -> SessionState:
        safe = {
            RuntimePhase.READY,
            RuntimePhase.WAITING_FOR_APPROVAL,
            RuntimePhase.WAITING_FOR_SELECTION,
            RuntimePhase.WAITING_FOR_HANDOFF,
            RuntimePhase.WAITING_FOR_USER,
            RuntimePhase.COMPLETED,
            RuntimePhase.CANCELLED,
            RuntimePhase.FAILED,
        }
        active_target = session.handoff_stack[-1].target if session.handoff_stack else None
        agents: dict[AgentKey, AgentSessionState] = {}
        for key, state in session.agents.items():
            if key is not AgentKey.MAIN and key is not active_target:
                agents[key] = AgentSessionState()
                continue
            if state.phase in safe:
                agents[key] = replace(state, pending_logical_call=None)
                continue
            history = state.history
            if state.pending_tool is not None:
                pending = state.pending_tool
                history = (*history, ToolResultRecord(
                    event_id=self._id_generator.new_id(),
                    call_id=pending.call_id,
                    tool_name=pending.tool_name,
                    output={"code": "cancelled", "message": "Interrupted before snapshot"},
                    timestamp=self._clock.now(),
                    turn_id=state.turn_id,
                    plan=state.plan,
                ))
            agents[key] = replace(
                state,
                phase=RuntimePhase.CANCELLED,
                history=history,
                pending_tool=None,
                pending_logical_call=None,
                cancel_reason="Interrupted before snapshot",
            )
        return replace(session, agents=agents, updated_at=self._clock.now())

    def _restore_active_plan(self) -> None:
        active_key = self._session.active_agent
        for key, plan in self._plans.items():
            plan.restore(self._session.agents[active_key].plan if key is active_key else None)

    def _apply_transition(self, previous_active_key: AgentKey, transition: SessionTransition) -> SessionState:
        agents = dict(transition.session.agents)
        if transition.closed_agent is previous_active_key:
            self._plans[previous_active_key].restore(None)
            agents[previous_active_key] = replace(agents[previous_active_key], plan=None)
        else:
            agents[previous_active_key] = replace(
                agents[previous_active_key],
                plan=self._plans[previous_active_key].snapshot(),
            )
        for key in (transition.started_agent, transition.closed_agent):
            if key is not None and key in self._plans:
                self._plans[key].restore(None)
        if transition.closed_agent is not None:
            agents[transition.closed_agent] = replace(agents[transition.closed_agent], plan=None)
        attempts = self._append_attempt(transition.session.llm_attempts, transition.attempt)
        return replace(
            transition.session,
            agents=agents,
            llm_attempts=attempts,
            updated_at=self._clock.now(),
        )

    @staticmethod
    def _append_attempt(
        attempts: tuple[LLMAttemptRecord, ...],
        attempt: LLMAttemptRecord | None,
    ) -> tuple[LLMAttemptRecord, ...]:
        if attempt is None:
            return attempts
        for existing in attempts:
            if existing.attempt_id == attempt.attempt_id:
                if existing == attempt:
                    return attempts
                raise ValueError("Conflicting replay for LLM attempt id")
            if (
                existing.logical_call_id == attempt.logical_call_id
                and existing.attempt_index == attempt.attempt_index
            ):
                raise ValueError("Conflicting replay for logical call attempt index")
        same_call = [item for item in attempts if item.logical_call_id == attempt.logical_call_id]
        if not same_call:
            if attempt.attempt_index != 1:
                raise ValueError("A new logical call must start at attempt index 1")
            if attempt.reason.value != "primary":
                raise ValueError("A new logical call must start with PRIMARY")
        else:
            expected_index = max(item.attempt_index for item in same_call) + 1
            if attempt.attempt_index != expected_index:
                raise ValueError("Logical call attempt indexes must be contiguous")
            first = same_call[0]
            if attempt.scope != first.scope or attempt.request_profile != first.request_profile:
                raise ValueError("Logical call scope and profile must remain stable")
            if attempt.reason.value == "primary":
                raise ValueError("PRIMARY may only be used for the first attempt")
        return (*attempts, attempt)
