"""v2 application container exposing the typed runtime boundary."""

from pathlib import Path

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.app_commands import (
    ApplicationCommand,
    DumpSession,
    ExitSubAgent,
    RestoreSession,
    RewindSession,
)
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.session_codec import SessionSnapshot
from src.get_me_in.application.session_service import SessionService
from src.get_me_in.application.settings import Settings
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.web_search import WebSearchPort
from src.get_me_in.domain.sessions import SessionPreview, SessionView


class Application:
    """Owns R1 dependencies without exposing a temporary conversation API."""

    def __init__(
        self,
        *,
        settings: Settings,
        catalog: AgentCatalog,
        clock: Clock,
        id_generator: IdGenerator,
        cancellation: CancellationToken,
        runtime: AgentRuntime,
        sessions: SessionService,
        tool_catalog: ToolCatalog,
        web_search: WebSearchPort | None = None,
    ) -> None:
        self.settings = settings
        self.catalog = catalog
        self.clock = clock
        self.id_generator = id_generator
        self.cancellation = cancellation
        self.tool_catalog = tool_catalog
        self._runtime = runtime
        self._sessions = sessions
        self._web_search = web_search
        self._closed = False

    def handle(self, command: RuntimeCommand | ApplicationCommand) -> RuntimeEvent | SessionView | Path:
        """Run one typed command without exposing runtime internals."""
        if self._closed:
            raise RuntimeError("Application is closed")
        if isinstance(command, RestoreSession):
            return self.restore(command.session_id)
        if isinstance(command, RewindSession):
            return self._sessions.rewind(command.turn_id)
        if isinstance(command, ExitSubAgent):
            return self._sessions.exit_subagent()
        if isinstance(command, DumpSession):
            return self._sessions.dump()
        return self._sessions.handle(command)

    def view(self) -> SessionView:
        return self._sessions.view()

    def snapshot(self) -> SessionSnapshot:
        return self._sessions.snapshot()

    def restore(self, session_id: str) -> SessionView:
        return self._sessions.restore(session_id)

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return self._sessions.list_sessions()

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        """Cancel an active blocking call without mutating Runtime state cross-thread."""
        if self._closed:
            raise RuntimeError("Application is closed")
        self._sessions.request_cancel(reason)

    def close(self) -> None:
        self._closed = True
        self._sessions.close()
        if self._web_search is not None:
            self._web_search.close()
