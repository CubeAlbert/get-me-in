"""Tests for explicit tool catalog visibility and execution boundaries."""

import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey, Capability
from src.get_me_in.domain.tools import (
    ConfirmationMode,
    ToolDefinition,
    ToolFailure,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)


class ToolCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.public = _tool("clock")
        self.resume_only = _tool(
            "resume_read",
            capabilities=frozenset({Capability.WORKSPACE_READ}),
        )
        self.catalog = ToolCatalog((self.public, self.resume_only))

    def test_visibility_is_capability_based(self) -> None:
        visible = self.catalog.list_for_capabilities(frozenset({Capability.ROUTE}))

        self.assertEqual((self.public,), visible)

    def test_export_descriptors_reflects_real_catalog(self) -> None:
        self.assertEqual(("clock", "resume_read"), tuple(item["name"] for item in self.catalog.export_descriptors()))

    def test_duplicate_names_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ToolCatalog((self.public, _tool("clock")))


class ToolExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken())

    def test_validates_arguments_before_running_handler(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("echo"),)))

        outcome = executor.execute("call", "echo", {}, self.context)

        self.assertIsInstance(outcome, ToolFailure)
        self.assertEqual("missing_argument", outcome.code)

    def test_requires_explicit_approval(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("delete", confirmation=ConfirmationMode.ALWAYS),)))

        outcome = executor.execute("call", "delete", {"text": "x"}, self.context)

        self.assertEqual("approval", outcome.kind)

    def test_rejection_and_cancellation_close_the_call_without_handler_execution(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("echo"),)))
        rejected = ToolContext("session", AgentKey.MAIN, CancellationToken(), rejected=True)
        cancelled_token = CancellationToken()
        cancelled_token.cancel()
        cancelled = ToolContext("session", AgentKey.MAIN, cancelled_token)

        self.assertEqual("rejected", executor.execute("call", "echo", {"text": "x"}, rejected).code)
        self.assertEqual("cancelled", executor.execute("call", "echo", {"text": "x"}, cancelled).code)

    def test_execution_respects_agent_capabilities(self) -> None:
        definition = _tool(
            "resume_read",
            capabilities=frozenset({Capability.WORKSPACE_READ}),
        )
        executor = ToolExecutor(ToolCatalog((definition,)))

        outcome = executor.execute(
            "call",
            "resume_read",
            {"text": "x"},
            self.context,
            frozenset({Capability.ROUTE}),
        )

        self.assertIsInstance(outcome, ToolFailure)
        self.assertEqual("tool_not_permitted", outcome.code)

    def test_context_exposes_plan_and_workspace_to_handlers(self) -> None:
        plan = PlanService(_Ids())
        workspace = object()
        captured: dict[str, object] = {}
        definition = ToolDefinition(
            name="inspect_context",
            description="inspect context",
            schema=ToolSchema(properties={}, required=frozenset()),
            policy=ToolPolicy(),
            handler=lambda arguments, context: _capture_context(captured, context),
        )
        executor = ToolExecutor(ToolCatalog((definition,)))
        context = ToolContext("session", AgentKey.MAIN, CancellationToken(), plan, workspace)

        outcome = executor.execute("call", "inspect_context", {}, context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertIs(plan, captured["plan"])
        self.assertIs(workspace, captured["workspace"])

    def test_returns_handler_data_as_typed_success(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("echo"),)))

        outcome = executor.execute("call", "echo", {"text": "x"}, self.context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual({"echo": "x"}, outcome.output)


def _tool(
    name: str,
    *,
    capabilities: frozenset[Capability] = frozenset(),
    confirmation: ConfirmationMode = ConfirmationMode.NEVER,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description=name,
        schema=ToolSchema(properties={"text": str}, required=frozenset({"text"})),
        policy=ToolPolicy(capabilities, confirmation),
        handler=lambda arguments, context: ToolSuccess({"echo": arguments["text"]}),
    )


def _capture_context(captured: dict[str, object], context: ToolContext) -> ToolSuccess:
    captured["plan"] = context.plan
    captured["workspace"] = context.workspace
    return ToolSuccess("captured")


class _Ids:
    def __init__(self) -> None:
        self._value = 0

    def new_id(self) -> str:
        self._value += 1
        return str(self._value)
