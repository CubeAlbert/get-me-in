"""Minimal model-completion port; request details are introduced in R2."""

from typing import Protocol


class CancellationSignal(Protocol):
    """Read-only cancellation view accepted by blocking adapters."""

    @property
    def is_cancelled(self) -> bool: ...


class LLMPort(Protocol):
    def complete(self, prompt: str, cancellation: CancellationSignal) -> str: ...
