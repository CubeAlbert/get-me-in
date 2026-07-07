"""App → Agent 输入协议 — 对称于 ``Response``，不进对话历史。

用法:
    from src.request import Request, RequestType

    # 用户输入
    Request(type=RequestType.USER_INPUT, message="你好")

    # PROGRESS 后自动继续
    Request(type=RequestType.CONTINUE)

    # 用户确认了工具执行
    Request(type=RequestType.CONFIRM_APPROVED)
"""

from dataclasses import dataclass
from enum import StrEnum


class RequestType(StrEnum):
    """App → Agent 请求类型。"""

    USER_INPUT = "user_input"
    """用户输入了文本，``message`` 为输入内容。"""

    CONTINUE = "continue"
    """PROGRESS 后自动继续执行。``message`` 为空。"""

    CONFIRM_APPROVED = "confirm_approved"
    """用户确认了工具执行。``message`` 为空。"""


@dataclass
class Request:
    """App → Agent 指令，告诉 Agent 本轮要做什么。

    ``Request`` 是 App ↔ Agent 交互层，**不进对话历史**。

    Attributes:
        type: 请求类型。
        message: 用户输入文本，仅 ``USER_INPUT`` 时填写，其余为空。
    """

    type: RequestType
    message: str = ""
