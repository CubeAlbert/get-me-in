"""R6 manifest-diff domain tests; KnowledgeService follows in a later slice."""

from datetime import datetime, timezone
from threading import Event, Thread
from time import monotonic, sleep
import unittest

from src.get_me_in.domain.knowledge import (
    IndexManifest,
    KnowledgeCollection,
    KnowledgeSource,
    ManifestEntry,
    ManifestStatus,
    PendingIndexOperation,
)
from src.get_me_in.application.background_worker import BackgroundWorker
from src.get_me_in.application.knowledge_service import KnowledgeService
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.domain.knowledge import IndexHit, KnowledgeDocument, KnowledgeState


class ManifestDiffTests(unittest.TestCase):
    def test_diff_classifies_add_update_delete_and_unchanged_in_source_key_order(self) -> None:
        manifest = _manifest(
            _entry("references/a.md", "a", indexed_hash="a"),
            _entry("references/b.md", "old", indexed_hash="old"),
            _entry("references/deleted.md", "gone", indexed_hash="gone"),
        )

        report = manifest.diff((_source("references/c.md", "c"), _source("references/b.md", "new"), _source("references/a.md", "a")))

        self.assertEqual(("references/c.md",), report.added)
        self.assertEqual(("references/b.md",), report.updated)
        self.assertEqual(("references/deleted.md",), report.deleted)
        self.assertEqual(("references/a.md",), report.unchanged)
        self.assertEqual((), report.renamed)
        self.assertEqual((), report.retried)

    def test_diff_recognizes_only_unambiguous_same_collection_same_hash_renames(self) -> None:
        manifest = _manifest(_entry("references/old.md", "same", indexed_hash="same"))

        report = manifest.diff((_source("references/new.md", "same"),))

        self.assertEqual((("references/old.md", "references/new.md"),), report.renamed)
        self.assertEqual((), report.added)
        self.assertEqual((), report.deleted)

    def test_ambiguous_rename_is_reported_as_add_and_delete(self) -> None:
        manifest = _manifest(
            _entry("references/old-a.md", "same", indexed_hash="same"),
            _entry("references/old-b.md", "same", indexed_hash="same"),
        )

        report = manifest.diff((_source("references/new.md", "same"),))

        self.assertEqual((), report.renamed)
        self.assertEqual(("references/new.md",), report.added)
        self.assertEqual(("references/old-a.md", "references/old-b.md"), report.deleted)

    def test_pending_and_error_operations_are_retried_instead_of_reclassified(self) -> None:
        manifest = _manifest(
            _entry("references/retry-upsert.md", "old", indexed_hash="old", status=ManifestStatus.ERROR, operation=PendingIndexOperation.UPSERT),
            _entry("references/retry-delete.md", "gone", indexed_hash="gone", status=ManifestStatus.PENDING, operation=PendingIndexOperation.DELETE),
        )

        report = manifest.diff((_source("references/retry-upsert.md", "new"),))

        self.assertEqual(("references/retry-delete.md", "references/retry-upsert.md"), report.retried)
        self.assertEqual((), report.updated)
        self.assertEqual((), report.deleted)

    def test_no_change_is_idempotent(self) -> None:
        manifest = _manifest(_entry("references/a.md", "hash", indexed_hash="hash"))
        observed = (_source("references/a.md", "hash"),)

        self.assertEqual(manifest.diff(observed), manifest.diff(observed))
        self.assertEqual(("references/a.md",), manifest.diff(observed).unchanged)

    def test_pending_status_is_not_unchanged_without_a_completed_operation(self) -> None:
        manifest = _manifest(
            _entry("references/a.md", "hash", indexed_hash="hash", status=ManifestStatus.PENDING)
        )

        report = manifest.diff((_source("references/a.md", "hash"),))

        self.assertEqual(("references/a.md",), report.updated)
        self.assertEqual((), report.unchanged)

    def test_duplicate_observed_source_keys_are_rejected(self) -> None:
        manifest = _manifest()

        with self.assertRaisesRegex(ValueError, "unique source_key"):
            manifest.diff((_source("references/a.md", "one"), _source("references/a.md", "two")))


class KnowledgeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = BackgroundWorker("knowledge-test", 1)
        self.index = _Index()
        self.manifests = _Manifests()
        self.source = _source("references/a.md", "hash")
        self.service = KnowledgeService((_Sources((self.source,)),), _Chunker(), self.index, self.manifests, self.worker)

    def tearDown(self) -> None:
        self.service.close()
        self.worker.close()

    def test_reload_sets_ready_and_search_uses_existing_retrieval_contract(self) -> None:
        self.assertEqual(KnowledgeState.IDLE, self.service.state)
        self.service.start()
        self.assertTrue(self.index.replaced_event.wait(timeout=1))
        _wait_for_state(self.service, KnowledgeState.READY)

        result = self.service.search("query", collection="references", category=None, top_k=1, cancellation=CancellationToken())

        self.assertEqual(KnowledgeState.READY, self.service.state)
        self.assertEqual(1, self.index.prepare_calls)
        self.assertEqual(("found",), tuple(item.content for item in result))

    def test_startup_prepares_index_even_when_manifest_is_unchanged(self) -> None:
        self.manifests.value = _manifest(
            _entry("references/a.md", "hash", indexed_hash="hash")
        )

        self.service.start()
        self.assertTrue(self.index.prepared_event.wait(timeout=1))
        _wait_for_state(self.service, KnowledgeState.READY)

        self.assertEqual(1, self.index.prepare_calls)
        self.assertEqual([], self.index.replaced)

    def test_prepare_failure_keeps_service_unavailable_and_can_be_retried(self) -> None:
        self.index.prepare_error = RuntimeError("model load failed")

        self.service.start()
        _wait_for_state(self.service, KnowledgeState.ERROR)

        with self.assertRaisesRegex(RuntimeError, "retrieval_unavailable"):
            self.service.search(
                "query",
                collection="references",
                category=None,
                top_k=1,
                cancellation=CancellationToken(),
            )

        self.index.prepare_error = None
        report = self.service.reload()

        self.assertEqual((), report.failures)
        self.assertEqual(KnowledgeState.READY, self.service.state)
        self.assertEqual(2, self.index.prepare_calls)

    def test_search_is_unavailable_before_first_successful_load(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "retrieval_unavailable"):
            self.service.search("query", collection="references", category=None, top_k=1, cancellation=CancellationToken())

    def test_index_and_delete_are_serialized_and_report_results(self) -> None:
        document = KnowledgeDocument(self.source, "content")

        self.assertEqual(("references/a.md",), self.service.index_document(document).updated)
        self.assertEqual(("references/a.md",), self.service.delete_source("references/a.md").deleted)

    def test_reload_persists_pending_then_ready_index_state(self) -> None:
        report = self.service.reload()

        self.assertEqual(("references/a.md",), report.added)
        self.assertEqual(("references/a.md",), tuple(self.index.replaced))
        entry = self.manifests.value.entries[0]
        self.assertEqual(ManifestStatus.READY, entry.status)
        self.assertEqual("hash", entry.indexed_hash)

    def test_targeted_reload_does_not_delete_manifest_entries_outside_target(self) -> None:
        memory_source = _source("memories/id.json", "memory-hash")
        self.manifests.value = _manifest(
            _entry("references/a.md", "hash", indexed_hash="hash"),
            _entry("memories/id.json", "memory-hash", indexed_hash="memory-hash"),
        )
        service = KnowledgeService(
            (_Sources((self.source,)), _Sources((memory_source,))),
            _Chunker(),
            self.index,
            self.manifests,
            self.worker,
        )

        report = service.reload("memories")

        self.assertEqual((), report.deleted)
        self.assertEqual(("memories/id.json",), report.unchanged)
        self.assertEqual(
            ("memories/id.json", "references/a.md"),
            tuple(sorted(entry.source_key for entry in self.manifests.value.entries)),
        )
        service.close()

    def test_targeted_reload_still_deletes_missing_entries_inside_target(self) -> None:
        self.manifests.value = _manifest(
            _entry("references/a.md", "hash", indexed_hash="hash"),
            _entry("memories/missing.json", "memory-hash", indexed_hash="memory-hash"),
        )

        report = self.service.reload("memories")

        self.assertEqual(("memories/missing.json",), report.deleted)
        self.assertEqual(
            ("references/a.md",),
            tuple(entry.source_key for entry in self.manifests.value.entries),
        )

    def test_request_cancel_interrupts_only_an_active_reload(self) -> None:
        blocking_index = _BlockingIndex()
        service = KnowledgeService(
            (_Sources((self.source,)),), _Chunker(), blocking_index, self.manifests, self.worker
        )

        service.start()
        self.assertTrue(blocking_index.started.wait(timeout=1))
        service.request_cancel()
        self.assertTrue(blocking_index.cancelled.wait(timeout=1))
        _wait_for_state(service, KnowledgeState.DEGRADED)

        self.assertTrue(service.index_document(KnowledgeDocument(self.source, "content")).updated)
        service.close()

    def test_startup_cancel_is_not_reset_before_queued_reload_begins(self) -> None:
        worker = _QueuedWorker()
        blocking_index = _BlockingIndex()
        service = KnowledgeService(
            (_Sources((self.source,)),), _Chunker(), blocking_index, self.manifests, worker
        )

        service.start()
        service.request_cancel()
        worker.run()

        self.assertTrue(blocking_index.cancelled.is_set())
        self.assertEqual(KnowledgeState.DEGRADED, service.state)
        service.close()

    def test_search_returns_busy_while_index_mutation_holds_serial_boundary(self) -> None:
        blocking_index = _BlockingIndex()
        service = KnowledgeService(
            (_Sources((self.source,)),), _Chunker(), blocking_index, self.manifests, self.worker
        )
        thread = Thread(target=service.reload)
        thread.start()
        self.assertTrue(blocking_index.started.wait(timeout=1))

        with self.assertRaisesRegex(RuntimeError, "retrieval_busy"):
            service.search(
                "query",
                collection="references",
                category=None,
                top_k=1,
                cancellation=CancellationToken(),
            )

        service.request_cancel()
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        service.close()

    def test_delete_finalize_failure_keeps_retryable_manifest_intent(self) -> None:
        memory_source = _source("memories/id.json", "hash")
        self.manifests.value = _manifest(
            _entry("memories/id.json", "hash", indexed_hash="hash")
        )
        service = KnowledgeService(
            (_Sources((memory_source,)),),
            _Chunker(),
            self.index,
            self.manifests,
            self.worker,
        )

        failed = service.delete_source(
            "memories/id.json", finalize=lambda: _raise_finalize_error()
        )

        self.assertEqual(("memories/id.json: repository failed",), failed.failures)
        entry = self.manifests.value.entries[0]
        self.assertEqual(ManifestStatus.ERROR, entry.status)
        self.assertEqual(PendingIndexOperation.DELETE, entry.pending_operation)

        reloaded = service.reload()
        self.assertEqual(
            ("memories/id.json: delete finalize pending",), reloaded.failures
        )
        self.assertEqual(PendingIndexOperation.DELETE, self.manifests.value.entries[0].pending_operation)

        succeeded = service.delete_source("memories/id.json", finalize=lambda: None)
        self.assertEqual(("memories/id.json",), succeeded.deleted)
        self.assertEqual((), self.manifests.value.entries)
        service.close()


class _Sources:
    def __init__(self, sources): self.sources = sources
    def scan(self, target=None): return self.sources
    def read(self, source): return KnowledgeDocument(source, "content")


class _Chunker:
    def chunk(self, document): return ()


class _Index:
    def __init__(self):
        self.replaced = []
        self.replaced_event = Event()
        self.prepared_event = Event()
        self.prepare_calls = 0
        self.prepare_error = None
    def prepare(self, cancellation):
        self.prepare_calls += 1
        self.prepared_event.set()
        if self.prepare_error is not None:
            raise self.prepare_error
    def replace_source(self, source, chunks, cancellation): self.replaced.append(source.source_key); self.replaced_event.set()
    def delete_source(self, source_key, *, cancellation): pass
    def search(self, query, *, collection, category, top_k, cancellation): return (IndexHit("chunk", "found", {}, 1.0),)
    def close(self): pass


class _BlockingIndex(_Index):
    def __init__(self):
        super().__init__()
        self.started = Event()
        self.cancelled = Event()
        self._should_block = True

    def replace_source(self, source, chunks, cancellation):
        if not self._should_block:
            return super().replace_source(source, chunks, cancellation)
        self._should_block = False
        self.started.set()
        deadline = monotonic() + 1
        while not cancellation.is_cancelled and monotonic() < deadline:
            sleep(0.001)
        if cancellation.is_cancelled:
            self.cancelled.set()
            self.started.clear()
            raise InterruptedError("cancelled")
        super().replace_source(source, chunks, cancellation)


class _QueuedWorker:
    def __init__(self): self.task = None
    def submit(self, task_name, task): self.task = task; return object()
    def run(self): self.task(CancellationToken())


class _Manifests:
    def __init__(self): self.value = _manifest()
    def load(self): return self.value
    def save(self, manifest): self.value = manifest
    def close(self): pass


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)


def _source(source_key: str, content_hash: str) -> KnowledgeSource:
    collection = KnowledgeCollection(source_key.partition("/")[0])
    return KnowledgeSource(collection, source_key, content_hash, _now())


def _entry(
    source_key: str,
    observed_hash: str,
    *,
    indexed_hash: str | None,
    status: ManifestStatus = ManifestStatus.READY,
    operation: PendingIndexOperation | None = None,
) -> ManifestEntry:
    collection = KnowledgeCollection(source_key.partition("/")[0])
    return ManifestEntry(source_key, collection, observed_hash, indexed_hash, _now(), status=status, pending_operation=operation)


def _manifest(*entries: ManifestEntry) -> IndexManifest:
    return IndexManifest(1, entries)


def _wait_for_state(service: KnowledgeService, expected: KnowledgeState) -> None:
    deadline = monotonic() + 1
    while service.state is not expected and monotonic() < deadline:
        sleep(0.001)
    if service.state is not expected:
        raise AssertionError(f"expected {expected}, got {service.state}")


def _raise_finalize_error() -> None:
    raise RuntimeError("repository failed")
