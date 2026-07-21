"""Rendering of static agent prompt templates."""

import re
from pathlib import Path

from src.get_me_in.domain.agents import AgentSpec


_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


class PromptTemplateError(ValueError):
    """Base class for prompt-template contract errors."""


class MissingPromptVariableError(PromptTemplateError):
    """A template references a variable with no supplied value."""


class UnexpectedPromptVariableError(PromptTemplateError):
    """A template contains a variable outside the supported prompt contract."""


class PromptRenderer:
    """Renders sorted ``general_agent`` templates from an immutable AgentSpec."""

    _ALLOWED_VARIABLES = frozenset(
        {
            "AGENT_NAME",
            "AGENT_DESCRIPTION",
            "RESPONSIBILITIES",
            "PRIMARY_GOAL",
            "SUCCESS_CRITERIONS",
            "PRIORITIES",
            "HARD_CONSTRAINTS",
            "SOFT_CONSTRAINTS",
            "ADDITION_TOOLS",
            "SUB_AGENTS_LIST",
            "TONE",
            "VERBOSITY",
            "EXPLANATION_STYLE",
            "STYLE_RULES",
            "STYLE_AVOIDS",
        }
    )

    def __init__(self, prompts_dir: Path) -> None:
        self._general_agent_dir = prompts_dir / "general_agent"

    def render(
        self,
        spec: AgentSpec,
        *,
        addition_tools: str = "",
        sub_agents_list: str = "",
    ) -> str:
        files = sorted(self._general_agent_dir.glob("*.md"))
        if not files:
            raise FileNotFoundError(
                f"No prompt templates found in {self._general_agent_dir}"
            )
        template = "\n".join(path.read_text(encoding="utf-8") for path in files)
        placeholders = set(_PLACEHOLDER_RE.findall(template))
        unexpected = placeholders - self._ALLOWED_VARIABLES
        if unexpected:
            raise UnexpectedPromptVariableError(
                f"Unsupported prompt variables: {', '.join(sorted(unexpected))}"
            )

        values = {
            "AGENT_NAME": spec.display_name,
            "AGENT_DESCRIPTION": spec.description,
            "RESPONSIBILITIES": "\n".join(spec.responsibilities),
            "PRIMARY_GOAL": spec.primary_goal,
            "SUCCESS_CRITERIONS": "\n".join(spec.success_criteria),
            "PRIORITIES": "\n".join(spec.priorities),
            "HARD_CONSTRAINTS": "\n".join(spec.hard_constraints),
            "SOFT_CONSTRAINTS": "\n".join(spec.soft_constraints),
            "ADDITION_TOOLS": addition_tools,
            "SUB_AGENTS_LIST": sub_agents_list,
            "TONE": spec.style.tone,
            "VERBOSITY": spec.style.verbosity,
            "EXPLANATION_STYLE": spec.style.explanation_style,
            "STYLE_RULES": "\n".join(spec.style.rules),
            "STYLE_AVOIDS": "\n".join(spec.style.avoids),
        }
        missing = placeholders - values.keys()
        if missing:
            raise MissingPromptVariableError(
                f"Missing prompt variables: {', '.join(sorted(missing))}"
            )
        return _PLACEHOLDER_RE.sub(lambda match: values[match.group(1)], template)
