"""Provider-independent synchronous model-completion contract."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from src.get_me_in.domain.messages import ConversationEvent


class CancellationSignal(Protocol):
    """Read-only cancellation view accepted by blocking adapters."""

    @property
    def is_cancelled(self) -> bool: ...


class ModelProfile(StrEnum):
    """Configured model tiers used by declarative agent specifications."""

    PRO = "pro"
    FLASH = "flash"


@dataclass(frozen=True)
class LLMRequest:
    """Complete provider-neutral request for one synchronous model call."""

    messages: tuple[ConversationEvent, ...]
    profile: ModelProfile
    timeout_seconds: float


@dataclass(frozen=True)
class LLMResult:
    """Raw assistant payload returned by a provider adapter."""

    content: str


class LLMPort(Protocol):
    def complete(
        self,
        request: LLMRequest,
        cancellation: CancellationSignal,
    ) -> LLMResult: ...

    def close(self) -> None: ...
