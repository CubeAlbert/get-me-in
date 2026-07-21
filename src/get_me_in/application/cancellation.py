"""Instance-scoped cancellation state."""

from threading import Event


class CancellationToken:
    """Cancellation signal owned by one Application instance."""

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    def reset(self) -> None:
        self._event.clear()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()
