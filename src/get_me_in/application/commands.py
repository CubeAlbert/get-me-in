"""Typed input commands for the v2 runtime."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeCommand:
    """Base type for commands accepted by ``AgentRuntime``."""


@dataclass(frozen=True)
class UserMessage(RuntimeCommand):
    text: str


@dataclass(frozen=True)
class Continue(RuntimeCommand):
    pass


@dataclass(frozen=True)
class Approve(RuntimeCommand):
    call_id: str


@dataclass(frozen=True)
class Reject(RuntimeCommand):
    call_id: str
    reason: str = ""


@dataclass(frozen=True)
class SubmitSelection(RuntimeCommand):
    request_id: str
    value: str


@dataclass(frozen=True)
class CancelSelection(RuntimeCommand):
    request_id: str
    reason: str = "Selection cancelled by user"


@dataclass(frozen=True)
class ToolResult(RuntimeCommand):
    """The explicit result that resumes a runtime paused for a tool call."""

    call_id: str
    output: str


@dataclass(frozen=True)
class CompleteHandoff(RuntimeCommand):
    call_id: str
    summary: str


@dataclass(frozen=True)
class FailHandoff(RuntimeCommand):
    call_id: str
    code: str
    message: str
    terminal: bool = False


@dataclass(frozen=True)
class Cancel(RuntimeCommand):
    reason: str = "Cancelled by user"
