"""Standard-library implementations of system ports."""

from datetime import datetime
from uuid import uuid4


class SystemClock:
    def now(self) -> datetime:
        return datetime.now().astimezone()


class UuidGenerator:
    def new_id(self) -> str:
        return str(uuid4())
