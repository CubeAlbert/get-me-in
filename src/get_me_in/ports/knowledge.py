"""Ports for explicit knowledge source, index, and manifest ownership."""

from typing import Protocol

from src.get_me_in.domain.knowledge import IndexChunk, IndexHit, IndexManifest, KnowledgeDocument, KnowledgeSource
from src.get_me_in.ports.llm import CancellationSignal


class KnowledgeSourceRepository(Protocol):
    def scan(self, target: str | None = None) -> tuple[KnowledgeSource, ...]: ...

    def read(self, source: KnowledgeSource) -> KnowledgeDocument: ...


class DocumentChunker(Protocol):
    def chunk(self, document: KnowledgeDocument) -> tuple[IndexChunk, ...]: ...


class KnowledgeIndexPort(Protocol):
    def prepare(self, cancellation: CancellationSignal) -> None: ...

    def replace_source(self, source: KnowledgeSource, chunks: tuple[IndexChunk, ...], cancellation: CancellationSignal) -> None: ...

    def delete_source(self, source_key: str, *, cancellation: CancellationSignal) -> None: ...

    def search(
        self,
        query: str,
        *,
        collection: str,
        category: str | None,
        top_k: int,
        cancellation: CancellationSignal,
    ) -> tuple[IndexHit, ...]: ...

    def close(self) -> None: ...


class ManifestRepository(Protocol):
    def load(self) -> IndexManifest: ...

    def save(self, manifest: IndexManifest) -> None: ...

    def close(self) -> None: ...
