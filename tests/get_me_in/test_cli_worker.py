"""WorkerRunner tests for the R5 single-worker boundary."""

from threading import Event, Thread
from time import sleep
import unittest
from unittest.mock import patch

from src.get_me_in.application.commands import Continue
from src.get_me_in.application.app_commands import ReloadKnowledge
from src.get_me_in.application.app_results import ApplicationResult
from src.get_me_in.application.events import Progress
from src.get_me_in.cli.worker import WorkerRunner


class WorkerRunnerTests(unittest.TestCase):
    def test_runs_one_application_command_and_returns_event(self) -> None:
        application = _Application(Progress("done"))
        runner = WorkerRunner(application, _Renderer(), poll_interval_seconds=0.1)

        event = runner.run(Continue())

        self.assertEqual(Progress("done"), event)
        self.assertEqual([Continue()], application.commands)

    def test_escape_requests_cancellation_only_through_application(self) -> None:
        application = _Application(Progress("cancelled"), wait_for_cancel=True)
        runner = WorkerRunner(application, _Renderer(), poll_interval_seconds=0.001)

        with patch("src.get_me_in.cli.worker._esc_pressed", side_effect=(True, False)):
            self.assertEqual(Progress("cancelled"), runner.run(Continue()))

        self.assertEqual(["Cancelled by user"], application.cancellations)

    def test_runs_application_command_and_returns_typed_result(self) -> None:
        application = _Application(_Result())
        runner = WorkerRunner(application, _Renderer(), poll_interval_seconds=0.1)

        result = runner.run(ReloadKnowledge("references"))

        self.assertEqual(_Result(), result)
        self.assertEqual([ReloadKnowledge("references")], application.commands)

    def test_rejects_concurrent_runs_and_close_cancels_active_work(self) -> None:
        application = _Application(Progress("done"), wait_for_cancel=True)
        runner = WorkerRunner(application, _Renderer(), poll_interval_seconds=0.001)
        result: list[object] = []
        thread = Thread(target=lambda: result.append(runner.run(Continue())))
        thread.start()
        self.assertTrue(application.started.wait(timeout=1))

        with self.assertRaisesRegex(RuntimeError, "active command"):
            runner.run(Continue())
        runner.close()
        thread.join(timeout=1)

        self.assertFalse(thread.is_alive())
        self.assertEqual(["CLI is closing"], application.cancellations)
        with self.assertRaisesRegex(RuntimeError, "closed"):
            runner.run(Continue())


class _Application:
    def __init__(self, event: Progress | ApplicationResult, wait_for_cancel: bool = False) -> None:
        self.event = event
        self.wait_for_cancel = wait_for_cancel
        self.commands: list[object] = []
        self.cancellations: list[str] = []
        self.started = Event()
        self._cancelled = Event()

    def handle(self, command: object) -> Progress | ApplicationResult:
        self.commands.append(command)
        self.started.set()
        if self.wait_for_cancel:
            self._cancelled.wait(timeout=1)
        return self.event

    def request_cancel(self, reason: str) -> None:
        self.cancellations.append(reason)
        self._cancelled.set()


class _Renderer:
    def status(self, message: str):
        return _Status()


class _Status:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *args: object) -> None:
        return None


class _Result(ApplicationResult):
    pass
