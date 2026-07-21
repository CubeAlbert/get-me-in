"""Provider-independent conversation records."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Role(StrEnum):
    """The speaker represented by a conversation event."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class EventKind(StrEnum):
    """Semantic kind of a conversation event."""

    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


@dataclass(frozen=True)
class ConversationEvent:
    """Immutable message data that can be passed to an LLM port."""

    event_id: str
    role: Role
    kind: EventKind
    content: str
    timestamp: datetime
