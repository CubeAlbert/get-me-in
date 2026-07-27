"""Local filesystem workspace with root confinement and atomic replacement."""

import hashlib
import fnmatch
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable

from charset_normalizer import from_bytes

from src.get_me_in.ports.workspace import (
    BatchDeleteResult,
    DeleteFailure,
    FileSnapshot,
    RevisionMismatchError,
    SearchMatch,
    TextLine,
    WorkspaceEntry,
    WorkspacePathError,
)


class LocalWorkspace:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def resolve(self, path: Path) -> Path:
        candidate = (self._root / path).resolve() if not path.is_absolute() else path.resolve()
        if not candidate.is_relative_to(self._root):
            raise WorkspacePathError(f"Path escapes workspace: {path}")
        return candidate

    def exists(self, path: Path) -> bool:
        return self.resolve(path).exists()

    def read(self, path: Path) -> FileSnapshot:
        resolved = self.resolve(path)
        content = _read_text(resolved)
        return FileSnapshot(resolved.relative_to(self._root), content, _revision(content))

    def content_hash(self, path: Path) -> str:
        resolved = self.resolve(path)
        if not resolved.is_file():
            raise WorkspacePathError(f"Path is not a file: {path}")
        digest = hashlib.sha256()
        with resolved.open("rb") as source:
            while chunk := source.read(64 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def read_lines(
        self, path: Path, *, offset: int = 0, limit: int | None = None
    ) -> tuple[TextLine, ...]:
        if offset < 0 or limit is not None and limit < 0:
            raise ValueError("offset and limit must not be negative")
        lines = self.read(path).content.splitlines()
        end = None if limit is None else offset + limit
        return tuple(TextLine(index + 1, value) for index, value in enumerate(lines[offset:end], offset))

    def list(self, path: Path = Path(".")) -> tuple[WorkspaceEntry, ...]:
        resolved = self.resolve(path)
        return tuple(
            WorkspaceEntry(item.relative_to(self._root), item.is_dir())
            for item in sorted(resolved.iterdir())
        )

    def search(
        self,
        pattern: str,
        *,
        path: Path = Path("."),
        glob: str = "**/*",
        regex: bool = False,
        max_matches: int | None = None,
    ) -> tuple[SearchMatch, ...]:
        if max_matches is not None and max_matches < 1:
            raise ValueError("max_matches must be positive")
        scope = self.resolve(path)
        candidates = (scope,) if scope.is_file() else sorted(scope.glob(glob))
        matcher = re.compile(pattern) if regex else None
        matches: list[SearchMatch] = []
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                content = _read_text(candidate)
            except UnicodeError:
                continue
            for number, line in enumerate(content.splitlines(), start=1):
                if (matcher.search(line) if matcher else pattern in line):
                    matches.append(SearchMatch(candidate.relative_to(self._root), TextLine(number, line)))
                    if max_matches is not None and len(matches) >= max_matches:
                        return tuple(matches)
        return tuple(matches)

    def find_files(
        self, pattern: str, *, path: Path = Path("."), max_results: int | None = None
    ) -> tuple[Path, ...]:
        if max_results is not None and max_results < 1:
            raise ValueError("max_results must be positive")
        scope = self.resolve(path)
        candidates = (scope,) if scope.is_file() else sorted(scope.rglob("*"))
        results = [
            candidate.relative_to(self._root)
            for candidate in candidates
            if candidate.is_file() and fnmatch.fnmatch(candidate.name, pattern)
        ]
        return tuple(results if max_results is None else results[:max_results])

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

    def delete_many(self, paths: Iterable[Path]) -> BatchDeleteResult:
        deleted: list[Path] = []
        failures: list[DeleteFailure] = []
        for path in paths:
            try:
                resolved = self.resolve(path)
                if resolved.is_dir():
                    resolved.rmdir()
                else:
                    resolved.unlink()
            except (OSError, WorkspacePathError) as error:
                failures.append(DeleteFailure(path, str(error)))
            else:
                deleted.append(path)
        return BatchDeleteResult(tuple(deleted), tuple(failures))

    def move(self, source: Path, destination: Path) -> None:
        source_path = self.resolve(source)
        destination_path = self.resolve(destination)
        if destination_path.exists():
            raise FileExistsError(f"Destination already exists: {destination}")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source_path, destination_path)


def _revision(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    match = from_bytes(raw).best()
    if match is None:
        raise UnicodeError(f"Cannot detect text encoding for {path}")
    return str(match)
