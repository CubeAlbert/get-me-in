"""Standard-library ProcessRunner implementation."""

import subprocess
from pathlib import Path

from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.process import ProcessResult


class SubprocessRunner:
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
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            return ProcessResult(
                None,
                error.stdout or "",
                error.stderr or "",
                timed_out=True,
            )
        if cancellation.is_cancelled:
            return ProcessResult(
                completed.returncode,
                completed.stdout,
                completed.stderr,
                cancelled=True,
            )
        return ProcessResult(completed.returncode, completed.stdout, completed.stderr)
