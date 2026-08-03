"""Port for the versioned memory repository."""

from typing import Protocol

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.knowledge import KnowledgeDocument
from src.get_me_in.domain.memories import MemoryRecord


class MemoryRepository(Protocol):
    def write(self, record: MemoryRecord) -> KnowledgeDocument: ...

    def get(self, memory_id: str) -> MemoryRecord | None: ...

    def list(self, agent: AgentKey | None = None) -> tuple[MemoryRecord, ...]: ...

    def delete(self, memory_id: str) -> None: ...

    def close(self) -> None: ...
