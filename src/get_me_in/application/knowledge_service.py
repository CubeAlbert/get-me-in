"""Explicit, serial knowledge lifecycle service using injected ports."""

from threading import Lock

from src.get_me_in.application.app_results import CloseReport
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.background_worker import BackgroundWorker
from dataclasses import replace

from src.get_me_in.domain.knowledge import (
    IndexManifest,
    KnowledgeDocument,
    KnowledgeState,
    ManifestEntry,
    ManifestStatus,
    PendingIndexOperation,
    ReloadReport,
)
from src.get_me_in.ports.knowledge import DocumentChunker, KnowledgeIndexPort, KnowledgeSourceRepository, ManifestRepository
from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.retrieval import RetrievalResult


class KnowledgeService:
    """Coordinates sources, manifest and index without owning its worker."""

    def __init__(
        self,
        sources: tuple[KnowledgeSourceRepository, ...],
        chunker: DocumentChunker,
        index: KnowledgeIndexPort,
        manifests: ManifestRepository,
        worker: BackgroundWorker,
    ) -> None:
        self._sources = sources
        self._chunker = chunker
        self._index = index
        self._manifests = manifests
        self._worker = worker
        self._state = KnowledgeState.IDLE
        self._cancellation = CancellationToken()
        self._lock = Lock()
        self._closed = False

    @property
    def state(self) -> KnowledgeState:
        return self._state

    def start(self) -> None:
        self.reload()

    def search(
        self, query: str, *, collection: str, category: str | None, top_k: int, cancellation: CancellationSignal
    ) -> tuple[RetrievalResult, ...]:
        if cancellation.is_cancelled:
            raise InterruptedError
        if self._state not in {KnowledgeState.READY, KnowledgeState.DEGRADED}:
            raise RuntimeError("retrieval_unavailable")
        return tuple(RetrievalResult(hit.content, hit.metadata) for hit in self._index.search(
            query, collection=collection, category=category, top_k=top_k, cancellation=cancellation
        ))

    def reload(self, target: str | None = None) -> ReloadReport:
        if not self._lock.acquire(blocking=False):
            return ReloadReport(busy=True)
        try:
            self._ensure_open()
            self._state = KnowledgeState.LOADING
            self._cancellation.reset()
            manifest = self._manifests.load()
            observed_pairs = tuple(
                (source, repository)
                for repository in self._sources
                for source in repository.scan(target)
            )
            observed = tuple(source for source, _ in observed_pairs)
            report = manifest.diff(observed)
            repositories = {source.source_key: repository for source, repository in observed_pairs}
            failures: list[str] = []
            for source_key in (*report.deleted, *(old for old, _ in report.renamed)):
                entry = next(entry for entry in manifest.entries if entry.source_key == source_key)
                manifest, error = self._delete_entry(manifest, entry)
                if error:
                    failures.append(error)
            for source_key in report.retried:
                entry = next(entry for entry in manifest.entries if entry.source_key == source_key)
                if entry.pending_operation is PendingIndexOperation.DELETE:
                    manifest, error = self._delete_entry(manifest, entry)
                else:
                    source = next((item for item in observed if item.source_key == source_key), None)
                    if source is None:
                        error = f"missing retry source: {source_key}"
                    else:
                        manifest, error = self._upsert_source(manifest, source, repositories[source_key])
                if error:
                    failures.append(error)
            for source_key in (*report.added, *report.updated, *(new for _, new in report.renamed)):
                manifest, error = self._upsert_source(manifest, next(source for source in observed if source.source_key == source_key), repositories[source_key])
                if error:
                    failures.append(error)
            self._state = KnowledgeState.DEGRADED if failures else KnowledgeState.READY
            return replace(report, failures=tuple(failures))
        except Exception as error:
            self._state = KnowledgeState.ERROR
            return ReloadReport(failures=(str(error),))
        finally:
            self._lock.release()

    def index_document(self, document: KnowledgeDocument) -> ReloadReport:
        if not self._lock.acquire(blocking=False):
            return ReloadReport(busy=True)
        try:
            self._ensure_open()
            manifest, error = self._upsert_document(self._manifests.load(), document)
            if error:
                self._state = KnowledgeState.DEGRADED
                return ReloadReport(failures=(error,))
            self._state = KnowledgeState.READY
            return ReloadReport(updated=(document.source.source_key,))
        except Exception as error:
            self._state = KnowledgeState.DEGRADED
            return ReloadReport(failures=(str(error),))
        finally:
            self._lock.release()

    def delete_source(self, source_key: str) -> ReloadReport:
        if not self._lock.acquire(blocking=False):
            return ReloadReport(busy=True)
        try:
            self._ensure_open()
            manifest = self._manifests.load()
            entry = next((item for item in manifest.entries if item.source_key == source_key), None)
            if entry is not None:
                _, error = self._delete_entry(manifest, entry)
                if error:
                    self._state = KnowledgeState.DEGRADED
                    return ReloadReport(failures=(error,))
            else:
                self._index.delete_source(source_key, cancellation=self._cancellation)
            return ReloadReport(deleted=(source_key,))
        except Exception as error:
            self._state = KnowledgeState.DEGRADED
            return ReloadReport(failures=(str(error),))
        finally:
            self._lock.release()

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        del reason
        self._cancellation.cancel()

    def close(self) -> CloseReport:
        if self._closed:
            return CloseReport()
        self._closed = True
        self._state = KnowledgeState.CLOSING
        issues = []
        for name, closer in (("knowledge_index", self._index.close), ("manifest_repository", self._manifests.close)):
            try:
                closer()
            except Exception as error:
                from src.get_me_in.application.app_results import CloseIssue
                issues.append(CloseIssue(name, str(error)))
        self._state = KnowledgeState.CLOSED
        return CloseReport(closed=("knowledge_service",), issues=tuple(issues))

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("KnowledgeService is closed")

    def _upsert_source(
        self, manifest: IndexManifest, source: object, repository: KnowledgeSourceRepository
    ) -> tuple[IndexManifest, str | None]:
        try:
            return self._upsert_document(manifest, repository.read(source))
        except Exception as error:
            return manifest, f"{source.source_key}: {error}"

    def _upsert_document(
        self, manifest: IndexManifest, document: KnowledgeDocument
    ) -> tuple[IndexManifest, str | None]:
        source = document.source
        chunks = self._chunker.chunk(document)
        existing = next((entry for entry in manifest.entries if entry.source_key == source.source_key), None)
        pending = ManifestEntry(
            source.source_key, source.collection, source.content_hash,
            existing.indexed_hash if existing else None, source.mtime,
            existing.chunk_ids if existing else (), ManifestStatus.PENDING,
            PendingIndexOperation.UPSERT,
        )
        manifest = self._replace_entry(manifest, pending)
        self._manifests.save(manifest)
        try:
            self._index.replace_source(source, chunks, self._cancellation)
        except Exception as error:
            failed = replace(pending, status=ManifestStatus.ERROR, error=str(error))
            manifest = self._replace_entry(manifest, failed)
            self._manifests.save(manifest)
            return manifest, f"{source.source_key}: {error}"
        ready = replace(
            pending, indexed_hash=source.content_hash,
            chunk_ids=tuple(chunk.chunk_id for chunk in chunks),
            status=ManifestStatus.READY, pending_operation=None,
        )
        manifest = self._replace_entry(manifest, ready)
        self._manifests.save(manifest)
        return manifest, None

    def _delete_entry(
        self, manifest: IndexManifest, entry: ManifestEntry
    ) -> tuple[IndexManifest, str | None]:
        pending = replace(entry, status=ManifestStatus.PENDING, pending_operation=PendingIndexOperation.DELETE, error=None)
        manifest = self._replace_entry(manifest, pending)
        self._manifests.save(manifest)
        try:
            self._index.delete_source(entry.source_key, cancellation=self._cancellation)
        except Exception as error:
            failed = replace(pending, status=ManifestStatus.ERROR, error=str(error))
            manifest = self._replace_entry(manifest, failed)
            self._manifests.save(manifest)
            return manifest, f"{entry.source_key}: {error}"
        manifest = IndexManifest(
            manifest.schema_version,
            tuple(item for item in manifest.entries if item.source_key != entry.source_key),
        )
        self._manifests.save(manifest)
        return manifest, None

    @staticmethod
    def _replace_entry(manifest: IndexManifest, replacement: ManifestEntry) -> IndexManifest:
        entries = tuple(
            replacement if entry.source_key == replacement.source_key else entry
            for entry in manifest.entries
        )
        if all(entry.source_key != replacement.source_key for entry in manifest.entries):
            entries = (*entries, replacement)
        return IndexManifest(manifest.schema_version, entries)
