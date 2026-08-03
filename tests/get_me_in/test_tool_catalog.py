"""Tests for explicit tool catalog visibility and execution boundaries."""

import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey, Capability
from src.get_me_in.domain.tools import (
    ConfirmationMode,
    ToolApproval,
    ToolDefinition,
    ToolFailure,
    ToolParameter,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)
from src.get_me_in.tools.customer_file import build_customer_file_tools
from src.get_me_in.tools.plan import build_plan_tools
from src.get_me_in.tools.resume import build_resume_tools
from src.get_me_in.tools.retrieval import build_retrieval_tools
from src.get_me_in.tools.switch import build_switch_tools
from src.get_me_in.tools.system import build_system_tools
from src.get_me_in.tools.web import build_web_tools
from src.get_me_in.tools.workspace import build_workspace_tools


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
        descriptors = self.catalog.export_descriptors()

        self.assertEqual(
            ("clock", "resume_read"),
            tuple(item["name"] for item in descriptors),
        )
        self.assertEqual("clock", descriptors[0]["purpose"])
        self.assertEqual("when needed", descriptors[0]["use_when"])

    def test_schema_rejects_undeclared_required_argument(self) -> None:
        with self.assertRaises(ValueError):
            ToolSchema({}, frozenset({"missing"}))

    def test_schema_rejects_required_argument_with_default(self) -> None:
        with self.assertRaises(ValueError):
            ToolSchema(
                {"text": ToolParameter(str, "text", default="value")},
                frozenset({"text"}),
            )

    def test_null_default_requires_explicit_nullable_contract(self) -> None:
        with self.assertRaises(ValueError):
            ToolParameter(str, "optional filter", default=None)

    def test_duplicate_names_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ToolCatalog((self.public, _tool("clock")))


class ProductionToolMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definitions = (
            *build_system_tools(object()),
            *build_plan_tools(),
            *build_workspace_tools(100, 50, 50),
            *build_web_tools(),
            *build_switch_tools(),
            *build_customer_file_tools(100),
            *build_retrieval_tools("app.log", 5),
            *build_resume_tools(),
        )
        self.by_name = {
            definition.name: definition for definition in self.definitions
        }

    def test_all_26_tools_have_complete_llm_facing_guidance(self) -> None:
        self.assertEqual(26, len(self.definitions))
        self.assertEqual(26, len(self.by_name))
        for definition in self.definitions:
            self.assertTrue(definition.purpose.strip(), definition.name)
            self.assertTrue(definition.use_when.strip(), definition.name)
            self.assertTrue(definition.expected_output.strip(), definition.name)
            for name, parameter in definition.schema.properties.items():
                self.assertTrue(parameter.description.strip(), f"{definition.name}.{name}")

    def test_legacy_selection_boundaries_and_defaults_are_preserved(self) -> None:
        current_datetime = self.by_name["get_current_datetime"]
        working_dir = self.by_name["get_working_dir"]
        memory = self.by_name["query_memory"]
        reference = self.by_name["query_reference_data"]
        self.assertEqual(
            frozenset({Capability.CURRENT_DATETIME}),
            current_datetime.policy.required_capabilities,
        )
        self.assertEqual(
            frozenset({Capability.WORKSPACE_READ}),
            working_dir.policy.required_capabilities,
        )
        self.assertEqual(
            frozenset({Capability.MEMORY_QUERY}),
            memory.policy.required_capabilities,
        )
        self.assertEqual(
            frozenset({Capability.KNOWLEDGE_QUERY}),
            reference.policy.required_capabilities,
        )
        self.assertIn("query_memory", reference.do_not_use_when)
        self.assertEqual(5, memory.schema.properties["top_k"].default)
        self.assertEqual(
            ("fact", "preference"),
            memory.schema.properties["memory_type"].allowed_values,
        )

    def test_query_memory_is_explicit_or_last_resort_only(self) -> None:
        memory = self.by_name["query_memory"]

        self.assertEqual(
            "仅在以下情况使用：用户明确要求查询其已保存的个人背景、技术栈、经历、偏好或期望；"
            "或者完成当前任务必须获得某项个人信息，该信息不在当前对话中，已先向用户询问但仍未获得有效答案，"
            "需要将历史记忆作为最后一次补充尝试。查询必须聚焦于当前明确缺失的信息。",
            memory.use_when,
        )
        self.assertEqual(
            "不要为了主动了解用户、补充用户画像、个性化回答、减少普通提问或确认已知信息而调用。"
            "当前对话、文件或工具结果已经提供所需信息时不要调用；尚未先向用户询问时不要调用；"
            "缺失信息只是可选信息、不影响任务继续时不要调用；问候、能力介绍、简单路由或闲聊时不要调用；"
            "用户拒绝提供该信息、要求不要访问记忆或查询公共参考数据时不要调用。"
            "查询无结果后不要更换近义词反复尝试，应回到用户询问。",
            memory.do_not_use_when,
        )
        self.assertEqual(ConfirmationMode.NEVER, memory.policy.confirmation)

        edit = self.by_name["workspace_edit"]
        self.assertIn("workspace_read", edit.use_when)
        self.assertIn("revision", edit.schema.properties)
        self.assertIs(dict, edit.schema.properties["edits"].items)

        choices = self.by_name["provide_choices"]
        self.assertIs(str, choices.schema.properties["choices"].items)

    def test_handoff_tools_require_directional_context_envelopes(self) -> None:
        to_subagent = self.by_name["switch_to_subagent"]
        to_main = self.by_name["switch_to_mainagent"]

        self.assertIn("目标 Agent 先依据HandoffContext向用户确认交接内容", to_subagent.purpose)
        self.assertIn("等待用户回复后才继续行动", to_main.purpose)
        self.assertEqual(
            "必须使用kind=\"delegate\"的完整<HandoffContext> envelope；source=\"main\"，"
            "target为目标Agent，status=\"pending_confirmation\"。分别填写OriginalUserRequest、"
            "ConfirmedInformation、InferredInformation、CompletedWork和PendingUserDecision，"
            "没有内容写“无”。使用中性摘要，不得用“请执行”等命令式措辞暗示用户已授权具体动作。",
            to_subagent.schema.properties["context"].description,
        )
        self.assertEqual(
            "必须使用kind=\"return\"的完整<HandoffContext> envelope；source为当前子Agent，"
            "target=\"main\"，status为completed、blocked或user_exit。分别填写OriginalUserRequest、"
            "ConfirmedInformation、InferredInformation、CompletedWork和PendingUserDecision，"
            "没有内容写“无”。使用中性总结，不得用命令式措辞暗示主Agent已获授权继续执行。",
            to_main.schema.properties["summary"].description,
        )
        self.assertEqual(ConfirmationMode.ALWAYS, to_subagent.policy.confirmation)
        self.assertEqual(ConfirmationMode.ALWAYS, to_main.policy.confirmation)

    def test_catalog_export_keeps_runtime_policy_separate_from_prompt_guidance(self) -> None:
        catalog = ToolCatalog(self.definitions)
        descriptor = next(
            item
            for item in catalog.export_descriptors()
            if item["name"] == "workspace_write"
        )

        self.assertIn("新建文件", descriptor["use_when"])
        self.assertEqual("always", descriptor["confirmation"])


class ToolExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken())

    def test_validates_arguments_before_running_handler(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("echo"),)))

        outcome = executor.execute("call", "echo", {}, self.context)

        self.assertIsInstance(outcome, ToolFailure)
        self.assertEqual("missing_argument", outcome.code)

    def test_ignores_unknown_arguments_like_v1(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("echo"),)))

        outcome = executor.execute(
            "call",
            "echo",
            {"text": "x", "thinking": "model summary"},
            self.context,
        )

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual({"echo": "x"}, outcome.output)

    def test_requires_explicit_approval(self) -> None:
        executor = ToolExecutor(ToolCatalog((_tool("delete", confirmation=ConfirmationMode.ALWAYS),)))

        outcome = executor.execute("call", "delete", {"text": "x"}, self.context)

        self.assertIsInstance(outcome, ToolApproval)
        self.assertEqual("delete", outcome.tool_name)

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
            purpose="inspect context",
            use_when="when needed",
            do_not_use_when="otherwise",
            expected_output="captured context",
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

    def test_nullable_optional_argument_reaches_handler(self) -> None:
        definition = ToolDefinition(
            name="optional_filter",
            purpose="inspect an optional filter",
            use_when="a filter may be supplied",
            do_not_use_when="otherwise",
            expected_output="the supplied filter",
            schema=ToolSchema(
                {
                    "filter": ToolParameter(
                        str,
                        "optional filter",
                        default=None,
                        nullable=True,
                    )
                }
            ),
            policy=ToolPolicy(),
            handler=lambda arguments, context: ToolSuccess(arguments["filter"]),
        )
        executor = ToolExecutor(ToolCatalog((definition,)))

        outcome = executor.execute(
            "call",
            "optional_filter",
            {"filter": None},
            self.context,
        )

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertIsNone(outcome.output)

    def test_allowed_values_and_list_items_are_checked_before_handlers(self) -> None:
        seen: list[object] = []
        definition = ToolDefinition(
            name="schema_boundary",
            purpose="validate schema boundaries",
            use_when="testing",
            do_not_use_when="otherwise",
            expected_output="validated arguments",
            schema=ToolSchema(
                {
                    "mode": ToolParameter(str, "mode", allowed_values=("safe", "fast")),
                    "items": ToolParameter(list, "items", items=str),
                },
                frozenset({"mode", "items"}),
            ),
            policy=ToolPolicy(),
            handler=lambda arguments, context: seen.append(arguments) or ToolSuccess(arguments),
        )
        executor = ToolExecutor(ToolCatalog((definition,)))

        invalid_value = executor.execute(
            "value", "schema_boundary", {"mode": "unsafe", "items": ["ok"]}, self.context
        )
        invalid_item = executor.execute(
            "item", "schema_boundary", {"mode": "safe", "items": ["ok", 1]}, self.context
        )
        values = ["ok"]
        valid = executor.execute(
            "valid", "schema_boundary", {"mode": "safe", "items": values, "unknown": "ignored"}, self.context
        )

        self.assertEqual("invalid_argument_value", invalid_value.code)
        self.assertEqual("invalid_argument_item_type", invalid_item.code)
        self.assertIsInstance(valid, ToolSuccess)
        self.assertIs(values, seen[0]["items"])
        self.assertEqual({"mode", "items"}, set(seen[0]))

    def test_production_schema_boundaries_reject_invalid_values_before_handlers(self) -> None:
        approved = ToolContext("session", AgentKey.MAIN, CancellationToken(), approved=True)
        resume = ToolExecutor(ToolCatalog(build_resume_tools()))
        choices = ToolExecutor(ToolCatalog(build_switch_tools()))
        workspace = ToolExecutor(ToolCatalog(build_workspace_tools(100, 50, 50)))

        invalid_template = resume.execute(
            "template", "copy_template", {"template": "invalid", "prefix": "resume"}, approved
        )
        invalid_choices = choices.execute(
            "choices", "provide_choices", {"question": "pick", "choices": [1]}, self.context
        )
        invalid_edits = workspace.execute(
            "edits",
            "workspace_edit",
            {"path": "file.txt", "revision": "rev", "edits": ["invalid"]},
            approved,
        )

        self.assertEqual("invalid_argument_value", invalid_template.code)
        self.assertEqual("invalid_argument_item_type", invalid_choices.code)
        self.assertEqual("invalid_argument_item_type", invalid_edits.code)


def _tool(
    name: str,
    *,
    capabilities: frozenset[Capability] = frozenset(),
    confirmation: ConfirmationMode = ConfirmationMode.NEVER,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        purpose=name,
        use_when="when needed",
        do_not_use_when="otherwise",
        expected_output="typed output",
        schema=ToolSchema(
            properties={"text": ToolParameter(str, "text to echo")},
            required=frozenset({"text"}),
        ),
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
