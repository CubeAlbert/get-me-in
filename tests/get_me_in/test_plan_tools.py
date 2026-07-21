"""Tests for PlanService-backed explicit tool definitions."""

import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolFailure, ToolSuccess
from src.get_me_in.tools.plan import build_plan_tools


class PlanToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executor = ToolExecutor(ToolCatalog(build_plan_tools()))
        self.context = ToolContext(
            "session", AgentKey.MAIN, CancellationToken(), plan=PlanService(_Ids())
        )

    def test_create_update_and_replan_return_structured_plan_payloads(self) -> None:
        created = self.executor.execute(
            "create", "create_plan", {"items": ["first", "second"]}, self.context
        )

        self.assertIsInstance(created, ToolSuccess)
        first_id = created.output["items"][0]["id"]
        updated = self.executor.execute(
            "update", "update_plan_status", {"id": first_id, "status": "completed"}, self.context
        )
        replanned = self.executor.execute(
            "replan", "replan", {"items": ["replacement"]}, self.context
        )

        self.assertEqual("in_progress", updated.output["items"][1]["status"])
        self.assertEqual("replacement", replanned.output["items"][-1]["description"])

    def test_invalid_status_returns_a_business_failure(self) -> None:
        self.executor.execute("create", "create_plan", {"items": ["first"]}, self.context)

        outcome = self.executor.execute(
            "update", "update_plan_status", {"id": "missing", "status": "unknown"}, self.context
        )

        self.assertIsInstance(outcome, ToolFailure)
        self.assertEqual("invalid_plan_status", outcome.code)


class _Ids:
    def __init__(self) -> None:
        self.value = 0

    def new_id(self) -> str:
        self.value += 1
        return str(self.value)
