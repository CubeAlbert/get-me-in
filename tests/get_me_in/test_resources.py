"""R6 resource ownership and background-worker tests."""

from threading import Event
from time import sleep
import unittest

from src.get_me_in.application.app_results import ApplicationResult, CloseReport
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
        stack = ResourceStack()
        stack.register("after-error", lambda: CloseReport(closed=("after-error",)))
        stack.register("timeout", _timeout)
        stack.register("error", _error)

        report = stack.close()

        self.assertEqual(("after-error",), report.closed)
        self.assertEqual(
            (("error", False), ("timeout", True)),
            tuple((issue.resource_name, issue.timed_out) for issue in report.issues),
        )


class BackgroundWorkerTests(unittest.TestCase):
    def test_runs_submitted_work_serially_and_returns_typed_receipt(self) -> None:
        completed = Event()
        order: list[str] = []
        worker = BackgroundWorker("memory", 1)
        try:
            first = worker.submit("first", lambda: order.append("first"))
            second = worker.submit("second", lambda: (order.append("second"), completed.set()))

            self.assertEqual(("memory-1", "first"), (first.job_id, first.task_name))
            self.assertEqual(("memory-2", "second"), (second.job_id, second.task_name))
            self.assertTrue(completed.wait(timeout=1))
            self.assertEqual(["first", "second"], order)
        finally:
            report = worker.close()

        self.assertEqual(("memory",), report.closed)
        self.assertIs(report, worker.close())

    def test_close_reports_timeout_without_losing_control(self) -> None:
        started = Event()
        release = Event()
        worker = BackgroundWorker("memory", 0.001)
        worker.submit("blocked", lambda: (started.set(), release.wait(timeout=1)))
        self.assertTrue(started.wait(timeout=1))

        report = worker.close()
        release.set()
        sleep(0.01)

        self.assertTrue(report.issues[0].timed_out)


def _error() -> CloseReport:
    raise RuntimeError("broken")


def _timeout() -> CloseReport:
    raise TimeoutError("slow")
