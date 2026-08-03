"""Deterministic Markdown chunking for the knowledge index."""

from hashlib import sha256

from src.get_me_in.domain.knowledge import IndexChunk, KnowledgeDocument


class MarkdownChunker:
    def chunk(self, document: KnowledgeDocument) -> tuple[IndexChunk, ...]:
        chunks = []
        for index, content in enumerate(piece.strip() for piece in document.content.split("\n---\n")):
            if not content:
                continue
            digest = sha256(f"{document.source.source_key}:{document.source.content_hash}:{index}".encode()).hexdigest()
            chunks.append(IndexChunk(digest, document.source.source_key, document.source.collection, content, document.metadata))
        return tuple(chunks)
