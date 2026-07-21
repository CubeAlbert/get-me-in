import tempfile
import unittest
from pathlib import Path

from src.get_me_in.application.prompt_renderer import (
    PromptRenderer,
    UnexpectedPromptVariableError,
)
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability


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
        capabilities=frozenset({Capability.ROUTE}),
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
