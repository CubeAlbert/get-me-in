"""Background memory build orchestration without a duplicate search API."""

from src.get_me_in.application.app_results import CloseIssue, CloseReport
from src.get_me_in.domain.memories import MemoryBuildReceipt, MemoryBuildReport, MemoryBuildSource
from src.get_me_in.ports.llm import CancellationSignal


class MemoryService:
    def __init__(self, repository: object, extractor: object, knowledge: object, worker: object) -> None:
        self._repository, self._extractor, self._knowledge, self._worker = repository, extractor, knowledge, worker

    def build_async(self, source: MemoryBuildSource) -> MemoryBuildReceipt:
        receipt = self._worker.submit(
            "build-memory", lambda cancellation: self._build(source, cancellation)
        )
        return MemoryBuildReceipt(receipt.job_id, source.session_id)

    def delete(self, memory_id: str) -> MemoryBuildReport:
        try:
            report = self._knowledge.delete_source(
                f"memories/{memory_id}.json",
                finalize=lambda: self._repository.delete(memory_id),
            )
            if report.failures:
                return MemoryBuildReport("", deleted_memory_id=memory_id, error="; ".join(report.failures))
            return MemoryBuildReport("", deleted_memory_id=memory_id)
        except Exception as error:
            return MemoryBuildReport("", deleted_memory_id=memory_id, error=str(error))

    def close(self) -> CloseReport:
        issues: list[CloseIssue] = []
        close_extractor = getattr(self._extractor, "close", None)
        for name, close in (
            ("memory_extractor", close_extractor),
            ("memory_repository", self._repository.close),
        ):
            if close is None:
                continue
            try:
                close()
            except Exception as error:
                issues.append(CloseIssue(name, str(error)))
        return CloseReport(closed=("memory_service",), issues=tuple(issues))

    def _build(
        self, source: MemoryBuildSource, cancellation: CancellationSignal
    ) -> MemoryBuildReport:
        created: list[str] = []
        try:
            records = self._extractor.extract(source, cancellation)
            for record in records:
                if cancellation.is_cancelled:
                    raise InterruptedError("memory build cancelled")
                document = self._repository.write(record)
                created.append(record.memory_id)
                report = self._knowledge.index_document(document, cancellation)
                if report.busy:
                    return MemoryBuildReport(
                        source.session_id,
                        tuple(created),
                        error=f"knowledge index busy for memory {record.memory_id}",
                    )
                if report.failures:
                    return MemoryBuildReport(
                        source.session_id,
                        tuple(created),
                        error="; ".join(report.failures),
                    )
            return MemoryBuildReport(source.session_id, tuple(created))
        except InterruptedError:
            raise
        except Exception as error:
            return MemoryBuildReport(source.session_id, tuple(created), error=str(error))
