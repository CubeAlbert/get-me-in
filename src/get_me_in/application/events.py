"""Typed output events emitted by the runtime."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord
from src.get_me_in.domain.plans import Plan


@dataclass(frozen=True)
class RuntimeEvent:
    """Base type for Runtime output; it deliberately carries no magic dict."""


class ProgressKind(StrEnum):
    CALLING_MODEL = "calling_model"
    REPAIRING_MODEL_RESPONSE = "repairing_model_response"
    WAITING_FOR_TOOL_RESULT = "waiting_for_tool_result"


@dataclass(frozen=True)
class Progress(RuntimeEvent):
    kind: ProgressKind


@dataclass(frozen=True)
class ApprovalRequested(RuntimeEvent):
    call_id: str
    tool_name: str


@dataclass(frozen=True)
class SelectionRequested(RuntimeEvent):
    request_id: str
    prompt: str
    choices: tuple[str, ...]


@dataclass(frozen=True)
class ToolStarted(RuntimeEvent):
    call_id: str
    tool_name: str
    message: str
    arguments: Mapping[str, object] = field(default_factory=dict)
    thinking: str | None = None


@dataclass(frozen=True)
class ToolFinished(RuntimeEvent):
    call_id: str
    tool_name: str
    output: str
    plan: Plan | None = None


@dataclass(frozen=True)
class HandoffRequested(RuntimeEvent):
    call_id: str
    source: AgentKey
    target: AgentKey
    context: str


@dataclass(frozen=True)
class Completed(RuntimeEvent):
    message: MessageRecord


@dataclass(frozen=True)
class Failed(RuntimeEvent):
    code: str
    message: str


@dataclass(frozen=True)
class Paused(RuntimeEvent):
    code: str
    message: str


@dataclass(frozen=True)
class Cancelled(RuntimeEvent):
    reason: str
