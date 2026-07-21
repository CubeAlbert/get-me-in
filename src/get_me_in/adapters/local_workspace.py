"""Local filesystem workspace with root confinement and atomic replacement."""

import hashlib
import os
import tempfile
from pathlib import Path

from src.get_me_in.ports.workspace import (
    FileSnapshot,
    RevisionMismatchError,
    WorkspaceEntry,
    WorkspacePathError,
)


class LocalWorkspace:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def resolve(self, path: Path) -> Path:
        candidate = (self._root / path).resolve() if not path.is_absolute() else path.resolve()
        if not candidate.is_relative_to(self._root):
            raise WorkspacePathError(f"Path escapes workspace: {path}")
        return candidate

    def read(self, path: Path) -> FileSnapshot:
        resolved = self.resolve(path)
        content = resolved.read_text(encoding="utf-8")
        return FileSnapshot(resolved.relative_to(self._root), content, _revision(content))

    def list(self, path: Path = Path(".")) -> tuple[WorkspaceEntry, ...]:
        resolved = self.resolve(path)
        return tuple(
            WorkspaceEntry(item.relative_to(self._root), item.is_dir())
            for item in sorted(resolved.iterdir())
        )

    def write(self, path: Path, content: str) -> FileSnapshot:
        resolved = self.resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=resolved.parent, delete=False
        ) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, resolved)
        return FileSnapshot(resolved.relative_to(self._root), content, _revision(content))

    def edit(self, path: Path, expected_revision: str, content: str) -> FileSnapshot:
        current = self.read(path)
        if current.revision != expected_revision:
            raise RevisionMismatchError(f"Stale revision for {path}")
        return self.write(path, content)

    def delete(self, path: Path) -> None:
        resolved = self.resolve(path)
        if resolved.is_dir():
            raise WorkspacePathError("Directory deletion is not supported by this operation")
        resolved.unlink()

    def move(self, source: Path, destination: Path) -> None:
        source_path = self.resolve(source)
        destination_path = self.resolve(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source_path, destination_path)


def _revision(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
