"""Provider-neutral web-search boundary."""

from typing import Protocol

from src.get_me_in.ports.llm import CancellationSignal


class WebSearchPort(Protocol):
    def search(self, query: str, cancellation: CancellationSignal) -> str: ...
    def close(self) -> None: ...
