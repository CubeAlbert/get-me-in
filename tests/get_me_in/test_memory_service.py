"""R6 memory contracts: copied inputs, repository persistence and async build."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
from time import monotonic, sleep
import unittest

from src.get_me_in.adapters.json_memory_repository import JsonMemoryRepository
from src.get_me_in.application.background_worker import BackgroundWorker
from src.get_me_in.application.app_results import BackgroundJobState
from src.get_me_in.application.memory_service import MemoryService
from src.get_me_in.application.memory_extractor import MemoryExtractor
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.memories import MemoryBuildSource, MemoryCategory, MemoryRecord
from src.get_me_in.domain.messages import MessageRecord, Role
from src.get_me_in.ports.llm import LLMResult


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
            result = _wait_for_job(worker, receipt.job_id)
        finally:
            worker.close()

        self.assertEqual("session", receipt.source_session_id)
        self.assertEqual(AgentKey.MAIN, receipt.source_agent_key)
        self.assertEqual("memory-build-1", receipt.job_id)
        self.assertEqual(BackgroundJobState.SUCCEEDED, result.state)
        self.assertEqual(("id",), result.value.created_memory_ids)
        self.assertEqual(1, len(repository.records))
        self.assertEqual(1, len(knowledge.documents))

    def test_build_retains_typed_partial_failure_after_repository_write(self) -> None:
        worker = BackgroundWorker("memory-partial-test", 1)
        repository = _Repository()
        service = MemoryService(repository, _Extractor(), _Knowledge(fail_index=True), worker)
        source = MemoryBuildSource("session", AgentKey.MAIN, ())
        try:
            receipt = service.build_async(source)
            result = _wait_for_job(worker, receipt.job_id)
        finally:
            worker.close()

        self.assertEqual(BackgroundJobState.FAILED, result.state)
        self.assertEqual(("id",), result.value.created_memory_ids)
        self.assertEqual("index failed", result.value.error)

    def test_delete_coordinates_index_before_removing_repository_record(self) -> None:
        worker = BackgroundWorker("memory-delete-test", 1)
        repository, knowledge = _Repository(), _Knowledge()
        service = MemoryService(repository, _Extractor(), knowledge, worker)
        try:
            report = service.delete("memory-1")
        finally:
            worker.close()

        self.assertEqual("memory-1", report.deleted_memory_id)
        self.assertEqual(["memories/memory-1.json"], knowledge.deleted_sources)
        self.assertEqual(["memory-1"], repository.deleted)

    def test_close_isolates_owned_resource_failures(self) -> None:
        worker = BackgroundWorker("memory-close-test", 1)
        repository = _Repository(fail_close=True)
        extractor = _Extractor(fail_close=True)
        service = MemoryService(repository, extractor, _Knowledge(), worker)

        report = service.close()
        worker.close()

        self.assertEqual(("memory_service",), report.closed)
        self.assertEqual(
            ("memory_extractor", "memory_repository"),
            tuple(issue.resource_name for issue in report.issues),
        )


class MemoryExtractorTests(unittest.TestCase):
    def test_extractor_uses_explicit_zero_temperature(self) -> None:
        llm = _RecordingLlm()
        extractor = MemoryExtractor(llm, "extract", _Clock(), _Ids(), 1)
        source = MemoryBuildSource("session", AgentKey.MAIN, ())

        extractor.extract(source, CancellationToken())

        self.assertEqual(0.0, llm.request.temperature)


class _Clock:
    def now(self): return _now()


class _Repository:
    def __init__(self, *, fail_close=False): self.records = []; self.deleted = []; self.fail_close = fail_close
    def write(self, record): self.records.append(record); return object()
    def delete(self, memory_id): self.deleted.append(memory_id)
    def close(self):
        if self.fail_close: raise RuntimeError("repository close failed")


class _Extractor:
    def __init__(self, *, fail_close=False): self.fail_close = fail_close
    def extract(self, source, cancellation): return (MemoryRecord(1, "id", AgentKey.MAIN, MemoryCategory.FACT, "fact", _now()),)
    def close(self):
        if self.fail_close: raise RuntimeError("extractor close failed")


class _Knowledge:
    def __init__(self, *, fail_index=False): self.documents = []; self.deleted_sources = []; self.fail_index = fail_index
    def index_document(self, document, cancellation=None):
        self.documents.append(document)
        return type("Report", (), {"busy": False, "failures": ("index failed",) if self.fail_index else ()})()
    def delete_source(self, source_key, *, finalize=None):
        self.deleted_sources.append(source_key)
        if finalize is not None:
            finalize()
        return type("Report", (), {"failures": ()})()


class _RecordingLlm:
    def complete(self, request, cancellation):
        self.request = request
        return LLMResult("[]")

    def close(self):
        pass


class _Ids:
    def new_id(self):
        return "id"


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)


def _wait_for_job(worker: BackgroundWorker, job_id: str):
    deadline = monotonic() + 1
    while monotonic() < deadline:
        result = worker.result(job_id)
        if result is not None and result.state in {
            BackgroundJobState.SUCCEEDED,
            BackgroundJobState.FAILED,
            BackgroundJobState.CANCELLED,
        }:
            return result
        sleep(0.001)
    raise AssertionError(f"background job did not finish: {job_id}")
