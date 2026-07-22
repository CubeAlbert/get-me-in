"""R6 manifest-diff domain tests; KnowledgeService follows in a later slice."""

from datetime import datetime, timezone
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

        result = self.service.search("query", collection="references", category=None, top_k=1, cancellation=CancellationToken())

        self.assertEqual(KnowledgeState.READY, self.service.state)
        self.assertEqual(("found",), tuple(item.content for item in result))

    def test_search_is_unavailable_before_first_successful_load(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "retrieval_unavailable"):
            self.service.search("query", collection="references", category=None, top_k=1, cancellation=CancellationToken())

    def test_index_and_delete_are_serialized_and_report_results(self) -> None:
        document = KnowledgeDocument(self.source, "content")

        self.assertEqual(("references/a.md",), self.service.index_document(document).updated)
        self.assertEqual(("references/a.md",), self.service.delete_source("references/a.md").deleted)


class _Sources:
    def __init__(self, sources): self.sources = sources
    def scan(self, target=None): return self.sources
    def read(self, source): return KnowledgeDocument(source, "content")


class _Chunker:
    def chunk(self, document): return ()


class _Index:
    def replace_source(self, source, chunks, cancellation): pass
    def delete_source(self, source_key, *, cancellation): pass
    def search(self, query, *, collection, category, top_k, cancellation): return (IndexHit("chunk", "found", {}, 1.0),)
    def close(self): pass


class _Manifests:
    def load(self): return _manifest()
    def save(self, manifest): pass
    def close(self): pass


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)


def _source(source_key: str, content_hash: str) -> KnowledgeSource:
    return KnowledgeSource(KnowledgeCollection.REFERENCES, source_key, content_hash, _now())


def _entry(
    source_key: str,
    observed_hash: str,
    *,
    indexed_hash: str | None,
    status: ManifestStatus = ManifestStatus.READY,
    operation: PendingIndexOperation | None = None,
) -> ManifestEntry:
    return ManifestEntry(source_key, KnowledgeCollection.REFERENCES, observed_hash, indexed_hash, _now(), status=status, pending_operation=operation)


def _manifest(*entries: ManifestEntry) -> IndexManifest:
    return IndexManifest(1, entries)
