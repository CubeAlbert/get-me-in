import json
import tempfile
import unittest
from pathlib import Path

from src.get_me_in.application.prompt_renderer import (
    PromptRenderer,
    UnexpectedPromptVariableError,
)
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
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
    def test_renders_sorted_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "02.md").write_text("{{AGENT_NAME}}", encoding="utf-8")
            (root / "01.md").write_text("{{PRIMARY_GOAL}}", encoding="utf-8")

            rendered = PromptRenderer(root.parent).render(_spec())

        self.assertEqual("目标\n主 Agent", rendered)

    def test_rejects_unsupported_template_variable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01.md").write_text("{{UNKNOWN}}", encoding="utf-8")

            with self.assertRaises(UnexpectedPromptVariableError):
                PromptRenderer(root.parent).render(_spec())

    def test_renders_priorities_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "01.md").write_text("{{PRIORITIES}}", encoding="utf-8")

            rendered = PromptRenderer(root.parent).render(_spec())

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

            rendered = PromptRenderer(root.parent).render(_spec(), tools=(visible,))

        tool = json.loads(rendered.splitlines()[0])
        self.assertEqual("clock", tool["name"])
        self.assertEqual("Get accurate time", tool["purpose"])
        self.assertEqual("The current time is needed", tool["use_when"])
        self.assertEqual(
            "The request is unrelated to time",
            tool["do_not_use_when"],
        )
        self.assertEqual("ISO timestamp", tool["expected_output"])
        self.assertEqual(
            {
                "type": "string",
                "description": "IANA timezone name",
                "default": "UTC",
                "allowed_values": ["UTC", "Asia/Shanghai"],
            },
            tool["input_schema"]["properties"]["timezone"],
        )
        self.assertEqual(
            {"type": "string"},
            tool["input_schema"]["properties"]["labels"]["items"],
        )
        self.assertNotIn("workspace_write", rendered)

    def test_reads_canonical_output_format_for_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "07_output_format.md").write_text(
                "<OutputFormat>canonical</OutputFormat>", encoding="utf-8"
            )

            rendered = PromptRenderer(root.parent).render_output_format()

        self.assertEqual("<OutputFormat>canonical</OutputFormat>", rendered)
