"""Minimal v2 application container for the R1 composition root."""

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.settings import Settings
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator


class Application:
    """Owns R1 dependencies without exposing a temporary conversation API."""

    def __init__(
        self,
        *,
        settings: Settings,
        catalog: AgentCatalog,
        prompt_renderer: PromptRenderer,
        clock: Clock,
        id_generator: IdGenerator,
        cancellation: CancellationToken,
    ) -> None:
        self.settings = settings
        self.catalog = catalog
        self.prompt_renderer = prompt_renderer
        self.clock = clock
        self.id_generator = id_generator
        self.cancellation = cancellation
        self._closed = False

    def close(self) -> None:
        self._closed = True
        self.cancellation.cancel()
