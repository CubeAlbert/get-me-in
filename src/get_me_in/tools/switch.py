"""Typed handoff and user-selection tool definitions."""

from collections.abc import Mapping

from src.get_me_in.domain.agents import AgentKey, Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandoff, ToolInteraction, ToolPolicy, ToolSchema


def build_switch_tools() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition("switch_to_subagent", "将任务交给指定子 Agent。", ToolSchema({"agent_name": str, "context": str}, frozenset({"agent_name"})), ToolPolicy(frozenset({Capability.ROUTE}), ConfirmationMode.ALWAYS), _to_subagent),
        ToolDefinition("switch_to_mainagent", "携带总结退回主 Agent。", ToolSchema({"summary": str}, frozenset({"summary"})), ToolPolicy(frozenset({Capability.RETURN_TO_MAIN}), ConfirmationMode.ALWAYS), _to_mainagent),
        ToolDefinition("provide_choices", "请求用户从多个选项中选择。", ToolSchema({"question": str, "choices": list}, frozenset({"question", "choices"})), ToolPolicy(frozenset({Capability.INTERACTION})), _choices),
    )


def _to_subagent(arguments: Mapping[str, object], context: object) -> ToolHandoff | ToolFailure:
    if getattr(context, "agent_key") is not AgentKey.MAIN:
        return ToolFailure("handoff_forbidden", "Only the main agent can delegate to a subagent")
    try:
        target = AgentKey(arguments["agent_name"])
    except ValueError:
        return ToolFailure("unknown_agent", f"Unknown agent: {arguments['agent_name']}")
    if target is AgentKey.MAIN:
        return ToolFailure("invalid_handoff", "Use a subagent as the target")
    return ToolHandoff(target, arguments.get("context", ""))


def _to_mainagent(arguments: Mapping[str, object], context: object) -> ToolHandoff | ToolFailure:
    if getattr(context, "agent_key") is AgentKey.MAIN:
        return ToolFailure("invalid_handoff", "Main agent cannot hand off to itself")
    return ToolHandoff(AgentKey.MAIN, arguments["summary"])


def _choices(arguments: Mapping[str, object], context: object) -> ToolInteraction:
    del context
    return ToolInteraction("selection", arguments["question"], tuple(arguments["choices"]))
