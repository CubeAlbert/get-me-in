"""Pricing, context safety, and read-only projections for LLM usage."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from math import ceil, floor, isfinite

from src.get_me_in.domain.llm_usage import (
    CostEstimateBasis,
    CostMeasurement,
    CostUnavailable,
    CostUnavailableReason,
    EstimatedCost,
    LLMAttemptOutcome,
    LLMAttemptPurpose,
    LLMAttemptReason,
    LLMAttemptRecord,
    LLMAttemptScope,
    ModelProfile,
    ReportedUsage,
    TokenUsage,
    UnavailableUsage,
    UsageMeasurement,
)
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.ports.llm import LLMRequest


class ContextSafetyStatus(StrEnum):
    SAFE = "safe"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ContextEstimate:
    estimated_input_tokens: int
    usable_context_tokens: int
    threshold_ratio: float
    threshold_tokens: int
    utilization_ratio: float
    status: ContextSafetyStatus


def _validate_price(value: Decimal, label: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
        raise ValueError(f"{label} must be a finite, non-negative Decimal")


@dataclass(frozen=True)
class ProfileTokenPricing:
    input_per_million: Decimal
    cached_input_per_million: Decimal
    output_per_million: Decimal

    def __post_init__(self) -> None:
        _validate_price(self.input_per_million, "input_per_million")
        _validate_price(self.cached_input_per_million, "cached_input_per_million")
        _validate_price(self.output_per_million, "output_per_million")


@dataclass(frozen=True)
class LLMPricing:
    unit: str
    pro: ProfileTokenPricing
    flash: ProfileTokenPricing

    def __post_init__(self) -> None:
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("unit must be a non-empty string")
        object.__setattr__(self, "unit", self.unit.strip().upper())

    def for_profile(self, profile: ModelProfile) -> ProfileTokenPricing:
        if profile is ModelProfile.PRO:
            return self.pro
        if profile is ModelProfile.FLASH:
            return self.flash
        raise ValueError(f"Unsupported model profile: {profile!r}")


@dataclass(frozen=True)
class TokenTotals:
    input_tokens: int
    cached_input_tokens: int
    uncached_input_tokens: int
    assumed_uncached_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class CostTotals:
    amount: Decimal
    unit: str | None
    unknown_attempts: int


@dataclass(frozen=True)
class UsageGroupView:
    agent: AgentKey
    purpose: LLMAttemptPurpose
    logical_calls: int
    attempts: int
    tokens: TokenTotals
    usage_unknown_attempts: int
    costs: CostTotals


@dataclass(frozen=True)
class UsageView:
    context: ContextEstimate
    logical_calls: int
    attempts: int
    tokens: TokenTotals
    usage_unknown_attempts: int
    costs: CostTotals
    groups: tuple[UsageGroupView, ...]
    recent_attempts: tuple[LLMAttemptRecord, ...]


class ContextSizer:
    """Estimate a complete request using a deterministic linear heuristic."""

    def estimate(self, request: LLMRequest) -> int:
        total = 2 + len(request.messages) * 4
        for message in request.messages:
            ascii_count = sum(ord(character) < 128 for character in message.content)
            non_ascii_count = len(message.content) - ascii_count
            total += ceil(ascii_count / 4) + non_ascii_count
        return total


class ContextPolicy:
    def __init__(
        self,
        sizer: ContextSizer,
        *,
        usable_context_tokens: int,
        threshold_ratio: float,
    ) -> None:
        if not isinstance(usable_context_tokens, int) or isinstance(usable_context_tokens, bool) or usable_context_tokens < 1:
            raise ValueError("usable_context_tokens must be a positive integer")
        if not isfinite(threshold_ratio) or not 0 < threshold_ratio < 1:
            raise ValueError("threshold_ratio must be finite and between 0 and 1")
        self._sizer = sizer
        self._usable_context_tokens = usable_context_tokens
        self._threshold_ratio = threshold_ratio

    def evaluate(self, request: LLMRequest) -> ContextEstimate:
        estimated = self._sizer.estimate(request)
        threshold = floor(self._usable_context_tokens * self._threshold_ratio)
        return ContextEstimate(
            estimated_input_tokens=estimated,
            usable_context_tokens=self._usable_context_tokens,
            threshold_ratio=self._threshold_ratio,
            threshold_tokens=threshold,
            utilization_ratio=estimated / self._usable_context_tokens,
            status=(
                ContextSafetyStatus.BLOCKED
                if estimated >= threshold
                else ContextSafetyStatus.SAFE
            ),
        )


class LLMUsageService:
    def __init__(self, pricing: LLMPricing | None) -> None:
        self._pricing = pricing

    def build_attempt(
        self,
        *,
        attempt_id: str,
        logical_call_id: str,
        attempt_index: int,
        scope: LLMAttemptScope,
        reason: LLMAttemptReason,
        request_profile: ModelProfile,
        response_model: str | None,
        outcome: LLMAttemptOutcome,
        usage: UsageMeasurement,
        terminal_at: datetime,
    ) -> LLMAttemptRecord:
        cost = self._cost_for(request_profile, usage)
        return LLMAttemptRecord(
            attempt_id=attempt_id,
            logical_call_id=logical_call_id,
            attempt_index=attempt_index,
            scope=scope,
            reason=reason,
            request_profile=request_profile,
            response_model=response_model,
            outcome=outcome,
            usage=usage,
            cost=cost,
            terminal_at=terminal_at,
        )

    def reconcile_restored(
        self,
        attempts: tuple[LLMAttemptRecord, ...],
    ) -> tuple[LLMAttemptRecord, ...]:
        if self._pricing is None:
            return attempts
        return tuple(
            attempt
            if not self._needs_reconciliation(attempt)
            else self._replace_cost(attempt)
            for attempt in attempts
        )

    def usage_view(
        self,
        attempts: tuple[LLMAttemptRecord, ...],
        context: ContextEstimate,
    ) -> UsageView:
        tokens = _token_totals(attempts)
        costs = _cost_totals(attempts)
        groups: dict[tuple[AgentKey, LLMAttemptPurpose], list[LLMAttemptRecord]] = defaultdict(list)
        for attempt in attempts:
            groups[(attempt.scope.agent, attempt.scope.purpose)].append(attempt)
        group_views = tuple(
            _group_view(agent, purpose, grouped)
            for (agent, purpose), grouped in sorted(
                groups.items(), key=lambda item: (item[0][0].value, item[0][1].value)
            )
        )
        return UsageView(
            context=context,
            logical_calls=len({attempt.logical_call_id for attempt in attempts}),
            attempts=len(attempts),
            tokens=tokens,
            usage_unknown_attempts=sum(
                isinstance(attempt.usage, UnavailableUsage) for attempt in attempts
            ),
            costs=costs,
            groups=group_views,
            recent_attempts=attempts[-10:],
        )

    def _needs_reconciliation(self, attempt: LLMAttemptRecord) -> bool:
        if not isinstance(attempt.usage, ReportedUsage):
            return False
        if isinstance(attempt.cost, CostUnavailable):
            return attempt.cost.reason is CostUnavailableReason.NO_PRICING
        return attempt.cost.unit != self._pricing.unit

    def _replace_cost(self, attempt: LLMAttemptRecord) -> LLMAttemptRecord:
        return LLMAttemptRecord(
            attempt_id=attempt.attempt_id,
            logical_call_id=attempt.logical_call_id,
            attempt_index=attempt.attempt_index,
            scope=attempt.scope,
            reason=attempt.reason,
            request_profile=attempt.request_profile,
            response_model=attempt.response_model,
            outcome=attempt.outcome,
            usage=attempt.usage,
            cost=self._cost_for(attempt.request_profile, attempt.usage),
            terminal_at=attempt.terminal_at,
        )

    def _cost_for(self, profile: ModelProfile, usage: UsageMeasurement) -> CostMeasurement:
        if isinstance(usage, UnavailableUsage):
            return CostUnavailable(CostUnavailableReason.USAGE_UNAVAILABLE)
        if self._pricing is None:
            return CostUnavailable(CostUnavailableReason.NO_PRICING)
        value = usage.value
        pricing = self._pricing.for_profile(profile)
        cached = value.cached_input_tokens or 0
        amount = (
            Decimal(value.uncached_input_tokens) * pricing.input_per_million
            + Decimal(cached) * pricing.cached_input_per_million
            + Decimal(value.output_tokens) * pricing.output_per_million
        ) / Decimal(1_000_000)
        basis = (
            CostEstimateBasis.REPORTED_BREAKDOWN
            if value.cached_input_tokens is not None
            else CostEstimateBasis.ASSUMED_UNCACHED
        )
        return EstimatedCost(amount, self._pricing.unit, basis)


def _empty_tokens() -> TokenTotals:
    return TokenTotals(0, 0, 0, 0, 0, 0, 0)


def _token_totals(attempts: tuple[LLMAttemptRecord, ...] | list[LLMAttemptRecord]) -> TokenTotals:
    values = [attempt.usage.value for attempt in attempts if isinstance(attempt.usage, ReportedUsage)]
    if not values:
        return _empty_tokens()
    return TokenTotals(
        input_tokens=sum(value.input_tokens for value in values),
        cached_input_tokens=sum(value.cached_input_tokens or 0 for value in values),
        uncached_input_tokens=sum(value.uncached_input_tokens for value in values),
        assumed_uncached_input_tokens=sum(
            value.input_tokens for value in values if value.cached_input_tokens is None
        ),
        output_tokens=sum(value.output_tokens for value in values),
        reasoning_output_tokens=sum(value.reasoning_output_tokens or 0 for value in values),
        total_tokens=sum(value.total_tokens for value in values),
    )


def _cost_totals(attempts: tuple[LLMAttemptRecord, ...] | list[LLMAttemptRecord]) -> CostTotals:
    known = [attempt.cost for attempt in attempts if isinstance(attempt.cost, EstimatedCost)]
    units = {cost.unit for cost in known}
    if len(units) > 1:
        raise ValueError("All estimated costs must use one billing unit")
    return CostTotals(
        amount=sum((cost.amount for cost in known), Decimal("0")),
        unit=next(iter(units), None),
        unknown_attempts=sum(isinstance(attempt.cost, CostUnavailable) for attempt in attempts),
    )


def _group_view(
    agent: AgentKey,
    purpose: LLMAttemptPurpose,
    attempts: list[LLMAttemptRecord],
) -> UsageGroupView:
    return UsageGroupView(
        agent=agent,
        purpose=purpose,
        logical_calls=len({attempt.logical_call_id for attempt in attempts}),
        attempts=len(attempts),
        tokens=_token_totals(attempts),
        usage_unknown_attempts=sum(
            isinstance(attempt.usage, UnavailableUsage) for attempt in attempts
        ),
        costs=_cost_totals(attempts),
    )
