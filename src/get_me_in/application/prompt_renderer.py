"""Rendering of static agent prompt templates."""

import re
import json
from collections.abc import Iterable
from pathlib import Path

from src.get_me_in.application.localization import Locale, prompt_language_name
from src.get_me_in.domain.agents import AgentDescriptor, AgentSpec, Capability
from src.get_me_in.domain.tools import ToolDefinition, ToolParameter


_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


class PromptTemplateError(ValueError):
    """Base class for prompt-template contract errors."""


class MissingPromptVariableError(PromptTemplateError):
    """A template references a variable with no supplied value."""


class UnexpectedPromptVariableError(PromptTemplateError):
    """A template contains a variable outside the supported prompt contract."""


class PromptRenderer:
    """Render deterministic templates in filename order."""

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
            "RESPONSE_LANGUAGE",
        }
    )

    def __init__(
        self,
        prompts_dir: Path,
        *,
        response_locale: Locale = Locale.ZH_CN,
    ) -> None:
        self._general_agent_dir = prompts_dir / "general_agent"
        self._response_language = prompt_language_name(response_locale)

    def render(
        self,
        spec: AgentSpec,
        *,
        tools: Iterable[ToolDefinition] = (),
        agents: Iterable[AgentDescriptor] = (),
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
            "ADDITION_TOOLS": self._render_tools(tools),
            "SUB_AGENTS_LIST": self._render_agents(spec, agents),
            "TONE": spec.style.tone,
            "VERBOSITY": spec.style.verbosity,
            "EXPLANATION_STYLE": spec.style.explanation_style,
            "STYLE_RULES": "\n".join(spec.style.rules),
            "STYLE_AVOIDS": "\n".join(spec.style.avoids),
            "RESPONSE_LANGUAGE": self._response_language,
        }
        missing = placeholders - values.keys()
        if missing:
            raise MissingPromptVariableError(
                f"Missing prompt variables: {', '.join(sorted(missing))}"
            )
        return _PLACEHOLDER_RE.sub(lambda match: values[match.group(1)], template)

    def render_output_format(self) -> str:
        """Return the canonical model-output contract used for format repair."""
        paths = tuple(sorted(self._general_agent_dir.glob("*_output_format.md")))
        if not paths:
            raise FileNotFoundError(
                f"Output format template not found in {self._general_agent_dir}"
            )
        if len(paths) != 1:
            raise PromptTemplateError(
                f"Expected exactly one output format template, found {len(paths)}"
            )
        return paths[0].read_text(encoding="utf-8")

    @staticmethod
    def _render_tools(tools: Iterable[ToolDefinition]) -> str:
        return "\n\n".join(PromptRenderer._render_tool(tool) for tool in tools)

    @staticmethod
    def _render_tool(tool: ToolDefinition) -> str:
        arguments = {
            name: PromptRenderer._render_parameter(
                parameter,
                required=name in tool.schema.required,
            )
            for name, parameter in tool.schema.properties.items()
        }
        rendered_arguments = json.dumps(arguments, ensure_ascii=False, indent=2)
        return (
            f'<Tool name="{tool.name}">\n'
            f"<Purpose>{tool.purpose}</Purpose>\n"
            f"<UseWhen>{tool.use_when}</UseWhen>\n"
            f"<DoNotUseWhen>{tool.do_not_use_when}</DoNotUseWhen>\n"
            "<Arguments>\n"
            f"{rendered_arguments}\n"
            "</Arguments>\n"
            f"<ExpectedOutput>{tool.expected_output}</ExpectedOutput>\n"
            "</Tool>"
        )

    @staticmethod
    def _render_parameter(
        parameter: ToolParameter,
        *,
        required: bool,
    ) -> dict[str, object]:
        value_type = PromptRenderer._json_type(parameter.value_type)
        if parameter.nullable:
            value_type = f"{value_type}|null"
        rendered: dict[str, object] = {
            "description": parameter.description,
            "type": value_type,
            "required": required,
        }
        if parameter.items is not None:
            rendered["items"] = {"type": PromptRenderer._json_type(parameter.items)}
        if parameter.has_default:
            rendered["default"] = parameter.default
        if parameter.allowed_values:
            rendered["enum"] = parameter.allowed_values
        return rendered

    @staticmethod
    def _json_type(value_type: type) -> str:
        return {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }.get(value_type, "object")

    @staticmethod
    def _render_agents(spec: AgentSpec, agents: Iterable[AgentDescriptor]) -> str:
        if Capability.ROUTE not in spec.capabilities:
            return ""
        return "\n\n".join(
            PromptRenderer._render_agent(agent)
            for agent in agents
            if agent.key is not spec.key
        )

    @staticmethod
    def _render_agent(agent: AgentDescriptor) -> str:
        responsibilities = "\n".join(agent.responsibilities)
        hard_constraints = "\n".join(agent.hard_constraints)
        return (
            f'<SubAgent name="{agent.key.value}">\n'
            f"<Name>{agent.display_name}</Name>\n"
            f"<Description>{agent.description}</Description>\n"
            f"<Responsibilities>{responsibilities}</Responsibilities>\n"
            f"<HardConstraints>{hard_constraints}</HardConstraints>\n"
            "</SubAgent>"
        )
