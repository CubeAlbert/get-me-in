"""Typed output events emitted by the v2 runtime."""

from dataclasses import dataclass

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord


@dataclass(frozen=True)
class RuntimeEvent:
    """Base type for Runtime output; it deliberately carries no magic dict."""


@dataclass(frozen=True)
class Progress(RuntimeEvent):
    message: str


@dataclass(frozen=True)
class ApprovalRequested(RuntimeEvent):
    call_id: str
    summary: str


@dataclass(frozen=True)
class SelectionRequested(RuntimeEvent):
    request_id: str
    prompt: str
    choices: tuple[str, ...]


@dataclass(frozen=True)
class ToolStarted(RuntimeEvent):
    call_id: str
    tool_name: str


@dataclass(frozen=True)
class ToolFinished(RuntimeEvent):
    call_id: str
    tool_name: str
    output: str


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
class Cancelled(RuntimeEvent):
    reason: str
