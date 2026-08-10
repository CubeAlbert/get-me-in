"""Immutable domain facts for interactive LLM attempt accounting."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from math import isfinite
from typing import TypeAlias

from src.get_me_in.domain.agents import AgentKey


class ModelProfile(StrEnum):
    PRO = "pro"
    FLASH = "flash"


class LLMAttemptPurpose(StrEnum):
    RUNTIME_DECISION = "runtime_decision"


class LLMAttemptReason(StrEnum):
    PRIMARY = "primary"
    FORMAT_REPAIR = "format_repair"
    EXPLICIT_RETRY = "explicit_retry"


class LLMAttemptOutcome(StrEnum):
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    FAILED = "failed"


class UsageUnavailableReason(StrEnum):
    NOT_REPORTED = "not_reported"
    NO_RESPONSE = "no_response"
    MALFORMED = "malformed"


class CostUnavailableReason(StrEnum):
    NO_PRICING = "no_pricing"
    USAGE_UNAVAILABLE = "usage_unavailable"


class CostEstimateBasis(StrEnum):
    REPORTED_BREAKDOWN = "reported_breakdown"
    ASSUMED_UNCACHED = "assumed_uncached"


def _non_empty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _non_negative_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _finite_non_negative_decimal(value: Decimal, label: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError(f"{label} must be a finite, non-negative Decimal")


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int | None = None
    reasoning_output_tokens: int | None = None

    def __post_init__(self) -> None:
        _non_negative_int(self.input_tokens, "input_tokens")
        _non_negative_int(self.output_tokens, "output_tokens")
        if self.cached_input_tokens is not None:
            _non_negative_int(self.cached_input_tokens, "cached_input_tokens")
            if self.cached_input_tokens > self.input_tokens:
                raise ValueError("cached_input_tokens must not exceed input_tokens")
        if self.reasoning_output_tokens is not None:
            _non_negative_int(self.reasoning_output_tokens, "reasoning_output_tokens")
            if self.reasoning_output_tokens > self.output_tokens:
                raise ValueError("reasoning_output_tokens must not exceed output_tokens")

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def uncached_input_tokens(self) -> int:
        if self.cached_input_tokens is None:
            return self.input_tokens
        return self.input_tokens - self.cached_input_tokens


@dataclass(frozen=True)
class ReportedUsage:
    value: TokenUsage

    def __post_init__(self) -> None:
        if not isinstance(self.value, TokenUsage):
            raise TypeError("ReportedUsage.value must be TokenUsage")


@dataclass(frozen=True)
class UnavailableUsage:
    reason: UsageUnavailableReason

    def __post_init__(self) -> None:
        if not isinstance(self.reason, UsageUnavailableReason):
            raise TypeError("UnavailableUsage.reason must be UsageUnavailableReason")


UsageMeasurement: TypeAlias = ReportedUsage | UnavailableUsage


@dataclass(frozen=True)
class EstimatedCost:
    amount: Decimal
    unit: str
    basis: CostEstimateBasis

    def __post_init__(self) -> None:
        _finite_non_negative_decimal(self.amount, "amount")
        if not isinstance(self.basis, CostEstimateBasis):
            raise TypeError("basis must be CostEstimateBasis")
        unit = _non_empty(self.unit, "unit").strip().upper()
        object.__setattr__(self, "unit", unit)


@dataclass(frozen=True)
class CostUnavailable:
    reason: CostUnavailableReason

    def __post_init__(self) -> None:
        if not isinstance(self.reason, CostUnavailableReason):
            raise TypeError("reason must be CostUnavailableReason")


CostMeasurement: TypeAlias = EstimatedCost | CostUnavailable


@dataclass(frozen=True)
class LLMAttemptScope:
    agent: AgentKey
    turn_id: str
    purpose: LLMAttemptPurpose
    handoff_episode_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.agent, AgentKey):
            raise TypeError("agent must be AgentKey")
        if not isinstance(self.purpose, LLMAttemptPurpose):
            raise TypeError("purpose must be LLMAttemptPurpose")
        _non_empty(self.turn_id, "turn_id")
        if self.handoff_episode_id is not None:
            _non_empty(self.handoff_episode_id, "handoff_episode_id")


@dataclass(frozen=True)
class LLMAttemptRecord:
    attempt_id: str
    logical_call_id: str
    attempt_index: int
    scope: LLMAttemptScope
    reason: LLMAttemptReason
    request_profile: ModelProfile
    response_model: str | None
    outcome: LLMAttemptOutcome
    usage: UsageMeasurement
    cost: CostMeasurement
    terminal_at: datetime

    def __post_init__(self) -> None:
        for value, label, expected in (
            (self.reason, "reason", LLMAttemptReason),
            (self.request_profile, "request_profile", ModelProfile),
            (self.outcome, "outcome", LLMAttemptOutcome),
        ):
            if not isinstance(value, expected):
                raise TypeError(f"{label} has an invalid type")
        if not isinstance(self.usage, (ReportedUsage, UnavailableUsage)):
            raise TypeError("usage has an invalid type")
        if not isinstance(self.cost, (EstimatedCost, CostUnavailable)):
            raise TypeError("cost has an invalid type")
        _non_empty(self.attempt_id, "attempt_id")
        _non_empty(self.logical_call_id, "logical_call_id")
        if not isinstance(self.attempt_index, int) or isinstance(self.attempt_index, bool) or self.attempt_index < 1:
            raise ValueError("attempt_index must be a positive integer")
        if self.response_model is not None:
            _non_empty(self.response_model, "response_model")
        if not isinstance(self.terminal_at, datetime) or self.terminal_at.tzinfo is None:
            raise ValueError("terminal_at must include a timezone")
        self._validate_outcome_contract()

    def _validate_outcome_contract(self) -> None:
        if self.outcome is LLMAttemptOutcome.COMPLETED:
            if isinstance(self.usage, UnavailableUsage) and self.usage.reason is UsageUnavailableReason.NO_RESPONSE:
                raise ValueError("COMPLETED attempt cannot use NO_RESPONSE usage")
            if isinstance(self.usage, ReportedUsage):
                if isinstance(self.cost, CostUnavailable) and self.cost.reason is CostUnavailableReason.USAGE_UNAVAILABLE:
                    raise ValueError("Reported usage cannot use USAGE_UNAVAILABLE cost")
                if isinstance(self.cost, EstimatedCost):
                    expected_basis = (
                        CostEstimateBasis.REPORTED_BREAKDOWN
                        if self.usage.value.cached_input_tokens is not None
                        else CostEstimateBasis.ASSUMED_UNCACHED
                    )
                    if self.cost.basis is not expected_basis:
                        raise ValueError(
                            "Estimated cost basis must match cached input token availability"
                        )
            elif not (
                isinstance(self.cost, CostUnavailable)
                and self.cost.reason is CostUnavailableReason.USAGE_UNAVAILABLE
            ):
                raise ValueError("Unavailable usage requires USAGE_UNAVAILABLE cost")
            return

        if self.response_model is not None:
            raise ValueError("A non-completed attempt cannot have a response model")
        if not (
            isinstance(self.usage, UnavailableUsage)
            and self.usage.reason is UsageUnavailableReason.NO_RESPONSE
        ):
            raise ValueError("A non-completed attempt requires NO_RESPONSE usage")
        if not (
            isinstance(self.cost, CostUnavailable)
            and self.cost.reason is CostUnavailableReason.USAGE_UNAVAILABLE
        ):
            raise ValueError("A non-completed attempt requires USAGE_UNAVAILABLE cost")
