"""Agent 切换工具 — switch_to_subagent / switch_to_mainagent。

审批由 ``BaseAgent._execute_tool()`` 根据 ``ConfirmMode`` 统一处理（通过 UIBridge 弹窗）。
Handler 返回 ``{"__switch__": True, ...}`` 或 ``{"__reject__": True, ...}`` sentinel。
"""

from src.agents.registry import MAIN_AGENT_KEY
from src.cli.uibridge import get_bridge
from src.tools.registry import ConfirmMode, tool


@tool(
    purpose="将用户切换至指定的专业子Agent处理其请求。切换后子Agent会接管对话，你无法再看到中间过程，仅在子Agent返回总结时恢复控制。",
    use_when="用户的请求属于某个子Agent的职责范围，需要由专业Agent接手处理。参考 <SubAgents> 列表选择合适的子Agent。",
    do_not_use_when="你自己可以处理、用户请求不属于任何子Agent的职责范围、或无法确定用户意图时。不确定时必须先向用户提问澄清。",
    expected_output="切换至子Agent，等待子Agent返回总结后恢复控制。",
    input_schema={
        "agent_name": {"description": "目标子Agent名称，必须与 <SubAgents> 中 SubAgent 的 name 属性一致"},
        "context": {"description": "给子Agent的完整上下文：用户需求、背景、已收集的关键信息等。越详细越好。"},
    },
    agent=[MAIN_AGENT_KEY],
    confirm_mode=ConfirmMode.ALWAYS,
)
def switch_to_subagent(agent_name: str, context: str = "") -> dict:
    """切换到子 Agent。

    Args:
        agent_name: 目标子Agent名称（对应 <SubAgents> 列表中 SubAgent 的 name 属性）。
        context: 给子Agent的完整上下文，包含用户需求、背景、已收集的关键信息。
    """
    return {"__switch__": True, "target": agent_name, "context": context}


@tool(
    purpose="结束当前子Agent会话，携带执行总结退回主Agent。调用此工具后主Agent会收到你的总结并继续为用户服务。",
    use_when="已完成用户请求的任务、用户明确表示要退出、或遇到无法处理的情况需要主Agent重新接手。",
    do_not_use_when="任务尚未完成且用户未要求退出。",
    expected_output="退回主Agent，主Agent收到你的总结后继续决策。",
    input_schema={
        "summary": {"description": "本次子Agent会话的执行总结：做了什么、结论、关键发现、需要主Agent继续跟进的事项。"},
    },
    agent=["*"],
    confirm_mode=ConfirmMode.ALWAYS,
)
def switch_to_mainagent(summary: str) -> dict:
    """退回主 Agent。

    Args:
        summary: 本次子Agent会话的执行总结，包含做了什么、结论、关键发现、
                 以及需要主Agent继续跟进的事项。
    """
    return {"__switch__": True, "target": MAIN_AGENT_KEY, "context": summary}


@tool(
    purpose="向用户列出选项并等待选择。用户可能从选项中选择，也可能提出自己的想法（UI 层自动提供自定义输入入口，你无需在 choices 中添加"其他"选项），你需要尊重用户的选择并据此调整后续行动。",
    use_when="用户的请求有多种可能的处理方式、你需要用户做出明确选择时。",
    do_not_use_when="用户意图已经明确、只有一个合理的选项、或用户已经明确指定了方向。",
    expected_output="用户选中的选项文本，作为 tool_call_result 返回。",
    input_schema={
        "question": {"description": "向用户展示的问题/提示文本"},
        "choices": {"description": "选项列表，每个选项描述一个可选的行动方向。无需添加"其他"/"自定义"选项，UI 已自动处理"},
    },
    agent=None,
    confirm_mode=ConfirmMode.NEVER,
)
def provide_choices(question: str, choices: list[str]) -> dict:
    """向用户列出选项并等待选择。

    Args:
        question: 向用户展示的问题/提示文本。
        choices: 选项列表，每个选项描述一个可选的行动方向。

    Returns:
        dict with "selected" key containing the user's choice.
    """
    ui = get_bridge()
    selected = ui.select(question, choices)
    return {"selected": selected}
