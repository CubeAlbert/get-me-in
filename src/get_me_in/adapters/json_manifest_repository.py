"""Atomic JSON persistence for schema-versioned index manifests."""

import json
from os import replace
from pathlib import Path
from datetime import datetime

from src.get_me_in.domain.knowledge import IndexManifest, ManifestEntry, ManifestStatus, KnowledgeCollection, PendingIndexOperation


class JsonManifestRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> IndexManifest:
        if not self._path.exists():
            return IndexManifest(1)
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        if raw.get("schema_version") != 1:
            raise ValueError("unsupported knowledge manifest schema")
        entries = tuple(
            ManifestEntry(
                item["source_key"], KnowledgeCollection(item["collection"]), item.get("observed_hash"),
                item.get("indexed_hash"), datetime.fromisoformat(item["mtime"]) if item.get("mtime") else None,
                tuple(item.get("chunk_ids", ())), ManifestStatus(item.get("status", "ready")),
                PendingIndexOperation(item["pending_operation"]) if item.get("pending_operation") else None,
                item.get("error"),
            )
            for item in raw.get("entries", ())
        )
        return IndexManifest(1, entries)

    def save(self, manifest: IndexManifest) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        raw = {"schema_version": manifest.schema_version, "entries": [entry.__dict__ | {"collection": entry.collection.value, "mtime": entry.mtime.isoformat() if entry.mtime else None, "status": entry.status.value, "pending_operation": entry.pending_operation.value if entry.pending_operation else None} for entry in manifest.entries]}
        temporary = self._path.with_suffix(f"{self._path.suffix}.tmp")
        temporary.write_text(json.dumps(raw, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        replace(temporary, self._path)

    def close(self) -> None:
        pass
