"""Contract tests for lightweight v2 knowledge adapters."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.json_manifest_repository import JsonManifestRepository
from src.get_me_in.adapters.local_knowledge_sources import LocalKnowledgeSourceRepository
from src.get_me_in.adapters.markdown_chunker import MarkdownChunker
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


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
