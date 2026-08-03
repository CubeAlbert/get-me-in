"""Atomic JSON-file implementation of the session repository."""

import json
from pathlib import Path
import tempfile

from src.get_me_in.domain.sessions import SessionPreview
from src.get_me_in.domain.messages import MessageRecord, Role
from src.get_me_in.domain.agents import AgentKey


class JsonSessionRepository:
    def __init__(self, root: Path, *, codec: object, session_preview_chars: int) -> None:
        self._root = Path(root)
        self._codec = codec
        self._session_preview_chars = session_preview_chars

    def save(self, snapshot: object) -> None:
        target = self._path(snapshot.session.session_id)
        self._write(target, self._codec.encode(snapshot))

    def dump(self, snapshot: object) -> Path:
        target = self._root / "dumps" / f"{snapshot.session.session_id}.json"
        self._write(target, self._codec.encode(snapshot))
        return target

    def _write(self, target: Path, payload: object) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
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
            if path.name.endswith(".dump.json"):
                continue
            snapshot = self.load(path.stem)
            session = snapshot.session
            previews.append(
                SessionPreview(
                    session.session_id,
                    session.active_agent,
                    session.updated_at,
                    _latest_user_preview(session, self._session_preview_chars),
                )
            )
        return tuple(sorted(previews, key=lambda item: item.updated_at, reverse=True))

    def close(self) -> None:
        pass

    def _path(self, session_id: str) -> Path:
        if not session_id or Path(session_id).name != session_id:
            raise ValueError("Session id must be a plain file name")
        return self._root / f"{session_id}.json"


def _latest_user_preview(session: object, preview_chars: int) -> str:
    history = session.agents.get(AgentKey.MAIN).history if AgentKey.MAIN in session.agents else ()
    for record in reversed(history):
        if isinstance(record, MessageRecord) and record.role is Role.USER:
            preview = " ".join(record.content.split())
            return f"{preview[:preview_chars - 1]}…" if len(preview) > preview_chars else preview
    return ""
