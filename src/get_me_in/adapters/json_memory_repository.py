"""Versioned JSON memory repository; never reads legacy Markdown memories."""

import json
from hashlib import sha256
from pathlib import Path

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.knowledge import KnowledgeCollection, KnowledgeDocument, KnowledgeSource
from src.get_me_in.domain.memories import MemoryCategory, MemoryRecord


class JsonMemoryRepository:
    def __init__(self, root: Path, clock: object) -> None:
        self._root, self._clock = root, clock

    def write(self, record: MemoryRecord) -> KnowledgeDocument:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._root / f"{record.memory_id}.json"
        path.write_text(json.dumps({"schema_version": record.schema_version, "memory_id": record.memory_id, "agent_key": record.agent_key.value, "category": record.category.value, "content": record.content, "created_at": record.created_at.isoformat()}), encoding="utf-8")
        return self.read(self._source(path))

    def get(self, memory_id: str) -> MemoryRecord | None:
        path = self._root / f"{memory_id}.json"
        return self._record(path) if path.exists() else None

    def list(self, agent: AgentKey | None = None) -> tuple[MemoryRecord, ...]:
        records = tuple(self._record(path) for path in sorted(self._root.glob("*.json"))) if self._root.exists() else ()
        return tuple(record for record in records if agent is None or record.agent_key is agent)

    def delete(self, memory_id: str) -> None:
        (self._root / f"{memory_id}.json").unlink(missing_ok=True)

    def scan(self, target: str | None = None) -> tuple[KnowledgeSource, ...]:
        sources = tuple(self._source(path) for path in sorted(self._root.glob("*.json"))) if self._root.exists() else ()
        return tuple(source for source in sources if target is None or target in source.source_key)

    def read(self, source: KnowledgeSource) -> KnowledgeDocument:
        record = self._record(self._root / source.source_key.removeprefix("memories/"))
        return KnowledgeDocument(source, record.content, {"category": record.category.value, "agent": record.agent_key.value})

    def close(self) -> None: pass

    def _source(self, path: Path) -> KnowledgeSource:
        return KnowledgeSource(KnowledgeCollection.MEMORIES, f"memories/{path.name}", sha256(path.read_bytes()).hexdigest(), self._clock.now())

    def _record(self, path: Path) -> MemoryRecord:
        raw = json.loads(path.read_text(encoding="utf-8"))
        from datetime import datetime
        return MemoryRecord(raw["schema_version"], raw["memory_id"], AgentKey(raw["agent_key"]), MemoryCategory(raw["category"]), raw["content"], datetime.fromisoformat(raw["created_at"]))
