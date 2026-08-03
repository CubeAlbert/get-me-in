import json
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.get_me_in.application.prompt_renderer import (
    PromptRenderer,
    UnexpectedPromptVariableError,
)
from src.get_me_in.application.localization import Locale
from src.get_me_in.domain.agents import (
    AgentDescriptor,
    AgentKey,
    AgentSpec,
    AgentStyle,
    Capability,
)
from src.get_me_in.domain.tools import (
    ToolDefinition,
    ToolParameter,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)


def _spec() -> AgentSpec:
    return AgentSpec(
        key=AgentKey.MAIN,
        display_name="主 Agent",
        description="描述",
        responsibilities=("职责",),
        primary_goal="目标",
        success_criteria=("标准",),
        hard_constraints=("约束",),
        soft_constraints=(),
        style=AgentStyle("专业", "简洁", "直接"),
        model_profile="pro",
        temperature=0.1,
        capabilities=frozenset({Capability.ROUTE}),
        priorities=("优先级",),
    )


class PromptRendererTests(unittest.TestCase):
    def test_renders_templates_in_filename_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "02.md").write_text("{{AGENT_NAME}}", encoding="utf-8")
            (root / "01.md").write_text("{{PRIMARY_GOAL}}", encoding="utf-8")
            (root / "08_input_format.md").write_text("input", encoding="utf-8")
            (root / "09_output_format.md").write_text("output", encoding="utf-8")
            (root / "10_reserved.md").write_text("reserved", encoding="utf-8")

            rendered = PromptRenderer(
                root.parent,
                response_locale=Locale.ZH_CN,
            ).render(_spec())

        self.assertEqual("目标\n主 Agent\ninput\noutput\nreserved", rendered)

    def test_production_templates_follow_their_numeric_filenames(self) -> None:
        rendered = PromptRenderer(
            Path("data/prompts"),
            response_locale=Locale.ZH_CN,
        ).render(_spec())

        self.assertEqual(
            (
                "01_role.md",
                "02_mission.md",
                "03_constraint.md",
                "04_tools.md",
                "05_sub_agents.md",
                "06_communtion_style.md",
                "07_response_language.md",
                "08_input_format.md",
                "09_output_format.md",
                "10_reserved.md",
            ),
            tuple(
                path.name
                for path in sorted(Path("data/prompts/general_agent").glob("*.md"))
            ),
        )

        sections = (
            "<Role>",
            "<Mission>",
            "<Constraints>",
            "<Tools>",
            "<HandoffContextContract>",
            "\n<SubAgents>\n",
            "<CommunicationStyle>",
            "<ResponseLanguage>",
            "<InputFormat>",
            "<OutputFormat>",
            "<Reserved>",
        )
        positions = tuple(rendered.index(section) for section in sections)

        self.assertEqual(tuple(sorted(positions)), positions)
        self.assertEqual(1, rendered.count("<ResponseLanguage>"))
        self.assertIn("zh-CN", rendered)

    def test_injects_explicit_response_locale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01_response.md").write_text(
                "<ResponseLanguage>{{RESPONSE_LANGUAGE}}</ResponseLanguage>",
                encoding="utf-8",
            )

            rendered = PromptRenderer(
                root.parent,
                response_locale=Locale.EN_US,
            ).render(_spec())

        self.assertEqual(
            "<ResponseLanguage>English (en-US)</ResponseLanguage>",
            rendered,
        )

    def test_production_handoff_context_contract_is_directional_and_turn_based(self) -> None:
        rendered = PromptRenderer(
            Path("data/prompts"),
            response_locale=Locale.ZH_CN,
        ).render(_spec())

        self.assertEqual(1, rendered.count("<HandoffContextContract>"))
        self.assertIn(
            '<HandoffContext kind="delegate|return" source="agent-key" '
            'target="agent-key" status="pending_confirmation|completed|blocked|user_exit">',
            rendered,
        )
        for field in (
            "OriginalUserRequest",
            "ConfirmedInformation",
            "InferredInformation",
            "CompletedWork",
            "PendingUserDecision",
        ):
            self.assertIn(f"<{field}>", rendered)
        self.assertIn(
            "无论该 Agent 是否首次运行、是否已有 history",
            rendered,
        )
        self.assertIn("handoff 接收回合不得调用任何工具", rendered)
        self.assertIn('kind="delegate" 时，只复述', rendered)
        self.assertIn('kind="return" 时，只向用户汇报', rendered)

    def test_input_format_is_the_locked_history_projection(self) -> None:
        input_format = Path("data/prompts/general_agent/08_input_format.md")

        self.assertEqual(
            "0917629fa08e67910501debccda4747706ace7c8e6ea7e6ee08804aa94e01d81",
            hashlib.sha256(input_format.read_bytes()).hexdigest(),
        )
        source = input_format.read_text(encoding="utf-8")
        self.assertIn('"event_type"', source)
        self.assertIn('"tool_call_id"', source)
        self.assertIn('"event_payload"', source)
        self.assertIn('"plan_status"', source)
        self.assertNotIn('"thinking"', source)

    def test_rejects_unsupported_template_variable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01.md").write_text("{{UNKNOWN}}", encoding="utf-8")

            with self.assertRaises(UnexpectedPromptVariableError):
                PromptRenderer(
                    root.parent,
                    response_locale=Locale.ZH_CN,
                ).render(_spec())

    def test_renders_priorities_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01.md").write_text("{{PRIORITIES}}", encoding="utf-8")

            rendered = PromptRenderer(
                root.parent,
                response_locale=Locale.ZH_CN,
            ).render(_spec())

        self.assertEqual("优先级", rendered)

    def test_renders_only_supplied_catalog_descriptors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01.md").write_text(
                "{{ADDITION_TOOLS}}\n{{SUB_AGENTS_LIST}}", encoding="utf-8"
            )
            visible = ToolDefinition(
                name="clock",
                purpose="Get accurate time",
                use_when="The current time is needed",
                do_not_use_when="The request is unrelated to time",
                expected_output="ISO timestamp",
                schema=ToolSchema(
                    {
                        "timezone": ToolParameter(
                            str,
                            "IANA timezone name",
                            default="UTC",
                            allowed_values=("UTC", "Asia/Shanghai"),
                        ),
                        "labels": ToolParameter(
                            list,
                            "Labels to include",
                            items=str,
                        ),
                    }
                ),
                policy=ToolPolicy(),
                handler=lambda arguments, context: ToolSuccess("ok"),
            )
            second = ToolDefinition(
                name="calendar",
                purpose="Get a calendar",
                use_when="A calendar is needed",
                do_not_use_when="The request is unrelated to dates",
                expected_output="Calendar data",
                schema=ToolSchema({}),
                policy=ToolPolicy(),
                handler=lambda arguments, context: ToolSuccess("ok"),
            )

            rendered = PromptRenderer(
                root.parent,
                response_locale=Locale.ZH_CN,
            ).render(
                _spec(),
                tools=(visible, second),
            )

        expected_sections = (
            '<Tool name="clock">',
            "<Purpose>Get accurate time</Purpose>",
            "<UseWhen>The current time is needed</UseWhen>",
            "<DoNotUseWhen>The request is unrelated to time</DoNotUseWhen>",
            "<Arguments>",
            "<ExpectedOutput>ISO timestamp</ExpectedOutput>",
            "</Tool>",
        )
        positions = tuple(rendered.index(section) for section in expected_sections)
        self.assertEqual(tuple(sorted(positions)), positions)
        arguments_text = rendered.split("<Arguments>\n", 1)[1].split(
            "\n</Arguments>", 1
        )[0]
        arguments = json.loads(arguments_text)
        timezone_text = arguments_text.split('"timezone": {', 1)[1].split(
            "\n  },", 1
        )[0]
        parameter_fields = (
            '"description"',
            '"type"',
            '"required"',
            '"default"',
            '"enum"',
        )
        field_positions = tuple(
            timezone_text.index(field) for field in parameter_fields
        )
        self.assertEqual(tuple(sorted(field_positions)), field_positions)
        self.assertEqual(
            {
                "description": "IANA timezone name",
                "type": "string",
                "required": False,
                "default": "UTC",
                "enum": ["UTC", "Asia/Shanghai"],
            },
            arguments["timezone"],
        )
        self.assertEqual(
            {"type": "string"},
            arguments["labels"]["items"],
        )
        self.assertFalse(arguments["labels"]["required"])
        self.assertIn("</Tool>\n\n<Tool name=\"calendar\">", rendered)
        self.assertNotIn("workspace_write", rendered)

    def test_reads_canonical_output_format_for_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "42_output_format.md").write_text(
                "<OutputFormat>canonical</OutputFormat>", encoding="utf-8"
            )

            rendered = PromptRenderer(
                root.parent,
                response_locale=Locale.ZH_CN,
            ).render_output_format()

        self.assertEqual("<OutputFormat>canonical</OutputFormat>", rendered)

    def test_production_output_format_uses_flat_message_entity_projection(self) -> None:
        rendered = PromptRenderer(
            Path("data/prompts"),
            response_locale=Locale.ZH_CN,
        ).render_output_format()
        schema_text = rendered.split("<Schema>\n", 1)[1].split("\n</Schema>", 1)[0]
        schema = json.loads(schema_text)

        self.assertEqual(1, rendered.count("<Schema>"))
        self.assertNotIn("<FinishFormat>", rendered)
        self.assertNotIn("<ToolCallFormat>", rendered)
        self.assertEqual(
            ["finish", "tool_call"],
            schema["properties"]["event_type"]["enum"],
        )
        self.assertEqual(
            ["event_type", "message"],
            schema["required"],
        )
        self.assertEqual(1, schema["properties"]["message"]["minLength"])
        self.assertIn("可以使用 Markdown", schema["properties"]["message"]["description"])
        self.assertEqual("string", schema["properties"]["thinking"]["type"])
        self.assertIn("纯文本", schema["properties"]["thinking"]["description"])
        self.assertIn("不使用 Markdown", schema["properties"]["thinking"]["description"])
        payload_description = schema["properties"]["event_payload"]["description"]
        self.assertIn("tool_call 时为工具参数对象", payload_description)
        self.assertIn("参数名和类型必须匹配对应 Tool 的 Arguments", payload_description)
        self.assertNotIn("<InputOutputDistinction>", rendered)
        self.assertIn("无论 event_type 为 finish 还是 tool_call，都必须提供 message", rendered)
        self.assertIn("message 必须是非空、非纯空白字符串", rendered)
        self.assertIn("event_type=finish 时，必须提供 thinking", rendered)
        self.assertIn("thinking 必须是纯文本字符串，不使用 Markdown", rendered)
        self.assertNotIn("省略、null 或空白字符串仍合法", rendered)
        self.assertNotIn("Runtime 生成或重新投影", rendered)
        self.assertIn("无需提供 id、role、timestamp、tool_call_id 或 plan_status", rendered)
        self.assertIn("参数必须直接放入 event_payload", rendered)

    def test_renders_sub_agents_as_xml_only_for_routing_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01.md").write_text(
                "{{SUB_AGENTS_LIST}}",
                encoding="utf-8",
            )
            main = AgentDescriptor.from_spec(_spec())
            resume = AgentDescriptor(
                key=AgentKey.RESUME,
                display_name="Resume Agent",
                description="Tailors resumes",
                responsibilities=("Read the resume", "Build the PDF"),
                hard_constraints=("Stay in the workspace",),
            )
            job_search = AgentDescriptor(
                key=AgentKey.JOB_SEARCH,
                display_name="Job Search Agent",
                description="Searches for jobs",
                responsibilities=("Search current listings",),
                hard_constraints=("Use current sources",),
            )
            renderer = PromptRenderer(
                root.parent,
                response_locale=Locale.ZH_CN,
            )

            main_rendered = renderer.render(
                _spec(),
                agents=(main, resume, job_search),
            )
            resume_rendered = renderer.render(
                replace(
                    _spec(),
                    key=AgentKey.RESUME,
                    capabilities=frozenset(),
                ),
                agents=(main, resume, job_search),
            )

        expected_sections = (
            '<SubAgent name="resume">',
            "<Name>Resume Agent</Name>",
            "<Description>Tailors resumes</Description>",
            "<Responsibilities>Read the resume\nBuild the PDF</Responsibilities>",
            "<HardConstraints>Stay in the workspace</HardConstraints>",
            "</SubAgent>",
        )
        positions = tuple(
            main_rendered.index(section) for section in expected_sections
        )
        self.assertEqual(tuple(sorted(positions)), positions)
        self.assertIn(
            '</SubAgent>\n\n<SubAgent name="job_search">',
            main_rendered,
        )
        self.assertNotIn('<SubAgent name="main">', main_rendered)
        self.assertEqual("", resume_rendered)
