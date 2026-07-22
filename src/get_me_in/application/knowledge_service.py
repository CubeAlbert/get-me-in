"""Explicit, serial knowledge lifecycle service using injected ports."""

from threading import Lock

from src.get_me_in.application.app_results import CloseReport
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.background_worker import BackgroundWorker
from src.get_me_in.domain.knowledge import KnowledgeDocument, KnowledgeState, ReloadReport
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
            observed = tuple(source for repository in self._sources for source in repository.scan(target))
            report = manifest.diff(observed)
            self._state = KnowledgeState.READY
            return report
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
            self._index.replace_source(document.source, self._chunker.chunk(document), self._cancellation)
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
