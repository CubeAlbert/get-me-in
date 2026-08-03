"""Synchronous cancellable process execution contract."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.get_me_in.ports.llm import CancellationSignal


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    cancelled: bool = False


class ProcessRunner(Protocol):
    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        cancellation: CancellationSignal,
    ) -> ProcessResult: ...
