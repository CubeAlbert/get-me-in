import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.get_me_in.application.prompt_renderer import (
    PromptRenderer,
    UnexpectedPromptVariableError,
)
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
    def test_renders_sorted_templates_with_output_format_last(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir) / "general_agent"
            root.mkdir()
            (root / "02.md").write_text("{{AGENT_NAME}}", encoding="utf-8")
            (root / "01.md").write_text("{{PRIMARY_GOAL}}", encoding="utf-8")
            (root / "07_output_format.md").write_text("output", encoding="utf-8")
            (root / "08_input_format.md").write_text("input", encoding="utf-8")
            (root / "09_reserved.md").write_text("reserved", encoding="utf-8")

            rendered = PromptRenderer(root.parent).render(_spec())

        self.assertEqual("目标\n主 Agent\ninput\nreserved\noutput", rendered)

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

            rendered = PromptRenderer(root.parent).render(
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
            (root / "07_output_format.md").write_text(
                "<OutputFormat>canonical</OutputFormat>", encoding="utf-8"
            )

            rendered = PromptRenderer(root.parent).render_output_format()

        self.assertEqual("<OutputFormat>canonical</OutputFormat>", rendered)

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
            renderer = PromptRenderer(root.parent)

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
