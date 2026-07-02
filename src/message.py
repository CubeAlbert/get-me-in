"""通用消息 / 事件数据类 — 统一覆盖用户输入、系统指令、工具调用、工具结果和 LLM 回复。

所有模块（CLI、Agent、LLM、Memory）共用此数据结构。

用法:
    from src.message import Message

    msg = Message(message="你好", event_type="user_input", role="user")
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """对话中的一条消息 / 事件。

    Attributes:
        message: 展示文本 — 终端显示给用户的内容。
        event_type: 事件类型标识（如 ``"user_input"``、``"tool_call"``、``"finish"`` 等）。
        role: 发送者角色：``"user"`` / ``"assistant"`` / ``"system"``。默认 ``"user"``。
        timestamp: 消息时间戳，默认当前时间。
        id: uuid4 hex 字符串，消息唯一标识。
        event_payload: 结构化载荷（工具名、参数、结果等），无载荷时为 ``None``。
        thinking: LLM 内部推理过程；role 为 ``"user"`` 时恒为 ``None``。
    """

    message: str
    event_type: str
    role: str = "user"
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_payload: dict | None = None
    thinking: str | None = None
