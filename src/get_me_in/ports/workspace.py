"""Workspace boundary and revision-aware file data contracts."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class WorkspaceError(ValueError):
    """Base error for structured workspace boundary failures."""


class WorkspacePathError(WorkspaceError):
    """Raised when a path escapes the configured workspace root."""


class RevisionMismatchError(WorkspaceError):
    """Raised when an edit is based on a stale file revision."""


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    content: str
    revision: str


@dataclass(frozen=True)
class WorkspaceEntry:
    path: Path
    is_directory: bool


class WorkspacePort(Protocol):
    def resolve(self, path: Path) -> Path: ...
    def read(self, path: Path) -> FileSnapshot: ...
    def list(self, path: Path = Path(".")) -> tuple[WorkspaceEntry, ...]: ...
    def write(self, path: Path, content: str) -> FileSnapshot: ...
    def edit(self, path: Path, expected_revision: str, content: str) -> FileSnapshot: ...
    def delete(self, path: Path) -> None: ...
    def move(self, source: Path, destination: Path) -> None: ...
