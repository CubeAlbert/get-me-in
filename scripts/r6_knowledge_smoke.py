"""可复跑的 R6 真实 Chroma、embedding 与 reranker 验证。"""

from datetime import datetime, timezone
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    from chromadb import PersistentClient

    from src.get_me_in.adapters.chroma_knowledge_index import (
        ChromaKnowledgeIndex,
        CrossEncoderReranker,
        SentenceTransformerEmbedder,
    )
    from src.get_me_in.adapters.markdown_chunker import MarkdownChunker
    from src.get_me_in.application.cancellation import CancellationToken
    from src.get_me_in.application.settings import Settings
    from src.get_me_in.domain.knowledge import (
        KnowledgeCollection,
        KnowledgeDocument,
        KnowledgeSource,
    )

    settings = Settings.from_env(os.environ, project_root=project_root)
    index: ChromaKnowledgeIndex | None = None
    with TemporaryDirectory() as temporary:
        try:
            source = KnowledgeSource(
                KnowledgeCollection.REFERENCES,
                "references/r6-smoke.md",
                "r6-smoke-hash",
                datetime.now(timezone.utc),
            )
            document = KnowledgeDocument(
                source,
                "Python interview preparation includes algorithms and system design.",
                {"category": "interview_questions"},
            )
            index = ChromaKnowledgeIndex(
                PersistentClient(path=temporary),
                SentenceTransformerEmbedder(
                    settings.embedding_model, settings.embedding_batch_size
                ),
                CrossEncoderReranker(
                    settings.reranker_model,
                    settings.rerank_batch_size,
                    settings.retrieval_top_k,
                ),
            )
            cancellation = CancellationToken()
            index.replace_source(
                source, MarkdownChunker().chunk(document), cancellation
            )
            hits = index.search(
                "Python interview algorithms",
                collection="references",
                category="interview_questions",
                top_k=3,
                cancellation=cancellation,
            )
            if not hits or "Python interview" not in hits[0].content:
                raise AssertionError("real knowledge query did not return the fixture")
            index.delete_source(source.source_key, cancellation=cancellation)
            print(f"R6_SMOKE_OK hits={len(hits)} score={hits[0].score:.6f}")
        finally:
            if index is not None:
                index.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
