"""R6 resource ownership and background-worker tests."""

from threading import Event
from time import monotonic, sleep
import unittest

from src.get_me_in.application.app_results import (
    ApplicationResult,
    BackgroundJobState,
    CloseReport,
)
from src.get_me_in.application.background_worker import BackgroundWorker
from src.get_me_in.application.resources import ResourceStack


class ResourceStackTests(unittest.TestCase):
    def test_closes_in_reverse_order_and_is_idempotent(self) -> None:
        closed: list[str] = []
        stack = ResourceStack()
        stack.register("first", lambda: closed.append("first") or CloseReport())
        stack.register("second", lambda: closed.append("second") or CloseReport())

        first = stack.close()

        self.assertEqual(["second", "first"], closed)
        self.assertEqual(("second", "first"), first.closed)
        self.assertIs(first, stack.close())

    def test_close_isolates_error_and_timeout(self) -> None:
        closed: list[str] = []
        stack = ResourceStack()
        stack.register("after-timeout", lambda: closed.append("unsafe"))
        stack.register("timeout", _timeout)
        stack.register("error", _error)

        report = stack.close()

        self.assertEqual((), report.closed)
        self.assertEqual([], closed)
        self.assertEqual(
            (("error", False), ("timeout", True)),
            tuple((issue.resource_name, issue.timed_out) for issue in report.issues),
        )


class BackgroundWorkerTests(unittest.TestCase):
    def test_does_not_start_thread_until_first_submission(self) -> None:
        worker = BackgroundWorker("lazy-memory", 1)
        try:
            self.assertFalse(worker._thread.is_alive())
        finally:
            report = worker.close()

        self.assertEqual(("lazy-memory",), report.closed)

    def test_runs_submitted_work_serially_and_returns_typed_receipt(self) -> None:
        completed = Event()
        order: list[str] = []
        worker = BackgroundWorker("memory", 1)
        try:
            first = worker.submit("first", lambda _: order.append("first"))
            second = worker.submit("second", lambda _: (order.append("second"), completed.set()))

            self.assertEqual(("memory-1", "first"), (first.job_id, first.task_name))
            self.assertEqual(("memory-2", "second"), (second.job_id, second.task_name))
            self.assertTrue(completed.wait(timeout=1))
            self.assertEqual(["first", "second"], order)
            result = _wait_for_job(worker, second.job_id)
            self.assertEqual(BackgroundJobState.SUCCEEDED, result.state)
        finally:
            report = worker.close()

        self.assertEqual(("memory",), report.closed)
        self.assertIs(report, worker.close())

    def test_job_prefix_can_identify_a_logical_task_on_shared_worker(self) -> None:
        worker = BackgroundWorker("knowledge-memory", 1)
        try:
            worker.submit("load-knowledge", lambda _: None)
            receipt = worker.submit("build-memory", lambda _: None, job_prefix="memory-build")
            self.assertEqual("memory-build-1", receipt.job_id)
        finally:
            worker.close()

    def test_close_reports_timeout_without_losing_control(self) -> None:
        started = Event()
        release = Event()
        worker = BackgroundWorker("memory", 0.001)
        worker.submit("blocked", lambda _: (started.set(), release.wait(timeout=1)))
        self.assertTrue(started.wait(timeout=1))

        report = worker.close()
        release.set()
        sleep(0.01)

        self.assertTrue(report.issues[0].timed_out)

    def test_job_failure_is_retained_as_typed_result(self) -> None:
        worker = BackgroundWorker("memory", 1)
        receipt = worker.submit("broken", lambda _: _raise_job_error())
        result = _wait_for_job(worker, receipt.job_id)
        worker.close()

        self.assertEqual(BackgroundJobState.FAILED, result.state)
        self.assertEqual("job failed", result.error)

    def test_close_cooperatively_cancels_running_job(self) -> None:
        started = Event()
        worker = BackgroundWorker("memory", 1)

        def wait_for_cancel(cancellation):
            started.set()
            while not cancellation.is_cancelled:
                sleep(0.001)
            raise InterruptedError("cancelled")

        receipt = worker.submit("cancel", wait_for_cancel)
        self.assertTrue(started.wait(timeout=1))
        report = worker.close()
        result = worker.result(receipt.job_id)

        self.assertEqual(("memory",), report.closed)
        self.assertEqual(BackgroundJobState.CANCELLED, result.state)


def _error() -> CloseReport:
    raise RuntimeError("broken")


def _timeout() -> CloseReport:
    raise TimeoutError("slow")


def _raise_job_error() -> None:
    raise RuntimeError("job failed")


def _wait_for_job(worker: BackgroundWorker, job_id: str):
    deadline = monotonic() + 1
    while monotonic() < deadline:
        result = worker.result(job_id)
        if result is not None and result.state in {
            BackgroundJobState.SUCCEEDED,
            BackgroundJobState.FAILED,
            BackgroundJobState.CANCELLED,
        }:
            return result
        sleep(0.001)
    raise AssertionError(f"background job did not finish: {job_id}")
