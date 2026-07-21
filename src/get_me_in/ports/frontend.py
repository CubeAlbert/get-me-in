"""Frontend boundary for user-visible operating-system actions."""

from pathlib import Path
from typing import Protocol


class FrontendPort(Protocol):
    def open_file(self, path: Path) -> None: ...
