"""Declarative agent metadata used by the v2 composition root."""

from dataclasses import dataclass
from enum import StrEnum


class AgentKey(StrEnum):
    """Stable identifiers for agents included in the current application."""

    MAIN = "main"
    RESUME = "resume"
    JOB_SEARCH = "job_search"


class Capability(StrEnum):
    """Capabilities used later by ToolCatalog visibility rules."""

    ROUTE = "route"
    RESUME_WORKSPACE = "resume.workspace"
    RESUME_ARTIFACT = "resume.artifact"
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
    capabilities: frozenset[Capability]
    priorities: tuple[str, ...] = ()


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
