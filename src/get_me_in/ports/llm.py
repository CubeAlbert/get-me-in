"""Provider-independent synchronous model-completion contract."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from src.get_me_in.domain.messages import Role


class CancellationRegistrationPort(Protocol):
    def close(self) -> None: ...


class CancellationSignal(Protocol):
    @property
    def is_cancelled(self) -> bool: ...

    def register(self, callback: Callable[[], None]) -> CancellationRegistrationPort: ...


class ModelProfile(StrEnum):
    PRO = "pro"
    FLASH = "flash"


@dataclass(frozen=True)
class LLMMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class LLMRequest:
    messages: tuple[LLMMessage, ...]
    profile: ModelProfile
    timeout_seconds: float
    temperature: float | None = None


@dataclass(frozen=True)
class LLMResult:
    content: str


class LLMPort(Protocol):
    def complete(
        self,
        request: LLMRequest,
        cancellation: CancellationSignal,
    ) -> LLMResult: ...

    def close(self) -> None: ...
