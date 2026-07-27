"""Typed handoff and user-selection tool definitions."""

from collections.abc import Mapping

from src.get_me_in.domain.agents import AgentKey, Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandoff, ToolInteraction, ToolParameter, ToolPolicy, ToolSchema


def build_switch_tools() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition(
            name="switch_to_subagent",
            purpose="将用户切换至指定的专业子 Agent 处理其请求。切换后子 Agent 会接管对话，你无法再看到中间过程，仅在子 Agent 返回总结时恢复控制。",
            use_when="用户的请求属于某个子 Agent 的职责范围，需要由专业 Agent 接手处理。参考 <SubAgents> 列表选择合适的子 Agent。",
            do_not_use_when="你自己可以处理、用户请求不属于任何子 Agent 的职责范围、或无法确定用户意图时。不确定时必须先向用户提问澄清。",
            expected_output="切换至子 Agent，等待子 Agent 返回总结后恢复控制。",
            schema=ToolSchema(
                {
                    "agent_name": ToolParameter(
                        str,
                        "目标子 Agent key，必须与 <SubAgents> 中的 key 一致",
                    ),
                    "context": ToolParameter(
                        str,
                        "给子 Agent 的完整上下文：用户需求、背景、已收集的关键信息等。越详细越好。",
                        default="",
                    ),
                },
                frozenset({"agent_name"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.ROUTE}),
                ConfirmationMode.ALWAYS,
            ),
            handler=_to_subagent,
        ),
        ToolDefinition(
            name="switch_to_mainagent",
            purpose="结束当前子 Agent 会话，携带执行总结退回主 Agent。调用此工具后主 Agent 会收到你的总结并继续为用户服务。",
            use_when="已完成用户请求的任务、用户明确表示要退出、或遇到无法处理的情况需要主 Agent 重新接手。",
            do_not_use_when="任务尚未完成且用户未要求退出。",
            expected_output="退回主 Agent，主 Agent 收到你的总结后继续决策。",
            schema=ToolSchema(
                {
                    "summary": ToolParameter(
                        str,
                        "本次子 Agent 会话的执行总结：做了什么、结论、关键发现、需要主 Agent 继续跟进的事项。",
                    )
                },
                frozenset({"summary"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.RETURN_TO_MAIN}),
                ConfirmationMode.ALWAYS,
            ),
            handler=_to_mainagent,
        ),
        ToolDefinition(
            name="provide_choices",
            purpose="向用户列出选项并等待选择。用户可能从选项中选择，也可能提出自己的想法（UI 层自动提供自定义输入入口，你无需在 choices 中添加「其他」选项），你需要尊重用户的选择并据此调整后续行动。",
            use_when="用户的请求有多种可能的处理方式、你需要用户做出明确选择时。",
            do_not_use_when="用户意图已经明确、只有一个合理的选项、或用户已经明确指定了方向。",
            expected_output="用户选中的选项文本，作为 tool_call_result 返回。",
            schema=ToolSchema(
                {
                    "question": ToolParameter(str, "向用户展示的问题/提示文本"),
                    "choices": ToolParameter(
                        list,
                        "选项列表，每个选项描述一个可选的行动方向。无需添加「其他」/「自定义」选项，UI 已自动处理",
                        items=str,
                    ),
                },
                frozenset({"question", "choices"}),
            ),
            policy=ToolPolicy(frozenset({Capability.INTERACTION})),
            handler=_choices,
        ),
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
