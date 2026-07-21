"""Tests for timeout and cancellation-safe process results."""

import sys
import tempfile
import unittest
from pathlib import Path

from src.get_me_in.adapters.subprocess_runner import SubprocessRunner
from src.get_me_in.application.cancellation import CancellationToken


class SubprocessRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.cwd = Path(self.temporary_dir.name)

    def test_returns_stdout_and_exit_code(self) -> None:
        result = SubprocessRunner().run(
            (sys.executable, "-c", "print('ok')"),
            cwd=self.cwd,
            timeout_seconds=5,
            cancellation=CancellationToken(),
        )

        self.assertEqual(0, result.exit_code)
        self.assertEqual("ok", result.stdout.strip())

    def test_cancelled_before_start_does_not_launch_process(self) -> None:
        cancellation = CancellationToken()
        cancellation.cancel()

        result = SubprocessRunner().run(
            (sys.executable, "-c", "raise SystemExit(1)"),
            cwd=self.cwd,
            timeout_seconds=5,
            cancellation=cancellation,
        )

        self.assertTrue(result.cancelled)
        self.assertIsNone(result.exit_code)
