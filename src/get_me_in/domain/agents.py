"""Declarative agent metadata used by the composition root."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class AgentKey(StrEnum):
    """Stable identifiers for agents included in the current application."""

    MAIN = "main"
    RESUME = "resume"
    JOB_SEARCH = "job_search"


class Capability(StrEnum):
    """Fine-grained capabilities used by ToolCatalog visibility rules."""

    SYSTEM = "system"
    CURRENT_DATETIME = "current_datetime"
    PLAN = "plan"
    INTERACTION = "interaction"
    WEB_SEARCH = "web.search"
    EXTERNAL_FILE_READ = "external_file.read"
    ROUTE = "route"
    RETURN_TO_MAIN = "return_to_main"
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_WRITE = "workspace.write"
    WORKSPACE_OPEN = "workspace.open"
    RESUME_ARTIFACT = "resume.artifact"
    MEMORY_QUERY = "memory.query"
    KNOWLEDGE_QUERY = "knowledge.query"


@dataclass(frozen=True)
class AgentStyle:
    """Prompt style values that are independent of an agent implementation."""

    tone: str
    verbosity: str
    explanation_style: str
    rules: tuple[str, ...] = ()
    avoids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentSpec:
    """Complete, immutable declaration replacing v1's 14 metadata methods."""

    key: AgentKey
    display_name: str
    description: str
    responsibilities: tuple[str, ...]
    primary_goal: str
    success_criteria: tuple[str, ...]
    hard_constraints: tuple[str, ...]
    soft_constraints: tuple[str, ...]
    style: AgentStyle
    model_profile: str
    temperature: float
    capabilities: frozenset[Capability]
    priorities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isfinite(self.temperature) or not 0 <= self.temperature <= 2:
            raise ValueError("Agent temperature must be a finite value between 0 and 2")


@dataclass(frozen=True)
class AgentDescriptor:
    """Public routing view that does not expose an agent implementation."""

    key: AgentKey
    display_name: str
    description: str
    responsibilities: tuple[str, ...]
    hard_constraints: tuple[str, ...]

    @classmethod
    def from_spec(cls, spec: AgentSpec) -> "AgentDescriptor":
        return cls(
            key=spec.key,
            display_name=spec.display_name,
            description=spec.description,
            responsibilities=spec.responsibilities,
            hard_constraints=spec.hard_constraints,
        )
