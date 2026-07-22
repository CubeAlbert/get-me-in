"""Strongly typed application-command and shutdown results."""

from dataclasses import dataclass
from enum import StrEnum

from src.get_me_in.domain.knowledge import ReloadReport
from src.get_me_in.domain.memories import MemoryBuildReceipt


@dataclass(frozen=True)
class ApplicationResult:
    """Base type for results that are not Runtime events."""


@dataclass(frozen=True)
class BackgroundJobReceipt:
    job_id: str
    task_name: str


class BackgroundJobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class BackgroundJobResult:
    job_id: str
    task_name: str
    state: BackgroundJobState
    value: object | None = None
    error: str | None = None


@dataclass(frozen=True)
class KnowledgeReloaded(ApplicationResult):
    report: ReloadReport


@dataclass(frozen=True)
class MemoryBuildScheduled(ApplicationResult):
    receipt: MemoryBuildReceipt


@dataclass(frozen=True)
class TurnFinalizationResult(ApplicationResult):
    snapshot_error: str | None = None
    memory_receipt: MemoryBuildReceipt | None = None
    memory_error: str | None = None


@dataclass(frozen=True)
class CloseIssue:
    resource_name: str
    message: str
    timed_out: bool = False


@dataclass(frozen=True)
class CloseReport:
    closed: tuple[str, ...] = ()
    issues: tuple[CloseIssue, ...] = ()
