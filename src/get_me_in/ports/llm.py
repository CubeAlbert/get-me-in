"""Provider-independent synchronous model-completion contract."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from src.get_me_in.domain.llm_usage import (
    ModelProfile,
    UnavailableUsage,
    UsageMeasurement,
    UsageUnavailableReason,
)
from src.get_me_in.domain.messages import Role


class CancellationRegistrationPort(Protocol):
    def close(self) -> None: ...


class CancellationSignal(Protocol):
    @property
    def is_cancelled(self) -> bool: ...

    def register(self, callback: Callable[[], None]) -> CancellationRegistrationPort: ...


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
    content: str | None
    response_model: str | None = None
    usage: UsageMeasurement = UnavailableUsage(UsageUnavailableReason.NOT_REPORTED)


class LLMPort(Protocol):
    def complete(
        self,
        request: LLMRequest,
        cancellation: CancellationSignal,
    ) -> LLMResult: ...

    def close(self) -> None: ...
