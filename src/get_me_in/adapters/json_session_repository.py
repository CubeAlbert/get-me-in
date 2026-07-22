"""Atomic JSON-file implementation of the v2 session repository."""

import json
from pathlib import Path
import tempfile

from src.get_me_in.domain.sessions import SessionPreview


class JsonSessionRepository:
    def __init__(self, root: Path, *, codec: object) -> None:
        self._root = Path(root)
        self._codec = codec

    def save(self, snapshot: object) -> None:
        target = self._path(snapshot.session.session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self._codec.encode(snapshot)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
            handle.flush()
        try:
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def load(self, session_id: str) -> object:
        path = self._path(session_id)
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return self._codec.decode(payload)

    def list(self) -> tuple[SessionPreview, ...]:
        if not self._root.exists():
            return ()
        previews = []
        for path in self._root.glob("*.json"):
            snapshot = self.load(path.stem)
            session = snapshot.session
            previews.append(SessionPreview(session.session_id, session.active_agent, session.updated_at))
        return tuple(sorted(previews, key=lambda item: item.updated_at, reverse=True))

    def close(self) -> None:
        pass

    def _path(self, session_id: str) -> Path:
        if not session_id or Path(session_id).name != session_id:
            raise ValueError("Session id must be a plain file name")
        return self._root / f"{session_id}.json"
