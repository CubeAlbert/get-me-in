"""Plan 机制工具 — 通用基础设施，所有 Agent 可用。

通过模块级 context variable 获取当前正在执行的 Agent 实例，
遵循与 UIBridge（``_set_bridge`` / ``get_bridge``）相同的模式。

用法::

    # 在 BaseAgent._execute_tool() 中自动设置
    from src.tools.plan_tools import _set_plan_agent
    _set_plan_agent(self)
    try:
        result = tool.handler(**filtered)
    finally:
        _set_plan_agent(None)

    # 工具 handler 中通过 _get_plan_agent() 访问 agent
    def create_plan(items: list[str]) -> dict:
        return _get_plan_agent()._create_plan(items)
"""

from typing import TYPE_CHECKING, Any

from src.tools.registry import ConfirmMode, tool

if TYPE_CHECKING:
    from src.agents.base import BaseAgent

# ── 模块级 context variable ────────────────────────────────────

_plan_agent: Any = None


def _set_plan_agent(agent: Any) -> None:
    """设置当前正在执行工具的 Agent 实例（由 BaseAgent._execute_tool 调用）。"""
    global _plan_agent
    _plan_agent = agent


def _get_plan_agent() -> Any:
    """获取当前 Agent 实例，仅在工具 handler 中有效。"""
    if _plan_agent is None:
        raise RuntimeError("_get_plan_agent() 只能在 plan 工具 handler 中调用")
    return _plan_agent


# ── Plan 工具 ──────────────────────────────────────────────────


@tool(
    purpose="创建一个结构化的执行计划，将复杂任务分解为有序步骤列表",
    use_when="满足以下任意情况：\n"
    "- 用户明确要求制定计划\n"
    "- 任务预计持续较长时间\n"
    "- 存在多个可以独立完成的子任务\n"
    "- 后续步骤可能因为前一步失败而调整\n"
    "- 用户需要持续看到执行进度",
    do_not_use_when="满足以下任意情况：\n"
    "- 任务只是一个连续的线性流程\n"
    "- 所有步骤都会连续执行且无需等待用户\n"
    "- 不需要跟踪执行状态\n"
    "- 不需要向用户展示进度\n"
    "- 预计可以一次回复完成",
    expected_output="返回创建后的完整计划状态，包括每个项的 id/描述/状态/顺序、当前激活项、下一项、是否全部完成",
    input_schema={
        "items": {
            "description": "计划项描述列表，每个字符串是一个步骤的简短描述",
        },
    },
    agent=None,
    confirm_mode=ConfirmMode.NEVER,
)
def create_plan(items: list[str]) -> dict:
    """创建新计划（覆盖旧计划），首项自动激活为 IN_PROGRESS。"""
    return _get_plan_agent()._create_plan(items)


@tool(
    purpose="更新指定计划项的状态：完成、取消，或将待执行项标记为进行中",
    use_when="当前步骤完成时标记为 completed；需要跳过某步骤时标记为 cancelled；需要回退重做时标记为 pending",
    do_not_use_when="计划不存在或所有项已完成时",
    expected_output="返回更新后的完整计划状态",
    input_schema={
        "id": {
            "description": "要更新的计划项 id",
        },
        "status": {
            "description": "新状态: pending / in_progress / completed / cancelled",
            "enum": ["pending", "in_progress", "completed", "cancelled"],
        },
    },
    agent=None,
    confirm_mode=ConfirmMode.NEVER,
)
def update_plan_status(id: str, status: str) -> dict:
    """更新指定计划项的状态。完成/取消当前项时自动激活下一项。"""
    return _get_plan_agent()._update_plan_status(id, status)


@tool(
    purpose="取消所有未完成的计划项，清空当前计划",
    use_when="用户明确要求取消当前计划，或计划已不再适用需要重新规划时",
    do_not_use_when="只想取消单个步骤时（应使用 update_plan_status）",
    expected_output="返回清空后的计划状态（plan=[]，all_completed=true）",
    input_schema={},
    agent=None,
    confirm_mode=ConfirmMode.NEVER,
)
def cancel_all_plans() -> dict:
    """取消所有未完成的计划项。"""
    return _get_plan_agent()._cancel_all_plans()
