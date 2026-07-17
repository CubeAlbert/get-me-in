"""通用消息 / 事件数据类 — 统一覆盖用户输入、系统指令、工具调用、工具结果和 LLM 回复。

所有模块（CLI、Agent、LLM、Memory）共用此数据结构。

用法:
    from src.message import Message

    msg = Message(event_type=EventType.USER_INPUT, message="你好")
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
class Role(StrEnum):
    """消息发送者角色枚举。"""

    USER = "user"
    """用户消息。"""
    SYSTEM = "system"
    """系统指令 / 提示消息。"""
    ASSISTANT = "assistant"
    """LLM 回复消息。"""


class EventType(StrEnum):
    """消息事件类型枚举。"""

    USER_INPUT = "user_input"
    """用户输入。"""

    TOOL_CALL = "tool_call"
    """工具调用。"""

    TOOL_CALL_RESULT = "tool_call_result"
    """工具调用结果。"""

    FINISH = "finish"
    """当前没有工具需要调用，展示结果给用户。"""

    SYSTEM_MESSAGE = "system_message"
    """系统提示消息（一般用于错误恢复或异常处理）。"""


@dataclass
class Message:
    """对话中的一条消息 / 事件。

    Attributes:
        event_type: 事件类型标识，见 ``EventType`` 枚举。
        message: 展示文本 — 终端显示给用户的内容。默认 ``""``。
        id: uuid4 hex 字符串，消息唯一标识。
        role: 发送者角色：``"user"`` / ``"assistant"`` / ``"system"``。默认 ``"user"``。
        timestamp: 消息时间戳，默认当前时间。
        tool: 调用的工具名，未调用工具时为 ``None``。
        tool_call_id: 对应 ``tool_call`` 消息的 ``id``，仅 ``tool_call_result`` 时填写，其余为 ``None``。
        event_payload: 结构化载荷。``tool_call`` 时为工具参数；``tool_call_result`` 时为工具调用结果。无载荷时为 ``None``。
        thinking: LLM 内部推理过程；role 为 ``"user"`` 时恒为 ``None``。
    """

    event_type: EventType
    message: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    role: Role = Role.USER
    timestamp: datetime = field(default_factory=datetime.now)
    tool: str | None = None
    tool_call_id: str | None = None
    event_payload: dict | None = None
    thinking: str | None = None
    plan_status: dict | None = None  # 系统注入，简化格式 {current, completed, remaining}

    def to_json(self) -> str:
        """序列化为 JSON 字符串，用于注入 LLM 对话历史。"""
        import dataclasses
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False, default=str)

    @staticmethod
    def from_dict(d: dict) -> "Message":
        """从字典反序列化 Message，用于 save/restore。

        与 :meth:`from_llm_reply` 不同，此方法从 ``dataclasses.asdict()``
        的输出重建 Message，而非从 LLM JSON 解析。
        """
        ts = d.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = None  # 由 field(default_factory=datetime.now) 自动填充

        return Message(
            event_type=EventType(d["event_type"]),
            message=d.get("message", ""),
            id=d.get("id", ""),
            role=Role(d.get("role", "user")),
            timestamp=ts,
            tool=d.get("tool"),
            tool_call_id=d.get("tool_call_id"),
            event_payload=d.get("event_payload"),
            thinking=d.get("thinking"),
            plan_status=d.get("plan_status"),
        )

    @staticmethod
    def from_llm_reply(reply: str) -> "Message":
        """从 LLM 返回的 JSON 构建 Message。

        按 ``06_output_format.md`` 扁平 schema 解析。
        ``json_repair`` 自动修复 LLM 常见格式错误（未转义换行、尾部逗号等）。

        Args:
            reply: LLM 返回的原始 JSON 字符串。

        Returns:
            解析后的 Message，``role`` 固定为 ``"assistant"``。

        """
        import json_repair
        parsed = json_repair.loads(reply)
        return Message(
            role=Role.ASSISTANT,
            id=parsed["id"],
            message=parsed["message"],
            event_type=parsed["event_type"],
            thinking=parsed.get("thinking"),
            tool=parsed.get("tool"),
            event_payload=parsed.get("event_payload"),
        )
