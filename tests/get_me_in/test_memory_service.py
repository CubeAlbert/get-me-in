"""R6 memory contracts: copied inputs, repository persistence and async build."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.json_memory_repository import JsonMemoryRepository
from src.get_me_in.application.background_worker import BackgroundWorker
from src.get_me_in.application.memory_service import MemoryService
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.memories import MemoryBuildSource, MemoryCategory, MemoryRecord
from src.get_me_in.domain.messages import MessageRecord, Role


class MemoryRepositoryTests(unittest.TestCase):
    def test_json_memory_is_v2_only_and_scannable_as_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonMemoryRepository(Path(temporary), _Clock())
            record = MemoryRecord(1, "memory-1", AgentKey.MAIN, MemoryCategory.FACT, "prefers Python", _now())

            document = repository.write(record)

            self.assertEqual(record, repository.get("memory-1"))
            self.assertEqual(("memories/memory-1.json",), tuple(source.source_key for source in repository.scan()))
            self.assertEqual("prefers Python", document.content)


class MemoryServiceTests(unittest.TestCase):
    def test_build_queues_copied_source_then_writes_and_indexes(self) -> None:
        worker = BackgroundWorker("memory-test", 1)
        repository, extractor, knowledge = _Repository(), _Extractor(), _Knowledge()
        service = MemoryService(repository, extractor, knowledge, worker)
        source = MemoryBuildSource("session", AgentKey.MAIN, ())
        try:
            receipt = service.build_async(source)
            worker.close()
        finally:
            worker.close()

        self.assertEqual("session", receipt.source_session_id)
        self.assertEqual(1, len(repository.records))
        self.assertEqual(1, len(knowledge.documents))


class _Clock:
    def now(self): return _now()


class _Repository:
    def __init__(self): self.records = []
    def write(self, record): self.records.append(record); return object()
    def delete(self, memory_id): pass
    def close(self): pass


class _Extractor:
    def extract(self, source, cancellation): return (MemoryRecord(1, "id", AgentKey.MAIN, MemoryCategory.FACT, "fact", _now()),)


class _Knowledge:
    def __init__(self): self.documents = []
    def index_document(self, document): self.documents.append(document)


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
