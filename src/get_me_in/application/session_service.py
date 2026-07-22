"""Application service owning exactly one active session aggregate."""

from dataclasses import replace

from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.orchestration import Orchestrator
from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.sessions import AgentSessionState, SessionPreview, SessionState, SessionView
from src.get_me_in.ports.clock import Clock
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
        workspace_access: WorkspaceAccessState,
    ) -> None:
        self._session = session
        self._orchestrator = orchestrator
        self._plans = plans
        self._repository = repository
        self._clock = clock
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
        return SessionView(self._session.session_id, self._session.active_agent, active.phase, active.plan)

    def snapshot(self) -> SessionSnapshot:
        snapshot = SessionSnapshot(self._session, self._clock.now())
        self._repository.save(snapshot)
        return snapshot

    def restore(self, session_id: str) -> SessionView:
        snapshot = self._repository.load(session_id)
        if not isinstance(snapshot, SessionSnapshot):
            raise TypeError("Session repository returned an invalid snapshot")
        self._workspace_access.clear_session(self._session.session_id)
        self._workspace_access.clear_session(snapshot.session.session_id)
        self._session = snapshot.session
        self._plans[self._session.active_agent].restore(self._session.agents[self._session.active_agent].plan)
        return self.view()

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return self._repository.list()

    def exit_subagent(self) -> RuntimeEvent:
        transition = self._orchestrator.exit_subagent(self._session)
        self._session = replace(transition.session, updated_at=self._clock.now())
        return transition.event

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        self._orchestrator.request_cancel(reason)

    def close(self) -> None:
        self._orchestrator.close()
        self._repository.close()
