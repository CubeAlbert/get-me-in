"""Provider-independent, strongly typed conversation records."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Role(StrEnum):
    """Speaker roles used by ordinary conversation messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class MessageRecord:
    event_id: str
    role: Role
    content: str
    timestamp: datetime
    turn_id: str = ""
    thinking: str | None = None


@dataclass(frozen=True)
class ToolCallRecord:
    event_id: str
    call_id: str
    tool_name: str
    arguments: Mapping[str, object]
    timestamp: datetime
    turn_id: str = ""
    thinking: str | None = None


@dataclass(frozen=True)
class ToolResultRecord:
    event_id: str
    call_id: str
    tool_name: str
    output: object
    timestamp: datetime
    turn_id: str = ""


ConversationRecord = MessageRecord | ToolCallRecord | ToolResultRecord
