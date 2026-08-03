"""Explicit, serial knowledge lifecycle service using injected ports."""

from collections.abc import Callable
import logging
from threading import Lock

from src.get_me_in.application.app_results import CloseIssue, CloseReport
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.background_worker import BackgroundWorker
from dataclasses import replace

from src.get_me_in.domain.knowledge import (
    IndexManifest,
    KnowledgeCollection,
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

logger = logging.getLogger(__name__)
_FILE_ONLY_LOG = {"_get_me_in_file_only": True}


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
        self._reload_cancellation = CancellationToken()
        self._reload_previous_state: KnowledgeState | None = None
        self._startup_reload_pending = False
        self._lock = Lock()
        self._closed = False

    @property
    def state(self) -> KnowledgeState:
        with self._lock:
            return self._state

    def start(self) -> None:
        with self._lock:
            self._ensure_open()
            if self._state is not KnowledgeState.IDLE:
                return
            self._reload_cancellation.reset()
            self._reload_previous_state = KnowledgeState.IDLE
            self._startup_reload_pending = True
            self._state = KnowledgeState.LOADING
        try:
            receipt = self._worker.submit("load-knowledge", self._run_startup_reload)
            logger.info(
                "knowledge startup queued: job_id=%s",
                getattr(receipt, "job_id", "unknown"),
            )
        except Exception:
            with self._lock:
                self._reload_previous_state = None
                self._startup_reload_pending = False
                self._state = KnowledgeState.ERROR
            raise

    def search(
        self, query: str, *, collection: str, category: str | None, top_k: int, cancellation: CancellationSignal
    ) -> tuple[RetrievalResult, ...]:
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("retrieval_busy")
        try:
            if cancellation.is_cancelled:
                raise InterruptedError
            if self._state not in {KnowledgeState.READY, KnowledgeState.DEGRADED}:
                logger.warning(
                    "retrieval unavailable: state=%s collection=%s category=%s top_k=%s",
                    self._state,
                    collection,
                    category,
                    top_k,
                )
                raise RuntimeError("retrieval_unavailable")
            return tuple(RetrievalResult(hit.content, hit.metadata) for hit in self._index.search(
                query, collection=collection, category=category, top_k=top_k, cancellation=cancellation
            ))
        finally:
            self._lock.release()

    def reload(self, target: str | None = None) -> ReloadReport:
        if not self._lock.acquire(blocking=False):
            return ReloadReport(busy=True)
        try:
            self._ensure_open()
            starting = self._startup_reload_pending
            previous_state = (
                self._reload_previous_state if starting else self._state
            )
            self._reload_previous_state = None
            self._startup_reload_pending = False
            logger.info("knowledge reload started: target=%s startup=%s", target, starting)
            self._state = KnowledgeState.LOADING
            if not starting:
                self._reload_cancellation.reset()
            logger.info("knowledge index prepare started: target=%s", target)
            self._index.prepare(self._reload_cancellation)
            logger.info("knowledge index prepare completed: target=%s", target)
            manifest = self._manifests.load()
            observed_pairs = tuple(
                (source, repository)
                for repository in self._sources
                for source in repository.scan(target)
                if target is None or target in source.source_key
            )
            observed = tuple(source for source, _ in observed_pairs)
            logger.info(
                "knowledge sources scanned: target=%s observed=%s manifest_entries=%s",
                target,
                len(observed),
                len(manifest.entries),
            )
            comparison_manifest = (
                manifest
                if target is None
                else IndexManifest(
                    manifest.schema_version,
                    tuple(
                        entry
                        for entry in manifest.entries
                        if target in entry.source_key
                    ),
                )
            )
            report = comparison_manifest.diff(observed)
            repositories = {source.source_key: repository for source, repository in observed_pairs}
            failures: list[str] = []
            for source_key in (*report.deleted, *(old for old, _ in report.renamed)):
                entry = next(entry for entry in manifest.entries if entry.source_key == source_key)
                manifest, error = self._delete_entry(manifest, entry, self._reload_cancellation)
                if error:
                    failures.append(error)
            for source_key in report.retried:
                entry = next(entry for entry in manifest.entries if entry.source_key == source_key)
                if entry.pending_operation is PendingIndexOperation.DELETE:
                    if source_key in repositories:
                        error = f"{source_key}: delete finalize pending"
                    else:
                        manifest, error = self._delete_entry(
                            manifest, entry, self._reload_cancellation
                        )
                else:
                    source = next((item for item in observed if item.source_key == source_key), None)
                    if source is None:
                        error = f"missing retry source: {source_key}"
                    else:
                        manifest, error = self._upsert_source(
                            manifest, source, repositories[source_key], self._reload_cancellation
                        )
                if error:
                    failures.append(error)
            for source_key in (*report.added, *report.updated, *(new for _, new in report.renamed)):
                manifest, error = self._upsert_source(
                    manifest,
                    next(source for source in observed if source.source_key == source_key),
                    repositories[source_key],
                    self._reload_cancellation,
                )
                if error:
                    failures.append(error)
            self._state = KnowledgeState.DEGRADED if failures else KnowledgeState.READY
            result = replace(report, failures=tuple(failures))
            logger.info(
                "knowledge reload completed: target=%s state=%s added=%s updated=%s deleted=%s failures=%s",
                target,
                self._state,
                len(result.added),
                len(result.updated),
                len(result.deleted),
                len(result.failures),
            )
            return result
        except InterruptedError as error:
            self._state = previous_state
            message = str(error) or "knowledge index operation cancelled"
            logger.info(
                "knowledge reload cancelled: target=%s startup=%s restored_state=%s reason=%s",
                target,
                starting,
                self._state,
                message,
            )
            return ReloadReport(failures=(message,))
        except Exception as error:
            self._state = KnowledgeState.ERROR
            logger.exception(
                "knowledge reload failed: target=%s state=%s",
                target,
                self._state,
                extra=_FILE_ONLY_LOG,
            )
            return ReloadReport(failures=(str(error),))
        finally:
            self._lock.release()

    def index_document(
        self,
        document: KnowledgeDocument,
        cancellation: CancellationSignal | None = None,
    ) -> ReloadReport:
        if not self._lock.acquire(blocking=False):
            return ReloadReport(busy=True)
        try:
            self._ensure_open()
            manifest, error = self._upsert_document(
                self._manifests.load(), document, cancellation or CancellationToken()
            )
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

    def delete_source(
        self,
        source_key: str,
        *,
        finalize: Callable[[], None] | None = None,
    ) -> ReloadReport:
        if not self._lock.acquire(blocking=False):
            return ReloadReport(busy=True)
        try:
            self._ensure_open()
            manifest = self._manifests.load()
            entry = next((item for item in manifest.entries if item.source_key == source_key), None)
            if entry is None:
                entry = ManifestEntry(
                    source_key=source_key,
                    collection=self._collection_from_source_key(source_key),
                    observed_hash=None,
                    indexed_hash=None,
                    mtime=None,
                )
            _, error = self._delete_entry(
                manifest, entry, CancellationToken(), finalize=finalize
            )
            if error:
                self._state = KnowledgeState.DEGRADED
                return ReloadReport(failures=(error,))
            return ReloadReport(deleted=(source_key,))
        except Exception as error:
            self._state = KnowledgeState.DEGRADED
            return ReloadReport(failures=(str(error),))
        finally:
            self._lock.release()

    def request_cancel(self, reason: str = "Cancelled by user") -> None:
        del reason
        if self._state is KnowledgeState.LOADING:
            self._reload_cancellation.cancel()

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
                issues.append(CloseIssue(name, str(error)))
        self._state = KnowledgeState.CLOSED
        return CloseReport(closed=("knowledge_service",), issues=tuple(issues))

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("KnowledgeService is closed")

    def _run_startup_reload(self, cancellation: CancellationSignal) -> ReloadReport:
        logger.info("knowledge startup reload started")
        registration = cancellation.register(self._reload_cancellation.cancel)
        try:
            report = self.reload()
            logger.info(
                "knowledge startup reload returned: state=%s failures=%s",
                self._state,
                len(report.failures),
            )
            return report
        finally:
            registration.close()

    def _upsert_source(
        self,
        manifest: IndexManifest,
        source: object,
        repository: KnowledgeSourceRepository,
        cancellation: CancellationSignal,
    ) -> tuple[IndexManifest, str | None]:
        try:
            return self._upsert_document(manifest, repository.read(source), cancellation)
        except Exception as error:
            return manifest, f"{source.source_key}: {error}"

    def _upsert_document(
        self,
        manifest: IndexManifest,
        document: KnowledgeDocument,
        cancellation: CancellationSignal,
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
            self._index.replace_source(source, chunks, cancellation)
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
        self,
        manifest: IndexManifest,
        entry: ManifestEntry,
        cancellation: CancellationSignal,
        *,
        finalize: Callable[[], None] | None = None,
    ) -> tuple[IndexManifest, str | None]:
        pending = replace(entry, status=ManifestStatus.PENDING, pending_operation=PendingIndexOperation.DELETE, error=None)
        manifest = self._replace_entry(manifest, pending)
        self._manifests.save(manifest)
        try:
            self._index.delete_source(entry.source_key, cancellation=cancellation)
            if finalize is not None:
                finalize()
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
    def _collection_from_source_key(source_key: str) -> KnowledgeCollection:
        collection, separator, _ = source_key.partition("/")
        if not separator:
            raise ValueError(f"invalid knowledge source key: {source_key}")
        return KnowledgeCollection(collection)

    @staticmethod
    def _replace_entry(manifest: IndexManifest, replacement: ManifestEntry) -> IndexManifest:
        entries = tuple(
            replacement if entry.source_key == replacement.source_key else entry
            for entry in manifest.entries
        )
        if all(entry.source_key != replacement.source_key for entry in manifest.entries):
            entries = (*entries, replacement)
        return IndexManifest(manifest.schema_version, entries)
