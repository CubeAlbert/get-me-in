"""Background memory build orchestration without a duplicate search API."""

from src.get_me_in.application.app_results import CloseReport
from src.get_me_in.domain.memories import MemoryBuildReceipt, MemoryBuildReport, MemoryBuildSource


class MemoryService:
    def __init__(self, repository: object, extractor: object, knowledge: object, worker: object) -> None:
        self._repository, self._extractor, self._knowledge, self._worker = repository, extractor, knowledge, worker

    def build_async(self, source: MemoryBuildSource) -> MemoryBuildReceipt:
        receipt = self._worker.submit("build-memory", lambda: self._build(source))
        return MemoryBuildReceipt(receipt.job_id, source.session_id)

    def delete(self, memory_id: str) -> MemoryBuildReport:
        try:
            report = self._knowledge.delete_source(f"memories/{memory_id}.json")
            if report.failures:
                return MemoryBuildReport("", deleted_memory_id=memory_id, error="; ".join(report.failures))
            self._repository.delete(memory_id)
            return MemoryBuildReport("", deleted_memory_id=memory_id)
        except Exception as error:
            return MemoryBuildReport("", deleted_memory_id=memory_id, error=str(error))

    def close(self) -> CloseReport:
        self._repository.close()
        close = getattr(self._extractor, "close", None)
        if close is not None:
            close()
        return CloseReport(closed=("memory_service",))

    def _build(self, source: MemoryBuildSource) -> None:
        from src.get_me_in.application.cancellation import CancellationToken
        for record in self._extractor.extract(source, CancellationToken()):
            self._knowledge.index_document(self._repository.write(record))
