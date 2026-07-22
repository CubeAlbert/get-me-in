"""Cancellable standard-library ProcessRunner implementation."""

import subprocess
import time
from pathlib import Path

from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.process import ProcessResult


class SubprocessRunner:
    def __init__(self, *, cancel_grace_seconds: float = 2.0) -> None:
        if cancel_grace_seconds < 0:
            raise ValueError("cancel_grace_seconds must not be negative")
        self._cancel_grace_seconds = cancel_grace_seconds

    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        cancellation: CancellationSignal,
    ) -> ProcessResult:
        if cancellation.is_cancelled:
            return ProcessResult(None, "", "Cancelled before process start", cancelled=True)
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        started = time.monotonic()
        while True:
            try:
                stdout, stderr = process.communicate(timeout=0.05)
                return ProcessResult(process.returncode, stdout, stderr)
            except subprocess.TimeoutExpired:
                if cancellation.is_cancelled:
                    stdout, stderr = self._stop(process)
                    return ProcessResult(process.returncode, stdout, stderr, cancelled=True)
                if time.monotonic() - started >= timeout_seconds:
                    stdout, stderr = self._stop(process)
                    return ProcessResult(process.returncode, stdout, stderr, timed_out=True)

    def _stop(self, process: subprocess.Popen[str]) -> tuple[str, str]:
        process.terminate()
        try:
            return process.communicate(timeout=self._cancel_grace_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.communicate()
