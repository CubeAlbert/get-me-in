"""Instance-scoped cancellation state with active-call callbacks."""

from collections.abc import Callable
from threading import Event, Lock


class CancellationRegistration:
    def __init__(self, token: "CancellationToken", key: int) -> None:
        self._token = token
        self._key = key

    def close(self) -> None:
        token, self._token = self._token, None
        if token is not None:
            token._unregister(self._key)


class CancellationToken:
    """Thread-safe signal owned by one Application instance."""

    def __init__(self) -> None:
        self._event = Event()
        self._lock = Lock()
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._next_key = 0

    def cancel(self) -> None:
        with self._lock:
            self._event.set()
            callbacks = tuple(self._callbacks.values())
        for callback in callbacks:
            try:
                callback()
            except Exception:
                pass

    def reset(self) -> None:
        self._event.clear()

    def register(self, callback: Callable[[], None]) -> CancellationRegistration:
        with self._lock:
            self._next_key += 1
            key = self._next_key
            self._callbacks[key] = callback
            cancelled = self._event.is_set()
        if cancelled:
            callback()
        return CancellationRegistration(self, key)

    def _unregister(self, key: int) -> None:
        with self._lock:
            self._callbacks.pop(key, None)

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()
