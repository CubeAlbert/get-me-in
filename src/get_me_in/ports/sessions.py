"""Persistence boundary for versioned v2 session snapshots."""

from typing import Protocol

from src.get_me_in.domain.sessions import SessionPreview


class SessionRepository(Protocol):
    def save(self, snapshot: object) -> None: ...

    def load(self, session_id: str) -> object: ...

    def list(self) -> tuple[SessionPreview, ...]: ...

    def close(self) -> None: ...
