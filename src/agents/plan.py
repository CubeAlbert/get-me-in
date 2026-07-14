"""Plan 机制数据模型 — 通用基础设施，BaseAgent 层共用。

Plan 让 Agent 能将复杂任务分解为有序步骤，LLM 通过工具创建/更新/取消计划项，
App 层渲染计划进度供用户查看。
"""

from dataclasses import dataclass, field
from enum import StrEnum


class PlanStatus(StrEnum):
    """计划项状态。"""

    PENDING = "pending"          # 待执行
    IN_PROGRESS = "in_progress"  # 当前正在执行（同时只有一个）
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消


@dataclass
class PlanItem:
    """单个计划步骤。

    Attributes:
        id: uuid hex 字符串，唯一标识。
        description: 步骤的简短描述。
        status: 当前状态。
        order: 执行顺序，从 0 开始递增。
    """

    id: str
    description: str
    status: PlanStatus
    order: int
