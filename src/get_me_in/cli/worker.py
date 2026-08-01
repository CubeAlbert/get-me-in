"""One cancellable worker for synchronous Application commands."""

from contextlib import nullcontext
from queue import Queue
import sys
from threading import Lock, Thread
from time import sleep
from typing import Any

from src.get_me_in.application.app_commands import ApplicationCommand
from src.get_me_in.application.app_results import ApplicationResult
from src.get_me_in.application.commands import RuntimeCommand
from src.get_me_in.application.events import RuntimeEvent


class WorkerRunner:
    """Serializes blocking Application calls and forwards cancellation publicly."""

    def __init__(self, application: object, renderer: object, *, poll_interval_seconds: float) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        self._application = application
        self._renderer = renderer
        self._poll_interval_seconds = poll_interval_seconds
        self._run_lock = Lock()
        self._closed = False

    def run(self, command: RuntimeCommand | ApplicationCommand) -> RuntimeEvent | ApplicationResult:
        """Run one command in the only worker, polling Esc and Ctrl+C for cancellation."""
        if self._closed:
            raise RuntimeError("WorkerRunner is closed")
        if not self._run_lock.acquire(blocking=False):
            raise RuntimeError("WorkerRunner already has an active command")
        results: Queue[RuntimeEvent | ApplicationResult | BaseException] = Queue(maxsize=1)
        worker = Thread(target=self._handle, args=(command, results), daemon=True)
        cancelled = False
        try:
            with _status(self._renderer, "处理中"):
                worker.start()
                while worker.is_alive():
                    try:
                        if not cancelled and _esc_pressed():
                            self._application.request_cancel("Cancelled by user")
                            cancelled = True
                        worker.join(self._poll_interval_seconds)
                    except KeyboardInterrupt:
                        if not cancelled:
                            self._application.request_cancel("Cancelled by user")
                            cancelled = True
            result = results.get()
            if isinstance(result, BaseException):
                raise result
            return result
        finally:
            self._run_lock.release()

    def close(self) -> None:
        """Prevent future runs and ask a currently active Application call to stop."""
        self._closed = True
        if self._run_lock.locked():
            self._application.request_cancel("CLI is closing")

    def _handle(
        self,
        command: RuntimeCommand | ApplicationCommand,
        results: Queue[RuntimeEvent | ApplicationResult | BaseException],
    ) -> None:
        try:
            result = self._application.handle(command)
            if not isinstance(result, (RuntimeEvent, ApplicationResult)):
                raise TypeError("Application.handle(command) must return RuntimeEvent or ApplicationResult")
            results.put(result)
        except BaseException as error:
            results.put(error)


def _status(renderer: object, message: str) -> Any:
    status = getattr(renderer, "status", None)
    return status(message) if status is not None else nullcontext()


def _esc_pressed() -> bool:
    """Consume an Esc key only on Windows; other keyboard handling stays frontend-owned."""
    if sys.platform != "win32":
        return False
    import msvcrt

    while msvcrt.kbhit():
        if msvcrt.getch() == b"\x1b":
            return True
    return False
