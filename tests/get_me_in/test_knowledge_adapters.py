"""Contract tests for lightweight v2 knowledge adapters."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.json_manifest_repository import JsonManifestRepository
from src.get_me_in.adapters.in_memory_manifest_repository import InMemoryManifestRepository
from src.get_me_in.adapters.local_knowledge_sources import LocalKnowledgeSourceRepository
from src.get_me_in.adapters.markdown_chunker import MarkdownChunker
from src.get_me_in.adapters.chroma_knowledge_index import ChromaKnowledgeIndex
from src.get_me_in.domain.knowledge import IndexManifest, KnowledgeCollection, KnowledgeDocument, KnowledgeSource, ManifestEntry


class KnowledgeAdapterTests(unittest.TestCase):
    def test_local_sources_are_markdown_only_and_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "category").mkdir()
            (root / "category" / "one.md").write_text("hello", encoding="utf-8")
            (root / "skip.txt").write_text("skip", encoding="utf-8")
            repository = LocalKnowledgeSourceRepository(root)

            sources = repository.scan()

            self.assertEqual(("references/category/one.md",), tuple(source.source_key for source in sources))
            self.assertEqual("category", repository.read(sources[0]).metadata["category"])
            with self.assertRaises(ValueError):
                repository.read(KnowledgeSource(KnowledgeCollection.REFERENCES, "references/../secret.md", "x", _now()))

    def test_chunk_ids_are_deterministic(self) -> None:
        source = KnowledgeSource(KnowledgeCollection.REFERENCES, "references/a.md", "hash", _now())
        document = KnowledgeDocument(source, "one\n---\ntwo")

        self.assertEqual(MarkdownChunker().chunk(document), MarkdownChunker().chunk(document))

    def test_manifest_round_trips_and_rejects_unknown_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            repository = JsonManifestRepository(path)
            manifest = IndexManifest(1, (ManifestEntry("references/a.md", KnowledgeCollection.REFERENCES, "seen", "indexed", _now()),))

            repository.save(manifest)

            self.assertEqual(manifest, repository.load())
            path.write_text('{"schema_version": 9}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema"):
                repository.load()

    def test_in_memory_manifests_are_process_local_and_start_empty(self) -> None:
        first = InMemoryManifestRepository()
        second = InMemoryManifestRepository()
        manifest = IndexManifest(1, (ManifestEntry("references/a.md", KnowledgeCollection.REFERENCES, "seen", "indexed", _now()),))

        first.save(manifest)

        self.assertEqual(manifest, first.load())
        self.assertEqual(IndexManifest(1), second.load())
        with self.assertRaisesRegex(ValueError, "schema"):
            first.save(IndexManifest(2))

    def test_chroma_index_uses_injected_client_and_reranker(self) -> None:
        client = _Client()
        index = ChromaKnowledgeIndex(client, _Embedder(), _Reranker())
        source = KnowledgeSource(KnowledgeCollection.REFERENCES, "references/a.md", "hash", _now())
        token = _Token()

        index.replace_source(source, MarkdownChunker().chunk(KnowledgeDocument(source, "text")), token)
        hits = index.search("query", collection="references", category=None, top_k=1, cancellation=token)
        index.close()

        self.assertEqual(("found",), tuple(hit.content for hit in hits))
        self.assertTrue(client.closed)

    def test_chroma_prepare_loads_embedder_and_reranker_without_querying(self) -> None:
        embedder = _PreparingModel()
        reranker = _PreparingModel()
        index = ChromaKnowledgeIndex(_FailingClient(), embedder, reranker)

        index.prepare(_Token())

        self.assertEqual(1, embedder.prepare_calls)
        self.assertEqual(1, reranker.prepare_calls)

    def test_chroma_replace_embeds_before_mutating_existing_source(self) -> None:
        collection = _Collection(old_ids=("old",))
        index = ChromaKnowledgeIndex(_Client(collection), _FailingEmbedder(), _Reranker())
        source = KnowledgeSource(KnowledgeCollection.REFERENCES, "references/a.md", "new", _now())

        with self.assertRaisesRegex(RuntimeError, "embedding failed"):
            index.replace_source(
                source,
                MarkdownChunker().chunk(KnowledgeDocument(source, "new text")),
                _Token(),
            )

        self.assertEqual([], collection.mutations)

    def test_chroma_replace_rolls_back_new_chunks_when_old_delete_fails(self) -> None:
        collection = _Collection(old_ids=("old",), fail_old_delete=True)
        index = ChromaKnowledgeIndex(_Client(collection), _Embedder(), _Reranker())
        source = KnowledgeSource(KnowledgeCollection.REFERENCES, "references/a.md", "new", _now())
        chunks = MarkdownChunker().chunk(KnowledgeDocument(source, "new text"))

        with self.assertRaisesRegex(RuntimeError, "delete failed"):
            index.replace_source(source, chunks, _Token())

        self.assertIn(("add", (chunks[0].chunk_id,)), collection.mutations)
        self.assertEqual(("delete", (chunks[0].chunk_id,)), collection.mutations[-1])

    def test_chroma_delete_propagates_operational_errors(self) -> None:
        index = ChromaKnowledgeIndex(_FailingClient(), _Embedder(), _Reranker())

        with self.assertRaisesRegex(RuntimeError, "chroma unavailable"):
            index.delete_source("references/a.md", cancellation=_Token())

    def test_chroma_search_returns_no_hits_when_collection_does_not_exist(self) -> None:
        index = ChromaKnowledgeIndex(_MissingCollectionClient(), _FailingEmbedder(), _Reranker())

        hits = index.search(
            "query",
            collection="memories",
            category=None,
            top_k=1,
            cancellation=_Token(),
        )

        self.assertEqual((), hits)

    def test_chroma_search_propagates_operational_errors(self) -> None:
        index = ChromaKnowledgeIndex(_FailingClient(), _Embedder(), _Reranker())

        with self.assertRaisesRegex(RuntimeError, "chroma unavailable"):
            index.search(
                "query",
                collection="memories",
                category=None,
                top_k=1,
                cancellation=_Token(),
            )


class _Token:
    is_cancelled = False


class _PreparingModel:
    def __init__(self):
        self.prepare_calls = 0

    def prepare(self, cancellation):
        self.prepare_calls += 1


class _Embedder:
    def embed(self, texts): return ([0.1],) * len(texts)


class _FailingEmbedder:
    def embed(self, texts): raise RuntimeError("embedding failed")


class _Reranker:
    def rerank(self, query, hits): return hits


class _Collection:
    def __init__(self, *, old_ids=(), fail_old_delete=False):
        self.old_ids = old_ids
        self.fail_old_delete = fail_old_delete
        self.mutations = []

    def get(self, **kwargs): return {"ids": list(self.old_ids)}
    def delete(self, **kwargs):
        ids = tuple(kwargs.get("ids", ()))
        self.mutations.append(("delete", ids or kwargs.get("where")))
        if self.fail_old_delete and ids == self.old_ids:
            raise RuntimeError("delete failed")
    def add(self, **kwargs): self.mutations.append(("add", tuple(kwargs["ids"])))
    def query(self, **kwargs):
        if not isinstance(kwargs["query_embeddings"], list):
            raise TypeError("query_embeddings must be a list")
        return {"ids": [["id"]], "documents": [["found"]], "metadatas": [[{}]], "distances": [[0.2]]}


class _Client:
    def __init__(self, collection=None): self.collection = collection or _Collection(); self.closed = False
    def get_or_create_collection(self, name): return self.collection
    def get_collection(self, name): return self.collection
    def close(self): self.closed = True


class _FailingClient:
    def get_collection(self, name): raise RuntimeError("chroma unavailable")


class _MissingCollectionClient:
    def get_collection(self, name):
        from chromadb.errors import NotFoundError

        raise NotFoundError(f"Collection {name} does not exist")


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
