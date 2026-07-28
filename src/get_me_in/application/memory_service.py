"""Background memory build orchestration without a duplicate search API."""

import logging

from src.get_me_in.application.app_results import CloseIssue, CloseReport
from src.get_me_in.domain.memories import MemoryBuildReceipt, MemoryBuildReport, MemoryBuildSource
from src.get_me_in.ports.llm import CancellationSignal

logger = logging.getLogger(__name__)
_MEMORY_JOB_PREFIX = "memory-build"
_FILE_ONLY_LOG = {"_get_me_in_file_only": True}
_USER_ERROR = "Error: memory build failed; details were written to app.log"


class MemoryService:
    def __init__(self, repository: object, extractor: object, knowledge: object, worker: object) -> None:
        self._repository, self._extractor, self._knowledge, self._worker = repository, extractor, knowledge, worker

    def build_async(self, source: MemoryBuildSource) -> MemoryBuildReceipt:
        receipt = self._worker.submit(
            "build-memory",
            lambda cancellation: self._build(source, cancellation),
            job_prefix=_MEMORY_JOB_PREFIX,
        )
        logger.info(
            "memory build scheduled: job_id=%s session_id=%s agent=%s records=%d",
            receipt.job_id,
            source.session_id,
            source.agent_key,
            len(source.records),
        )
        return MemoryBuildReceipt(receipt.job_id, source.session_id, source.agent_key)

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
        logger.info(
            "memory build started: session_id=%s agent=%s records=%d",
            source.session_id,
            source.agent_key,
            len(source.records),
        )
        try:
            records = self._extractor.extract(source, cancellation)
            for record in records:
                if cancellation.is_cancelled:
                    raise InterruptedError("memory build cancelled")
                document = self._repository.write(record)
                created.append(record.memory_id)
                report = self._knowledge.index_document(document, cancellation)
                if report.busy:
                    failure = MemoryBuildReport(
                        source.session_id,
                        tuple(created),
                        error=f"knowledge index busy for memory {record.memory_id}",
                    )
                    logger.error(
                        "memory build failed: session_id=%s agent=%s error=%s",
                        source.session_id,
                        source.agent_key,
                        failure.error,
                    )
                    return failure
                if report.failures:
                    failure = MemoryBuildReport(
                        source.session_id,
                        tuple(created),
                        error="; ".join(report.failures),
                    )
                    logger.error(
                        "memory build failed: session_id=%s agent=%s error=%s",
                        source.session_id,
                        source.agent_key,
                        failure.error,
                    )
                    return failure
            report = MemoryBuildReport(source.session_id, tuple(created))
            logger.info(
                "memory build completed: session_id=%s agent=%s created=%d",
                source.session_id,
                source.agent_key,
                len(created),
            )
            return report
        except InterruptedError:
            logger.warning(
                "memory build cancelled: session_id=%s agent=%s created=%d",
                source.session_id,
                source.agent_key,
                len(created),
            )
            raise
        except Exception as error:
            logger.exception(
                "memory build failed: session_id=%s agent=%s created=%d",
                source.session_id,
                source.agent_key,
                len(created),
                extra=_FILE_ONLY_LOG,
            )
            logger.error(_USER_ERROR)
            return MemoryBuildReport(source.session_id, tuple(created), error=_USER_ERROR)
