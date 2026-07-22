"""Application service owning exactly one active session aggregate."""

from dataclasses import replace

from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.domain.sessions import AgentSessionState, SessionPreview, SessionState, SessionView
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.sessions import SessionRepository


class SessionService:
    """Coordinates runtime transitions while retaining the only SessionState copy."""

    def __init__(
        self,
        session: SessionState,
        *,
        runtime: AgentRuntime,
        plans: PlanService,
        repository: SessionRepository,
        clock: Clock,
        workspace_access: WorkspaceAccessState,
    ) -> None:
        self._session = session
        self._runtime = runtime
        self._plans = plans
        self._repository = repository
        self._clock = clock
        self._workspace_access = workspace_access

    def handle(self, command: RuntimeCommand) -> RuntimeEvent:
        active = self._session.agents[self._session.active_agent]
        self._plans.restore(active.plan)
        transition = self._runtime.advance(active, command)
        updated_agent = replace(transition.state, plan=self._plans.snapshot())
        agents = dict(self._session.agents)
        agents[self._session.active_agent] = updated_agent
        self._session = replace(self._session, agents=agents, updated_at=self._clock.now())
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
        self._plans.restore(self._session.agents[self._session.active_agent].plan)
        return self.view()

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return self._repository.list()

    def close(self) -> None:
        self._repository.close()
