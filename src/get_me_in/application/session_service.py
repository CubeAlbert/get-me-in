"""Application service owning exactly one active session aggregate."""

from dataclasses import replace
from pathlib import Path

from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.orchestration import Orchestrator
from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.domain.agents import AgentKey
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
    ) -> None:
        self._session = session
        self._orchestrator = orchestrator
        self._plans = plans
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator
        self._workspace_access = workspace_access

    def handle(self, command: RuntimeCommand) -> RuntimeEvent:
        active_key = self._session.active_agent
        self._plans[active_key].restore(self._session.agents[active_key].plan)
        transition = self._orchestrator.handle(self._session, command)
        agents = dict(transition.session.agents)
        agents[active_key] = replace(agents[active_key], plan=self._plans[active_key].snapshot())
        self._session = replace(transition.session, agents=agents, updated_at=self._clock.now())
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
        self._session = snapshot.session
        self._plans[self._session.active_agent].restore(self._session.agents[self._session.active_agent].plan)
        return self.view()

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return self._repository.list()

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
            key: AgentSessionState(history=tuple(record for record in state.history if record.timestamp < boundary))
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
        self._plans[active_key].restore(self._session.agents[active_key].plan)
        transition = self._orchestrator.exit_subagent(self._session, summarize)
        agents = dict(transition.session.agents)
        agents[active_key] = replace(agents[active_key], plan=self._plans[active_key].snapshot())
        self._session = replace(transition.session, agents=agents, updated_at=self._clock.now())
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
        agents: dict[AgentKey, AgentSessionState] = {}
        for key, state in session.agents.items():
            if state.phase in safe:
                agents[key] = state
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
                cancel_reason="Interrupted before snapshot",
            )
        return replace(session, agents=agents, updated_at=self._clock.now())
