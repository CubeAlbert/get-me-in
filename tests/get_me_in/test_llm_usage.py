"""Pure domain and application tests for B00 token usage accounting."""

from datetime import datetime, timezone
from decimal import Decimal
import unittest

from src.get_me_in.application.llm_usage import (
    ContextPolicy,
    ContextSafetyStatus,
    ContextSizer,
    LLMUsageService,
    LLMPricing,
    ProfileTokenPricing,
)
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.llm_usage import (
    CostUnavailable,
    CostUnavailableReason,
    CostEstimateBasis,
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
    UsageUnavailableReason,
)
from src.get_me_in.domain.messages import Role
from src.get_me_in.ports.llm import LLMMessage, LLMRequest


_NOW = datetime(2026, 8, 10, 12, tzinfo=timezone.utc)


class LLMUsageTests(unittest.TestCase):
    def test_context_sizer_uses_the_declared_linear_formula(self) -> None:
        request = LLMRequest(
            messages=(LLMMessage(Role.USER, "abcde中文"),),
            profile=ModelProfile.PRO,
            timeout_seconds=1,
        )

        self.assertEqual(10, ContextSizer().estimate(request))

    def test_context_policy_blocks_at_the_threshold(self) -> None:
        policy = ContextPolicy(
            ContextSizer(), usable_context_tokens=10, threshold_ratio=0.9
        )
        request = LLMRequest(
            messages=(LLMMessage(Role.USER, "abcde中文"),),
            profile=ModelProfile.PRO,
            timeout_seconds=1,
        )

        estimate = policy.evaluate(request)

        self.assertEqual(9, estimate.threshold_tokens)
        self.assertEqual(ContextSafetyStatus.BLOCKED, estimate.status)

    def test_pricing_distinguishes_reported_cache_breakdown(self) -> None:
        pricing = LLMPricing(
            " usd ",
            ProfileTokenPricing(Decimal("1"), Decimal("2"), Decimal("3")),
            ProfileTokenPricing(Decimal("4"), Decimal("5"), Decimal("6")),
        )
        service = LLMUsageService(pricing)
        scope = LLMAttemptScope(AgentKey.MAIN, "turn-1", LLMAttemptPurpose.RUNTIME_DECISION)

        attempt = service.build_attempt(
            attempt_id="attempt-1",
            logical_call_id="call-1",
            attempt_index=1,
            scope=scope,
            reason=LLMAttemptReason.PRIMARY,
            request_profile=ModelProfile.PRO,
            response_model="provider-model",
            outcome=LLMAttemptOutcome.COMPLETED,
            usage=ReportedUsage(TokenUsage(100, 30, cached_input_tokens=20)),
            terminal_at=_NOW,
        )

        self.assertEqual("USD", attempt.cost.unit)
        self.assertEqual(Decimal("0.00021"), attempt.cost.amount)
        self.assertEqual("reported_breakdown", attempt.cost.basis.value)

    def test_missing_usage_pricing_keeps_typed_unknown_cost(self) -> None:
        service = LLMUsageService(None)
        scope = LLMAttemptScope(AgentKey.MAIN, "turn-1", LLMAttemptPurpose.RUNTIME_DECISION)

        attempt = service.build_attempt(
            attempt_id="attempt-1",
            logical_call_id="call-1",
            attempt_index=1,
            scope=scope,
            reason=LLMAttemptReason.PRIMARY,
            request_profile=ModelProfile.PRO,
            response_model=None,
            outcome=LLMAttemptOutcome.COMPLETED,
            usage=UnavailableUsage(UsageUnavailableReason.NOT_REPORTED),
            terminal_at=_NOW,
        )

        self.assertIsInstance(attempt.cost, CostUnavailable)
        self.assertEqual(CostUnavailableReason.USAGE_UNAVAILABLE, attempt.cost.reason)

    def test_estimated_cost_basis_matches_cached_input_availability(self) -> None:
        scope = LLMAttemptScope(AgentKey.MAIN, "turn-1", LLMAttemptPurpose.RUNTIME_DECISION)

        with self.assertRaisesRegex(ValueError, "basis"):
            LLMAttemptRecord(
                "attempt-1",
                "call-1",
                1,
                scope,
                LLMAttemptReason.PRIMARY,
                ModelProfile.PRO,
                "provider-model",
                LLMAttemptOutcome.COMPLETED,
                ReportedUsage(TokenUsage(10, 2)),
                EstimatedCost(Decimal("0"), "USD", CostEstimateBasis.REPORTED_BREAKDOWN),
                _NOW,
            )

    def test_attempt_record_rejects_invalid_scope_type(self) -> None:
        with self.assertRaisesRegex(TypeError, "scope"):
            LLMAttemptRecord(
                "attempt-1",
                "call-1",
                1,
                object(),
                LLMAttemptReason.PRIMARY,
                ModelProfile.PRO,
                "provider-model",
                LLMAttemptOutcome.COMPLETED,
                ReportedUsage(TokenUsage(10, 2)),
                EstimatedCost(Decimal("0"), "USD", CostEstimateBasis.ASSUMED_UNCACHED),
                _NOW,
            )

    def test_usage_view_aggregates_without_double_counting_reasoning_tokens(self) -> None:
        service = LLMUsageService(None)
        scope = LLMAttemptScope(AgentKey.MAIN, "turn-1", LLMAttemptPurpose.RUNTIME_DECISION)
        first = service.build_attempt(
            attempt_id="attempt-1",
            logical_call_id="call-1",
            attempt_index=1,
            scope=scope,
            reason=LLMAttemptReason.PRIMARY,
            request_profile=ModelProfile.PRO,
            response_model="model",
            outcome=LLMAttemptOutcome.COMPLETED,
            usage=ReportedUsage(TokenUsage(100, 30, reasoning_output_tokens=10)),
            terminal_at=_NOW,
        )
        second = service.build_attempt(
            attempt_id="attempt-2",
            logical_call_id="call-2",
            attempt_index=1,
            scope=LLMAttemptScope(AgentKey.RESUME, "turn-2", LLMAttemptPurpose.RUNTIME_DECISION),
            reason=LLMAttemptReason.PRIMARY,
            request_profile=ModelProfile.FLASH,
            response_model=None,
            outcome=LLMAttemptOutcome.TIMEOUT,
            usage=UnavailableUsage(UsageUnavailableReason.NO_RESPONSE),
            terminal_at=_NOW,
        )
        context = ContextPolicy(ContextSizer(), usable_context_tokens=1000, threshold_ratio=0.95).evaluate(
            LLMRequest((), ModelProfile.PRO, 1)
        )

        view = service.usage_view((first, second), context)

        self.assertEqual(2, view.attempts)
        self.assertEqual(130, view.tokens.total_tokens)
        self.assertEqual(10, view.tokens.reasoning_output_tokens)
        self.assertEqual(1, view.usage_unknown_attempts)
        self.assertEqual(2, len(view.groups))
        self.assertEqual((first, second), view.recent_attempts)

    def test_non_completed_attempt_requires_no_response_usage(self) -> None:
        scope = LLMAttemptScope(AgentKey.MAIN, "turn-1", LLMAttemptPurpose.RUNTIME_DECISION)
        with self.assertRaises(ValueError):
            from src.get_me_in.domain.llm_usage import LLMAttemptRecord, EstimatedCost, CostEstimateBasis

            LLMAttemptRecord(
                "attempt-1",
                "call-1",
                1,
                scope,
                LLMAttemptReason.PRIMARY,
                ModelProfile.PRO,
                None,
                LLMAttemptOutcome.TIMEOUT,
                ReportedUsage(TokenUsage(1, 1)),
                EstimatedCost(Decimal("0"), "USD", CostEstimateBasis.ASSUMED_UNCACHED),
                _NOW,
            )
