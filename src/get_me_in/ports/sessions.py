"""Minimal session persistence lifecycle port; snapshot methods arrive in R4."""

from typing import Protocol


class SessionRepository(Protocol):
    def close(self) -> None: ...
