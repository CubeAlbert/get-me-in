"""Filesystem-backed v2 reference sources with a strict Markdown boundary."""

from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone

from src.get_me_in.domain.knowledge import KnowledgeCollection, KnowledgeDocument, KnowledgeSource


class LocalKnowledgeSourceRepository:
    def __init__(self, reference_root: Path) -> None:
        self._root = reference_root.resolve()

    def scan(self, target: str | None = None) -> tuple[KnowledgeSource, ...]:
        paths = sorted(path for path in self._root.rglob("*.md") if path.is_file())
        sources = tuple(self._source(path) for path in paths)
        return tuple(source for source in sources if target is None or target in source.source_key)

    def read(self, source: KnowledgeSource) -> KnowledgeDocument:
        path = self._path(source)
        return KnowledgeDocument(source, path.read_text(encoding="utf-8"), {"category": path.parent.name})

    def _source(self, path: Path) -> KnowledgeSource:
        content = path.read_bytes()
        return KnowledgeSource(KnowledgeCollection.REFERENCES, f"references/{path.relative_to(self._root).as_posix()}", sha256(content).hexdigest(), datetime.fromtimestamp(path.stat().st_mtime, timezone.utc))

    def _path(self, source: KnowledgeSource) -> Path:
        if source.collection is not KnowledgeCollection.REFERENCES or not source.source_key.startswith("references/"):
            raise ValueError("source is outside this reference repository")
        path = (self._root / source.source_key.removeprefix("references/")).resolve()
        if not path.is_relative_to(self._root) or path.suffix.lower() != ".md":
            raise ValueError("source is outside this reference repository")
        return path
