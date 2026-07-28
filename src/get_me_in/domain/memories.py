"""Immutable, versioned memory contracts for the R6 application boundary."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import ConversationRecord


class MemoryCategory(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"


@dataclass(frozen=True)
class MemoryRecord:
    schema_version: int
    memory_id: str
    agent_key: AgentKey
    category: MemoryCategory
    content: str
    created_at: datetime


@dataclass(frozen=True)
class MemoryBuildSource:
    """A copied provider-neutral conversation with no display thinking summaries."""

    session_id: str
    agent_key: AgentKey
    records: tuple[ConversationRecord, ...]


@dataclass(frozen=True)
class MemoryBuildReceipt:
    job_id: str
    source_session_id: str
    source_agent_key: AgentKey


@dataclass(frozen=True)
class MemoryBuildReport:
    source_session_id: str
    created_memory_ids: tuple[str, ...] = ()
    deleted_memory_id: str | None = None
    error: str | None = None
