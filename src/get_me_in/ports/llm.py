"""Minimal model-completion port; request details are introduced in R2."""

from typing import Protocol

from src.get_me_in.application.cancellation import CancellationToken


class LLMPort(Protocol):
    def complete(self, prompt: str, cancellation: CancellationToken) -> str: ...
