"""Explicit tool definitions and typed outcomes for the v2 runtime."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from src.get_me_in.domain.agents import AgentKey, Capability

class ConfirmationMode(StrEnum):
    """Whether a tool call requires an application-level approval round trip."""

    NEVER = "never"
    ALWAYS = "always"


@dataclass(frozen=True)
class ToolSchema:
    """Flat, typed arguments accepted by a ToolDefinition."""

    properties: Mapping[str, type]
    required: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ToolPolicy:
    """Visibility and approval rules declared beside a tool, never in a registry."""

    required_capabilities: frozenset[Capability] = frozenset()
    confirmation: ConfirmationMode = ConfirmationMode.NEVER


class ToolOutcome:
    """Base type for all results emitted by a tool handler."""


@dataclass(frozen=True)
class ToolSuccess(ToolOutcome):
    output: object


@dataclass(frozen=True)
class ToolFailure(ToolOutcome):
    code: str
    message: str
    suggestion: str | None = None


@dataclass(frozen=True)
class ToolHandoff(ToolOutcome):
    target: AgentKey
    context: str


@dataclass(frozen=True)
class ToolInteraction(ToolOutcome):
    kind: str
    prompt: str
    choices: tuple[str, ...] = ()


class ToolHandlerContext(Protocol):
    """Minimal structural context required by a domain tool handler."""

    session_id: str
    agent_key: AgentKey


ToolHandler = Callable[[Mapping[str, object], ToolHandlerContext], ToolOutcome]


@dataclass(frozen=True)
class ToolDefinition:
    """One explicitly assembled tool with no import-time registration behavior."""

    name: str
    description: str
    schema: ToolSchema
    policy: ToolPolicy
    handler: ToolHandler
