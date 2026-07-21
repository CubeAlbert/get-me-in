"""Explicit user-authorized external-file access boundary."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ExternalFileContent:
    path: Path
    format: str
    text: str


class ExternalFileReaderPort(Protocol):
    def read(self, path: Path) -> ExternalFileContent: ...
