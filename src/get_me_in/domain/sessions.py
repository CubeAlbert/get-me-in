"""Immutable session aggregate models for the v2 application boundary."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import ConversationRecord
from src.get_me_in.domain.plans import Plan


class RuntimePhase(StrEnum):
    READY = "ready"
    MODEL_PENDING = "model_pending"
    MODEL_QUEUED = "model_queued"
    TOOL_READY = "tool_ready"
    WAITING_FOR_TOOL_RESULT = "waiting_for_tool_result"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    WAITING_FOR_SELECTION = "waiting_for_selection"
    WAITING_FOR_HANDOFF = "waiting_for_handoff"
    WAITING_FOR_USER = "waiting_for_user"
    CANCELLED_NOTICE = "cancelled_notice"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class PendingToolCall:
    call_id: str
    tool_name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class AgentSessionState:
    """All persistent Runtime state for one agent within one session."""

    phase: RuntimePhase = RuntimePhase.READY
    history: tuple[ConversationRecord, ...] = ()
    model_calls: int = 0
    pending_tool: PendingToolCall | None = None
    format_repairs_used: int = 0
    cancel_reason: str = "Cancelled by user"
    turn_id: str = ""
    plan: Plan | None = None


@dataclass(frozen=True)
class HandoffFrame:
    source: AgentKey
    target: AgentKey
    call_id: str
    turn_id: str
    context: str


@dataclass(frozen=True)
class SessionState:
    """The single canonical owner of active-agent and agent-local state."""

    session_id: str
    active_agent: AgentKey
    agents: Mapping[AgentKey, AgentSessionState]
    handoff_stack: tuple[HandoffFrame, ...]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SessionTurnView:
    """Read-only user-turn projection exposed to frontends."""

    turn_id: str
    agent_key: AgentKey
    user_text: str
    timestamp: datetime


@dataclass(frozen=True)
class SessionView:
    session_id: str
    active_agent: AgentKey
    phase: RuntimePhase
    plan: Plan | None
    rewind_points: tuple[SessionTurnView, ...] = ()


@dataclass(frozen=True)
class SessionPreview:
    session_id: str
    active_agent: AgentKey
    updated_at: datetime
    preview: str = ""
