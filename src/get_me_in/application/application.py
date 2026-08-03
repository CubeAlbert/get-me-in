"""Application container exposing the typed runtime boundary."""

from pathlib import Path

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.app_commands import (
    ApplicationCommand,
    DumpSession,
    ExitSubAgent,
    RestoreSession,
    RewindSession,
    ReloadKnowledge,
    BuildMemory,
)
from src.get_me_in.application.app_results import (
    ApplicationResult,
    KnowledgeReloaded,
    MemoryBuildScheduled,
    TurnFinalizationResult,
)
from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.app_results import CloseReport
from src.get_me_in.application.resources import ResourceStack
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
        sessions: SessionService,
        tool_catalog: ToolCatalog,
        web_search: WebSearchPort | None = None,
        resources: ResourceStack | None = None,
        knowledge: object | None = None,
        memory: object | None = None,
    ) -> None:
        self.settings = settings
        self.catalog = catalog
        self.clock = clock
        self.id_generator = id_generator
        self.tool_catalog = tool_catalog
        self._sessions = sessions
        self._web_search = web_search
        self._resources = resources
        self._knowledge = knowledge
        self._memory = memory
        self._closed = False
        self._close_report: CloseReport | None = None

    def handle(self, command: RuntimeCommand | ApplicationCommand) -> RuntimeEvent | SessionView | Path | ApplicationResult:
        """Run one typed command without exposing runtime internals."""
        if self._closed:
            raise RuntimeError("Application is closed")
        if isinstance(command, RestoreSession):
            return self.restore(command.session_id)
        if isinstance(command, RewindSession):
            return self.rewind(command.turn_id)
        if isinstance(command, ExitSubAgent):
            return self.exit_subagent(command.summarize)
        if isinstance(command, DumpSession):
            return self.dump()
        if isinstance(command, ReloadKnowledge):
            if self._knowledge is None:
                raise RuntimeError("knowledge service is unavailable")
            return KnowledgeReloaded(self._knowledge.reload(command.target))
        if isinstance(command, BuildMemory):
            if self._memory is None:
                raise RuntimeError("memory service is unavailable")
            return MemoryBuildScheduled(self._memory.build_async(self._sessions.memory_source()))
        return self._sessions.handle(command)

    def view(self) -> SessionView:
        return self._sessions.view()

    def snapshot(self) -> SessionSnapshot:
        return self._sessions.snapshot()

    def restore(self, session_id: str) -> SessionView:
        return self._sessions.restore(session_id)

    def rewind(self, turn_id: str) -> SessionView:
        return self._sessions.rewind(turn_id)

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return self._sessions.list_sessions()

    def dump(self) -> Path:
        return self._sessions.dump()

    def exit_subagent(self, summarize: bool = True) -> RuntimeEvent:
        return self._sessions.exit_subagent(summarize)

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        """Cancel an active blocking call without mutating Runtime state cross-thread."""
        if self._closed:
            raise RuntimeError("Application is closed")
        self._sessions.request_cancel(reason)
        if self._knowledge is not None:
            self._knowledge.request_cancel(reason)

    def finalize_turn(self) -> TurnFinalizationResult:
        """Persist a terminal session and independently schedule optional memory work."""
        snapshot_error: str | None = None
        memory_receipt = None
        memory_error: str | None = None
        try:
            self.snapshot()
        except Exception as error:
            snapshot_error = str(error)
        if self.settings.auto_memory_on_exit and self._memory is not None:
            try:
                memory_receipt = self._memory.build_async(self._sessions.memory_source())
            except Exception as error:
                memory_error = str(error)
        return TurnFinalizationResult(snapshot_error, memory_receipt, memory_error)

    def close(self) -> CloseReport:
        if self._close_report is not None:
            return self._close_report
        self._closed = True
        if self._resources is not None:
            self._close_report = self._resources.close()
        else:
            self._sessions.close()
            if self._web_search is not None:
                self._web_search.close()
            self._close_report = CloseReport(
                closed=("sessions", "web_search") if self._web_search is not None else ("sessions",)
            )
        return self._close_report
