"""RAG ChromaStore — Chroma 向量存储封装。

用法:
    from src.rag.store import ChromaStore

    store = ChromaStore()
    store.add(chunks, collection="references")
    results = store.query(query_vector, collection="references", filter={"category": "knowledge_base"})
    store.remove(source_file="data/reference/knowledge_base/cs_fundamentals.md", collection="references")
"""

from src.config import config
from src.rag.chunker import Chunk
from src.rag.embedder import Embedder

import chromadb


class ChromaStore:
    """封装 Chroma 客户端，管理 collection 的创建、写入、查询、删除。

    内部持有 Embedder 完成向量化。通过 CHROMA_PERSIST_DIR 环境变量
    切换内存/持久化模式。不预建 collection，首次 add() 自动创建。
    """

    def __init__(self) -> None:
        self._embedder = Embedder()
        persist_dir = getattr(config, "CHROMA_PERSIST_DIR", None)
        if persist_dir:
            self._client = chromadb.PersistentClient(path=persist_dir)
        else:
            self._client = chromadb.Client()

    def add(self, chunks: list[Chunk], collection: str) -> None:
        """将 chunk 列表向量化后写入指定 collection。

        Args:
            chunks: 待写入的 Chunk 列表。
            collection: collection 名（不校验，调用方保证正确）。
        """
        if not chunks:
            return

        contents = [chunk.content for chunk in chunks]
        ids = [chunk.id for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        vectors = self._embedder.embed(contents)

        col = self._client.get_or_create_collection(collection)
        col.add(ids=ids, embeddings=vectors, metadatas=metadatas, documents=contents)

    def query(
        self,
        query_text: str,
        collection: str,
        filter: dict | None = None,
        top_k: int | None = None,
    ) -> list[Chunk]:
        """在指定 collection 中执行语义检索。

        Args:
            query_text: 查询文本，内部自动向量化。
            collection: collection 名。
            filter: Chroma where 条件，直接透传。None 表示全库检索。
            top_k: 返回数量，默认值由 RETRIEVAL_TOP_K 环境变量配置。

        Returns:
            匹配的 Chunk 列表，content 从 Chroma documents 字段还原。
        """
        n_results = top_k if top_k is not None else int(config.RETRIEVAL_TOP_K)
        query_vector = self._embedder.embed([query_text])[0]

        col = self._client.get_collection(collection)
        result = col.query(
            query_embeddings=[query_vector],
            n_results=n_results,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[Chunk] = []
        if not result["ids"] or not result["ids"][0]:
            return chunks

        for i, chunk_id in enumerate(result["ids"][0]):
            content = result["documents"][0][i] if result["documents"] else ""
            metadata = result["metadatas"][0][i] if result["metadatas"] else {}
            chunks.append(Chunk(id=chunk_id, content=content, metadata=metadata))

        return chunks

    def remove(self, source_file: str, collection: str) -> None:
        """按 source_file 删除指定 collection 中的旧 chunk。

        静默执行，source_file 不存在时不报错。

        Args:
            source_file: 来源文件路径，对应 Chunk.metadata["source_file"]。
            collection: collection 名。
        """
        try:
            col = self._client.get_collection(collection)
            col.delete(where={"source_file": source_file})
        except Exception:
            pass
