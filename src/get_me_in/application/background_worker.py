"""A single application-owned non-daemon worker for background R6 jobs."""

from collections.abc import Callable
from queue import Queue
from threading import Lock, Thread

from src.get_me_in.application.app_results import BackgroundJobReceipt, CloseIssue, CloseReport


_STOP = object()
_BackgroundTask = Callable[[], None]


class BackgroundWorker:
    """Serial background execution with deterministic, bounded shutdown."""

    def __init__(self, name: str, shutdown_timeout_seconds: float) -> None:
        if not name:
            raise ValueError("worker name must not be empty")
        if shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be positive")
        self._name = name
        self._shutdown_timeout_seconds = shutdown_timeout_seconds
        self._tasks: Queue[_BackgroundTask | object] = Queue()
        self._lock = Lock()
        self._next_job = 0
        self._closed = False
        self._close_report: CloseReport | None = None
        self._thread = Thread(target=self._run, name=name, daemon=False)
        self._thread.start()

    def submit(self, task_name: str, task: _BackgroundTask) -> BackgroundJobReceipt:
        if not task_name:
            raise ValueError("task name must not be empty")
        with self._lock:
            if self._closed:
                raise RuntimeError("BackgroundWorker is closed")
            self._next_job += 1
            receipt = BackgroundJobReceipt(f"{self._name}-{self._next_job}", task_name)
            self._tasks.put(task)
        return receipt

    def close(self) -> CloseReport:
        with self._lock:
            if self._close_report is not None:
                return self._close_report
            if self._closed:
                return CloseReport()
            self._closed = True
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
            task = self._tasks.get()
            try:
                if task is _STOP:
                    return
                task()
            except Exception:
                # Each submitted operation owns its typed failure result.
                pass
            finally:
                self._tasks.task_done()
