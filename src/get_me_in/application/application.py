"""v2 application container exposing the typed runtime boundary."""

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.settings import Settings
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.web_search import WebSearchPort


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
        self._web_search = web_search
        self._closed = False

    def handle(self, command: RuntimeCommand) -> tuple[RuntimeEvent, ...]:
        """Run one typed command without exposing runtime internals."""
        if self._closed:
            raise RuntimeError("Application is closed")
        return self._runtime.handle(command)

    def close(self) -> None:
        self._closed = True
        self._runtime.close()
        if self._web_search is not None:
            self._web_search.close()
