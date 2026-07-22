"""Immutable knowledge-index contracts and manifest change detection."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class KnowledgeCollection(StrEnum):
    """The v2 collections exposed through the existing retrieval contract."""

    REFERENCES = "references"
    MEMORIES = "memories"


class KnowledgeState(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    DEGRADED = "degraded"
    ERROR = "error"
    CLOSING = "closing"
    CLOSED = "closed"


class ManifestStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    ERROR = "error"


class PendingIndexOperation(StrEnum):
    UPSERT = "upsert"
    DELETE = "delete"


@dataclass(frozen=True)
class KnowledgeSource:
    """Observed source metadata; document content is loaded separately."""

    collection: KnowledgeCollection
    source_key: str
    content_hash: str
    mtime: datetime


@dataclass(frozen=True)
class KnowledgeDocument:
    source: KnowledgeSource
    content: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IndexChunk:
    chunk_id: str
    source_key: str
    collection: KnowledgeCollection
    content: str
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class IndexHit:
    chunk_id: str
    content: str
    metadata: Mapping[str, object]
    score: float


@dataclass(frozen=True)
class ManifestEntry:
    source_key: str
    collection: KnowledgeCollection
    observed_hash: str | None
    indexed_hash: str | None
    mtime: datetime | None
    chunk_ids: tuple[str, ...] = ()
    status: ManifestStatus = ManifestStatus.READY
    pending_operation: PendingIndexOperation | None = None
    error: str | None = None


@dataclass(frozen=True)
class ReloadReport:
    """A deterministic scan result, not a report of completed index work."""

    added: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    deleted: tuple[str, ...] = ()
    renamed: tuple[tuple[str, str], ...] = ()
    retried: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()


@dataclass(frozen=True)
class IndexManifest:
    schema_version: int
    entries: tuple[ManifestEntry, ...] = ()

    def __post_init__(self) -> None:
        source_keys = tuple(entry.source_key for entry in self.entries)
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("IndexManifest entries must have unique source_key values")

    def diff(self, observed_sources: tuple[KnowledgeSource, ...]) -> ReloadReport:
        """Compare an observed scan with this manifest without changing either input."""
        observed_keys = tuple(source.source_key for source in observed_sources)
        if len(observed_keys) != len(set(observed_keys)):
            raise ValueError("observed_sources must have unique source_key values")

        observed_by_key = {source.source_key: source for source in observed_sources}
        entries_by_key = {entry.source_key: entry for entry in self.entries}
        retried = {
            entry.source_key
            for entry in self.entries
            if entry.status in {ManifestStatus.PENDING, ManifestStatus.ERROR}
            and entry.pending_operation is not None
        }

        added_keys = set(observed_by_key) - set(entries_by_key)
        deleted_keys = set(entries_by_key) - set(observed_by_key)
        renamed = _detect_renames(
            tuple(entries_by_key[key] for key in deleted_keys if key not in retried),
            tuple(observed_by_key[key] for key in added_keys),
        )
        renamed_old = {old_key for old_key, _ in renamed}
        renamed_new = {new_key for _, new_key in renamed}

        added = added_keys - renamed_new
        deleted = deleted_keys - renamed_old - retried
        updated: set[str] = set()
        unchanged: set[str] = set()
        for source_key, source in observed_by_key.items():
            entry = entries_by_key.get(source_key)
            if entry is None or source_key in retried:
                continue
            if (
                entry.indexed_hash == source.content_hash
                and entry.status is ManifestStatus.READY
                and entry.pending_operation is None
                and entry.error is None
            ):
                unchanged.add(source_key)
            else:
                updated.add(source_key)

        return ReloadReport(
            added=tuple(sorted(added)),
            updated=tuple(sorted(updated)),
            deleted=tuple(sorted(deleted)),
            renamed=tuple(sorted(renamed, key=lambda pair: (pair[1], pair[0]))),
            retried=tuple(sorted(retried)),
            unchanged=tuple(sorted(unchanged)),
        )


def _detect_renames(
    deleted_entries: tuple[ManifestEntry, ...], observed_sources: tuple[KnowledgeSource, ...]
) -> tuple[tuple[str, str], ...]:
    deleted_by_identity: dict[tuple[KnowledgeCollection, str], list[ManifestEntry]] = {}
    added_by_identity: dict[tuple[KnowledgeCollection, str], list[KnowledgeSource]] = {}
    for entry in deleted_entries:
        content_hash = entry.observed_hash or entry.indexed_hash
        if content_hash is not None:
            deleted_by_identity.setdefault((entry.collection, content_hash), []).append(entry)
    for source in observed_sources:
        added_by_identity.setdefault((source.collection, source.content_hash), []).append(source)

    pairs: list[tuple[str, str]] = []
    for identity, entries in deleted_by_identity.items():
        sources = added_by_identity.get(identity, [])
        if len(entries) == 1 and len(sources) == 1:
            pairs.append((entries[0].source_key, sources[0].source_key))
    return tuple(pairs)
