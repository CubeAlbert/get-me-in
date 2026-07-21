"""Minimal v2 application container for the R1 composition root."""

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.settings import Settings
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.ports.clock import Clock
from src.get_me_in.ports.ids import IdGenerator
from src.get_me_in.ports.llm import LLMPort


class TemporaryConversationUnavailableError(RuntimeError):
    """Raised when the R1 temporary conversation has no injected LLM port."""


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
        llm: LLMPort | None = None,
    ) -> None:
        self.settings = settings
        self.catalog = catalog
        self.prompt_renderer = prompt_renderer
        self.clock = clock
        self.id_generator = id_generator
        self.cancellation = cancellation
        self._llm = llm
        self._closed = False

    def complete_text(self, text: str) -> str:
        """Run one no-tool completion.

        TEMP-R1: remove this method when R2's typed AgentRuntime owns model calls.
        It intentionally has no history, tools, handoff, session, or retry behavior.
        """
        if self._closed:
            raise RuntimeError("Application is closed")
        if not text.strip():
            raise ValueError("text must not be blank")
        if self._llm is None:
            raise TemporaryConversationUnavailableError(
                "Inject an LLMPort to use the temporary R1 conversation"
            )

        self.cancellation.reset()
        prompt = self.prompt_renderer.render(self.catalog.get(AgentKey.MAIN))
        return self._llm.complete(f"{prompt}\n\nUser: {text}", self.cancellation)

    def close(self) -> None:
        self._closed = True
        self.cancellation.cancel()
