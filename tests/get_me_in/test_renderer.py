"""Focused tests for safe rendering of the interactive usage projection."""

from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path
import unittest

from rich.console import Console

from src.get_me_in.application.localization import Locale
from src.get_me_in.application.llm_usage import (
    ContextEstimate,
    ContextSafetyStatus,
    CostTotals,
    TokenTotals,
    UsageGroupView,
    UsageView,
)
from src.get_me_in.cli.localization import load_translator
from src.get_me_in.cli.renderer import Renderer
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.llm_usage import (
    LLMAttemptOutcome,
    LLMAttemptPurpose,
    LLMAttemptReason,
    LLMAttemptRecord,
    LLMAttemptScope,
    ModelProfile,
    ReportedUsage,
    TokenUsage,
    EstimatedCost,
    CostEstimateBasis,
)


class RendererUsageTests(unittest.TestCase):
    def test_usage_render_is_a_safe_summary_without_prompt_or_response_content(self) -> None:
        output = StringIO()
        attempt = LLMAttemptRecord(
            attempt_id="attempt-1",
            logical_call_id="call-1",
            attempt_index=1,
            scope=LLMAttemptScope(
                agent=AgentKey.MAIN,
                turn_id="turn-1",
                purpose=LLMAttemptPurpose.RUNTIME_DECISION,
            ),
            reason=LLMAttemptReason.PRIMARY,
            request_profile=ModelProfile.PRO,
            response_model="provider-model",
            outcome=LLMAttemptOutcome.COMPLETED,
            usage=ReportedUsage(TokenUsage(input_tokens=8, output_tokens=3)),
            cost=EstimatedCost(
                Decimal("0.000011"),
                "USD",
                CostEstimateBasis.ASSUMED_UNCACHED,
            ),
            terminal_at=datetime(2026, 8, 10, tzinfo=timezone.utc),
        )
        view = UsageView(
            context=ContextEstimate(120, 230000, 0.95, 218500, 0.01, ContextSafetyStatus.SAFE),
            logical_calls=1,
            attempts=1,
            tokens=TokenTotals(8, 0, 8, 8, 3, 0, 11),
            usage_unknown_attempts=0,
            costs=CostTotals(Decimal("0.000011"), "USD", 0),
            groups=(
                UsageGroupView(
                    AgentKey.MAIN,
                    LLMAttemptPurpose.RUNTIME_DECISION,
                    1,
                    1,
                    TokenTotals(8, 0, 8, 8, 3, 0, 11),
                    0,
                    CostTotals(Decimal("0.000011"), "USD", 0),
                ),
            ),
            recent_attempts=(attempt,),
        )
        renderer = Renderer(
            console=Console(file=output, force_terminal=False, color_system=None),
            translator=load_translator(
                Path(__file__).resolve().parents[2] / "data/locales",
                Locale.EN_US,
            ),
        )

        renderer.render_usage(view)

        rendered = output.getvalue()
        self.assertIn("Usage", rendered)
        self.assertIn("attempt-1", rendered)
        self.assertIn("11", rendered)
        self.assertNotIn("provider-model", rendered)
        self.assertNotIn("prompt", rendered.casefold())
        self.assertNotIn("raw-response", rendered.casefold())


if __name__ == "__main__":
    unittest.main()
