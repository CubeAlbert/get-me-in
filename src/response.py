"""CLI 指令层数据类 — Agent 通过 Response 向 App 下达渲染指令，不进对话历史。

用法:
    from src.response import Response, ResponseType

    # 正常结束
    Response(type=ResponseType.FINISH, message="任务完成")

    # 让用户选择
    Response(type=ResponseType.SELECT, message="请选择", choices=["选项A", "选项B"])

    # 请求审批
    Response(type=ResponseType.CONFIRM, message="即将执行删除操作")

    # 中间进度
    Response(type=ResponseType.PROGRESS, message="正在调用 get_current_datetime...")
"""

from dataclasses import dataclass
from enum import StrEnum


class ResponseType(StrEnum):
    """Response 指令类型。"""

    FINISH = "finish"  # 渲染 markdown，本轮结束
    SELECT = "select"  # 渲染 questionary.select
    CONFIRM = "confirm"  # 渲染 questionary.confirm
    PROGRESS = "progress"  # 中间进度，App 渲染后自动继续 agent loop


class ConfirmChoice(StrEnum):
    """App 层审批确认选项。"""
    APPROVE = "✅ 执行"
    REJECT = "❌ 取消"


@dataclass
class Response:
    """Agent → CLI 指令，告诉 App 如何渲染本轮结果。

    ``Response`` 是 CLI 指令层，**不进对话历史**。

    Attributes:
        type: 指令类型。
        message: 展示文本 (markdown)。
        sub_type: 对应 ``Message.event_type``，用于 App 判断继续/终止逻辑。
        choices: ``type=SELECT`` 时的选项列表，最后一项自动追加"🔧 自定义输入..."。
        thinking: LLM 推理过程，由 ``SHOW_THINKING`` 环境变量控制是否渲染。
    """

    type: ResponseType
    message: str
    sub_type: str = ""
    choices: list[str] | None = None
    thinking: str | None = None
    switch_agent: str | None = None
    switch_context: str | None = None
    switch_tool_call_id: str | None = None
