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


class _NoDefault:
    def __repr__(self) -> str:
        return "NO_DEFAULT"


NO_DEFAULT = _NoDefault()


@dataclass(frozen=True)
class ToolParameter:
    """One LLM-visible argument contract with deterministic runtime type data."""

    value_type: type
    description: str
    default: object = NO_DEFAULT
    items: type | None = None
    allowed_values: tuple[object, ...] = ()
    nullable: bool = False

    def __post_init__(self) -> None:
        if self.has_default:
            if self.default is None:
                if not self.nullable:
                    raise ValueError("A null tool argument default requires nullable=True")
            elif not isinstance(self.default, self.value_type):
                raise ValueError(
                    f"Tool argument default must be {self.value_type.__name__}"
                )
        for value in self.allowed_values:
            if not isinstance(value, self.value_type):
                raise ValueError(
                    f"Allowed tool argument values must be {self.value_type.__name__}"
                )

    @property
    def has_default(self) -> bool:
        return self.default is not NO_DEFAULT


@dataclass(frozen=True)
class ToolSchema:
    """Flat, typed arguments accepted by a ToolDefinition."""

    properties: Mapping[str, ToolParameter]
    required: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        unknown_required = self.required - self.properties.keys()
        if unknown_required:
            raise ValueError(
                f"Required tool arguments are not declared: {', '.join(sorted(unknown_required))}"
            )
        for name, parameter in self.properties.items():
            if not parameter.description.strip():
                raise ValueError(f"Tool argument {name} requires a description")
            if name in self.required and parameter.has_default:
                raise ValueError(f"Required tool argument {name} cannot declare a default")
            if name in self.required and parameter.nullable:
                raise ValueError(f"Required tool argument {name} cannot be nullable")
            if parameter.items is not None and parameter.value_type is not list:
                raise ValueError(f"Tool argument {name} can declare items only when its type is list")


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
class ToolApproval(ToolOutcome):
    """A tool call paused until the frontend approves or rejects it."""

    prompt: str


@dataclass(frozen=True)
class ToolSelection(ToolOutcome):
    """A tool call paused until the frontend submits or cancels a choice."""

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
    purpose: str
    use_when: str
    do_not_use_when: str
    expected_output: str
    schema: ToolSchema
    policy: ToolPolicy
    handler: ToolHandler

    def __post_init__(self) -> None:
        for field_name in ("name", "purpose", "use_when", "expected_output"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"ToolDefinition.{field_name} must not be empty")
