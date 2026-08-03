"""A single application-owned non-daemon worker for background R6 jobs."""

from collections.abc import Callable
import logging
from queue import Queue
from threading import Lock, Thread

from src.get_me_in.application.app_results import (
    BackgroundJobReceipt,
    BackgroundJobResult,
    BackgroundJobState,
    CloseIssue,
    CloseReport,
)
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.ports.llm import CancellationSignal


_STOP = object()
_BackgroundTask = Callable[[CancellationSignal], object]
_QueuedTask = tuple[str, str, _BackgroundTask, CancellationToken]
logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Serial background execution with deterministic, bounded shutdown."""

    def __init__(self, name: str, shutdown_timeout_seconds: float) -> None:
        if not name:
            raise ValueError("worker name must not be empty")
        if shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be positive")
        self._name = name
        self._shutdown_timeout_seconds = shutdown_timeout_seconds
        self._tasks: Queue[_QueuedTask | object] = Queue()
        self._lock = Lock()
        self._next_jobs: dict[str, int] = {}
        self._closed = False
        self._close_report: CloseReport | None = None
        self._results: dict[str, BackgroundJobResult] = {}
        self._tokens: dict[str, CancellationToken] = {}
        self._thread = Thread(target=self._run, name=name, daemon=False)
        self._started = False

    def submit(
        self,
        task_name: str,
        task: _BackgroundTask,
        *,
        job_prefix: str | None = None,
    ) -> BackgroundJobReceipt:
        if not task_name:
            raise ValueError("task name must not be empty")
        if job_prefix is not None and not job_prefix:
            raise ValueError("job prefix must not be empty")
        with self._lock:
            if self._closed:
                raise RuntimeError("BackgroundWorker is closed")
            prefix = job_prefix or self._name
            next_job = self._next_jobs.get(prefix, 0) + 1
            self._next_jobs[prefix] = next_job
            receipt = BackgroundJobReceipt(f"{prefix}-{next_job}", task_name)
            cancellation = CancellationToken()
            self._tokens[receipt.job_id] = cancellation
            self._results[receipt.job_id] = BackgroundJobResult(
                receipt.job_id, task_name, BackgroundJobState.QUEUED
            )
            self._tasks.put((receipt.job_id, task_name, task, cancellation))
            if not self._started:
                self._thread.start()
                self._started = True
        logger.info(
            "background job queued: worker=%s job_id=%s task=%s",
            self._name,
            receipt.job_id,
            task_name,
        )
        return receipt

    def result(self, job_id: str) -> BackgroundJobResult | None:
        with self._lock:
            return self._results.get(job_id)

    def close(self) -> CloseReport:
        with self._lock:
            if self._close_report is not None:
                return self._close_report
            if self._closed:
                return CloseReport()
            self._closed = True
            if not self._started:
                self._close_report = CloseReport(closed=(self._name,))
                return self._close_report
            for cancellation in self._tokens.values():
                cancellation.cancel()
            self._tasks.put(_STOP)
        self._thread.join(self._shutdown_timeout_seconds)
        if self._thread.is_alive():
            self._close_report = CloseReport(
                issues=(CloseIssue(self._name, "background worker did not stop before timeout", timed_out=True),)
            )
        else:
            self._close_report = CloseReport(closed=(self._name,))
        return self._close_report

    def _run(self) -> None:
        while True:
            queued = self._tasks.get()
            try:
                if queued is _STOP:
                    return
                job_id, task_name, task, cancellation = queued
                if cancellation.is_cancelled:
                    logger.warning(
                        "background job cancelled before execution: worker=%s job_id=%s task=%s",
                        self._name,
                        job_id,
                        task_name,
                    )
                    self._set_result(
                        BackgroundJobResult(
                            job_id,
                            task_name,
                            BackgroundJobState.CANCELLED,
                            error="background job cancelled before execution",
                        )
                    )
                    continue
                logger.info(
                    "background job started: worker=%s job_id=%s task=%s",
                    self._name,
                    job_id,
                    task_name,
                )
                self._set_result(
                    BackgroundJobResult(job_id, task_name, BackgroundJobState.RUNNING)
                )
                value = task(cancellation)
                error = getattr(value, "error", None)
                failures = getattr(value, "failures", ())
                if error is None and failures:
                    error = "; ".join(str(item) for item in failures)
                state = (
                    BackgroundJobState.CANCELLED
                    if cancellation.is_cancelled
                    else BackgroundJobState.FAILED
                    if error
                    else BackgroundJobState.SUCCEEDED
                )
                self._set_result(
                    BackgroundJobResult(job_id, task_name, state, value, error)
                )
            except InterruptedError as error:
                self._set_result(
                    BackgroundJobResult(
                        job_id,
                        task_name,
                        BackgroundJobState.CANCELLED,
                        error=str(error) or "background job cancelled",
                    )
                )
            except Exception as error:
                logger.exception(
                    "background job raised an exception: worker=%s job_id=%s task=%s",
                    self._name,
                    job_id,
                    task_name,
                )
                self._set_result(
                    BackgroundJobResult(
                        job_id,
                        task_name,
                        BackgroundJobState.FAILED,
                        error=str(error),
                    )
                )
            finally:
                self._tasks.task_done()

    def _set_result(self, result: BackgroundJobResult) -> None:
        with self._lock:
            self._results[result.job_id] = result
            if result.state in {
                BackgroundJobState.SUCCEEDED,
                BackgroundJobState.FAILED,
                BackgroundJobState.CANCELLED,
            }:
                self._tokens.pop(result.job_id, None)
                log = logger.error if result.state is BackgroundJobState.FAILED else logger.info
                log(
                    "background job finished: worker=%s job_id=%s task=%s state=%s error=%s",
                    self._name,
                    result.job_id,
                    result.task_name,
                    result.state,
                    result.error or "",
                )
