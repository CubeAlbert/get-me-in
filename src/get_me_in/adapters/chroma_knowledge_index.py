"""Explicit v2 vector adapters; models and persistence are constructor-owned."""

import logging

from src.get_me_in.domain.knowledge import IndexChunk, IndexHit, KnowledgeSource
from src.get_me_in.ports.llm import CancellationSignal

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, batch_size: int, model: object | None = None) -> None:
        self._batch_size = batch_size
        self._model_name = model_name
        self._model = model

    def prepare(self, cancellation: CancellationSignal) -> None:
        _raise_if_cancelled(cancellation)
        logger.info("embedding model prepare started: model=%s", self._model_name)
        self._ensure_model()
        logger.info("embedding model prepare completed: model=%s", self._model_name)
        _raise_if_cancelled(cancellation)

    def _ensure_model(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def embed(self, texts: tuple[str, ...]) -> tuple[list[float], ...]:
        self._ensure_model()
        values = self._model.encode(list(texts), batch_size=self._batch_size, normalize_embeddings=True, show_progress_bar=False)
        return tuple(value.tolist() for value in values)


class CrossEncoderReranker:
    def __init__(self, model_name: str, batch_size: int, top_k: int, model: object | None = None) -> None:
        self._batch_size, self._top_k, self._model_name = batch_size, top_k, model_name
        self._model = model

    def prepare(self, cancellation: CancellationSignal) -> None:
        _raise_if_cancelled(cancellation)
        logger.info("reranker model prepare started: model=%s", self._model_name)
        self._ensure_model()
        logger.info("reranker model prepare completed: model=%s", self._model_name)
        _raise_if_cancelled(cancellation)

    def _ensure_model(self) -> None:
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self._model_name)

    def rerank(self, query: str, hits: tuple[IndexHit, ...]) -> tuple[IndexHit, ...]:
        self._ensure_model()
        scores = self._model.predict([(query, hit.content) for hit in hits], batch_size=self._batch_size, show_progress_bar=False)
        ranked = tuple(sorted((IndexHit(hit.chunk_id, hit.content, hit.metadata | {"rerank_score": float(score)}, float(score)) for hit, score in zip(hits, scores)), key=lambda hit: hit.score, reverse=True))
        return ranked[:self._top_k]


class ChromaKnowledgeIndex:
    def __init__(self, client: object, embedder: SentenceTransformerEmbedder, reranker: CrossEncoderReranker) -> None:
        self._client, self._embedder, self._reranker = client, embedder, reranker

    def prepare(self, cancellation: CancellationSignal) -> None:
        logger.info("chroma knowledge index prepare started")
        self._embedder.prepare(cancellation)
        self._reranker.prepare(cancellation)
        logger.info("chroma knowledge index prepare completed")

    def replace_source(self, source: KnowledgeSource, chunks: tuple[IndexChunk, ...], cancellation: CancellationSignal) -> None:
        _raise_if_cancelled(cancellation)
        embeddings = self._embedder.embed(tuple(chunk.content for chunk in chunks)) if chunks else ()
        _raise_if_cancelled(cancellation)
        collection = self._client.get_or_create_collection(source.collection.value)
        existing = collection.get(where={"source_key": source.source_key}, include=[])
        old_ids = tuple(existing.get("ids", ()))
        new_ids = tuple(chunk.chunk_id for chunk in chunks)
        try:
            if chunks:
                collection.add(
                    ids=list(new_ids),
                    embeddings=list(embeddings),
                    documents=[chunk.content for chunk in chunks],
                    metadatas=[
                        dict(chunk.metadata) | {"source_key": source.source_key}
                        for chunk in chunks
                    ],
                )
            _raise_if_cancelled(cancellation)
            stale_ids = tuple(identifier for identifier in old_ids if identifier not in new_ids)
            if stale_ids:
                collection.delete(ids=list(stale_ids))
        except Exception as error:
            rollback_error: Exception | None = None
            if new_ids:
                try:
                    collection.delete(ids=list(new_ids))
                except Exception as cleanup_error:
                    rollback_error = cleanup_error
            if rollback_error is not None:
                raise RuntimeError(
                    f"knowledge replace failed: {error}; rollback failed: {rollback_error}"
                ) from error
            raise

    def delete_source(self, source_key: str, *, cancellation: CancellationSignal) -> None:
        _raise_if_cancelled(cancellation)
        collection_name, separator, _ = source_key.partition("/")
        if not separator or collection_name not in {"references", "memories"}:
            raise ValueError(f"invalid knowledge source key: {source_key}")
        try:
            collection = self._client.get_collection(collection_name)
        except Exception as error:
            if _is_missing_collection(error):
                return
            raise
        collection.delete(where={"source_key": source_key})
        _raise_if_cancelled(cancellation)

    def search(self, query: str, *, collection: str, category: str | None, top_k: int, cancellation: CancellationSignal) -> tuple[IndexHit, ...]:
        if cancellation.is_cancelled: raise InterruptedError
        try:
            target = self._client.get_collection(collection)
        except Exception as error:
            if _is_missing_collection(error):
                return ()
            raise
        result = target.query(
            query_embeddings=list(self._embedder.embed((query,))),
            n_results=top_k,
            where={"category": category} if category else None,
            include=["documents", "metadatas", "distances"],
        )
        hits = tuple(IndexHit(identifier, result["documents"][0][index], result["metadatas"][0][index], 1 - float(result["distances"][0][index])) for index, identifier in enumerate(result.get("ids", [[]])[0]))
        return self._reranker.rerank(query, hits)

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if close is not None:
            close()


def _raise_if_cancelled(cancellation: CancellationSignal) -> None:
    if cancellation.is_cancelled:
        raise InterruptedError("knowledge index operation cancelled")


def _is_missing_collection(error: Exception) -> bool:
    try:
        from chromadb.errors import NotFoundError
    except ImportError:
        return False
    return isinstance(error, NotFoundError)
