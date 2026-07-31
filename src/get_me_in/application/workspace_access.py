"""Session-scoped read authorization for revision-aware workspace edits."""

from pathlib import Path
from threading import Lock

from src.get_me_in.ports.workspace import RevisionMismatchError


class WorkspaceAccessState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._revisions: dict[tuple[str, Path], str] = {}

    def authorize_read(self, session_id: str, path: Path, revision: str) -> None:
        with self._lock:
            self._revisions[(session_id, Path(path))] = revision

    def require_revision(self, session_id: str, path: Path, revision: str) -> None:
        with self._lock:
            authorized = self._revisions.get((session_id, Path(path)))
        if authorized != revision:
            raise RevisionMismatchError(
                f"Session {session_id} must read {path} before editing its current revision"
            )

    def consume_revision(self, session_id: str, path: Path, revision: str) -> None:
        key = (session_id, Path(path))
        with self._lock:
            authorized = self._revisions.get(key)
            if authorized != revision:
                raise RevisionMismatchError(
                    f"Session {session_id} must read {path} before editing its current revision"
                )
            del self._revisions[key]

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._revisions = {
                key: value for key, value in self._revisions.items() if key[0] != session_id
            }
