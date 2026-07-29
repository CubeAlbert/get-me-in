"""ProcessRunner contract tests using real short-lived child processes."""

from pathlib import Path
import sys
import threading
import unittest

from src.get_me_in.adapters.subprocess_runner import SubprocessRunner
from src.get_me_in.application.cancellation import CancellationToken


class SubprocessRunnerTests(unittest.TestCase):
    def test_cancelled_before_start_does_not_launch_process(self) -> None:
        token = CancellationToken()
        token.cancel()

        result = SubprocessRunner().run(
            ("unused",), cwd=Path.cwd(), timeout_seconds=1, cancellation=token
        )

        self.assertTrue(result.cancelled)

    def test_returns_stdout_and_exit_code(self) -> None:
        result = SubprocessRunner().run(
            (sys.executable, "-c", "print('ok')"),
            cwd=Path.cwd(),
            timeout_seconds=2,
            cancellation=CancellationToken(),
        )

        self.assertEqual(0, result.exit_code)
        self.assertEqual("ok", result.stdout.strip())

    def test_replaces_invalid_output_without_returning_none(self) -> None:
        result = SubprocessRunner().run(
            (
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'\\x82'); "
                "sys.stderr.buffer.write(b'\\x82')",
            ),
            cwd=Path.cwd(),
            timeout_seconds=2,
            cancellation=CancellationToken(),
        )

        self.assertEqual(0, result.exit_code)
        self.assertIsInstance(result.stdout, str)
        self.assertIsInstance(result.stderr, str)
        self.assertIn("\ufffd", result.stdout)
        self.assertIn("\ufffd", result.stderr)

    def test_cancellation_terminates_an_active_process(self) -> None:
        token = CancellationToken()
        results: list[object] = []
        worker = threading.Thread(
            target=lambda: results.append(
                SubprocessRunner(cancel_grace_seconds=0.1).run(
                    (sys.executable, "-c", "import time; time.sleep(10)"),
                    cwd=Path.cwd(),
                    timeout_seconds=20,
                    cancellation=token,
                )
            )
        )
        worker.start()
        threading.Event().wait(0.1)
        token.cancel()
        worker.join(timeout=2)

        self.assertFalse(worker.is_alive())
        self.assertTrue(results[0].cancelled)
        self.assertIsInstance(results[0].stdout, str)
        self.assertIsInstance(results[0].stderr, str)
