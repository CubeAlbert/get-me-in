"""MemoryRetriever — 封装 RAG 语义检索，返回 Memory 对象。

无状态，直接调用。RAG 未就绪时抛出 RuntimeError。

用法:
    from src.memory.retriever import MemoryRetriever

    retriever = MemoryRetriever()
    memories = retriever.search("Python 异步", agent="main")
    for m in memories:
        print(m.content)
"""

from src.logger import get_logger
from src.memory.schemas import Memory, chunk_to_memory

logger = get_logger(__name__)


class MemoryRetriever:
    """语义检索记忆，内部封装 RAG search → Chunk → Memory 转换。

    无状态，不持任何外部依赖。agent=None 时跨 Agent 全量检索。
    """

    def search(
        self, query: str, agent: str | None = None, top_k: int = 5
    ) -> list[Memory]:
        """语义检索记忆。

        Args:
            query: 查询文本。
            agent: 限定 Agent 范围，None 表示跨 Agent 全量检索。
            top_k: 返回数量。

        Returns:
            匹配的 Memory 列表，按相关度降序。

        Raises:
            RuntimeError: RAG 未就绪（LOADING 或 ERROR 状态）。
        """
        from src.rag import is_ready, search as rag_search

        if not is_ready():
            raise RuntimeError("RAG 未就绪，无法检索记忆")

        filter_dict = {"agent": agent} if agent else None

        chunks = rag_search(
            query,
            collection="memories",
            filter=filter_dict,
            top_k=top_k,
        )

        memories = [chunk_to_memory(c) for c in chunks]
        logger.info(
            "MemoryRetriever: 检索完成 query='%s' agent=%s → %d 条",
            query, agent or "*", len(memories),
        )
        return memories
