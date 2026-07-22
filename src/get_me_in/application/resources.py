"""Application-owned, reverse-order resource lifecycle management."""

from collections.abc import Callable

from src.get_me_in.application.app_results import CloseIssue, CloseReport


class ResourceStack:
    """Close top-level owners once, in reverse registration order."""

    def __init__(self) -> None:
        self._resources: list[tuple[str, Callable[[], CloseReport | None]]] = []
        self._closed = False
        self._report: CloseReport | None = None

    def register(self, name: str, close: Callable[[], CloseReport | None]) -> None:
        if self._closed:
            raise RuntimeError("ResourceStack is closed")
        if not name:
            raise ValueError("resource name must not be empty")
        if any(existing_name == name for existing_name, _ in self._resources):
            raise ValueError(f"resource already registered: {name}")
        self._resources.append((name, close))

    def close(self) -> CloseReport:
        if self._report is not None:
            return self._report
        self._closed = True
        closed: list[str] = []
        issues: list[CloseIssue] = []
        for name, closer in reversed(self._resources):
            try:
                report = closer()
                closed.append(name)
                if report is not None:
                    issues.extend(report.issues)
            except TimeoutError as error:
                issues.append(CloseIssue(name, str(error), timed_out=True))
            except Exception as error:
                issues.append(CloseIssue(name, str(error)))
        self._report = CloseReport(tuple(closed), tuple(issues))
        return self._report
