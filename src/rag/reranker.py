"""RAG Reranker — cross-encoder 重排。

用法:
    from src.rag.reranker import Reranker

    reranker = Reranker()
    ranked = reranker.rerank("排序算法", candidates)
"""

from src.config import config
from src.rag.chunker import Chunk

from sentence_transformers import CrossEncoder


class Reranker:
    """独立加载 cross-encoder 模型，对召回结果精排。

    模型名由 CROSS_ENCODER_MODEL 配置，batch_size 由 RERANK_BATCH_SIZE 配置，
    top_k 默认值由 RERANK_TOP_K 配置。__init__ 时预热，避免首次调用卡顿。
    异常直接抛出，由调用方降级。
    """

    def __init__(self) -> None:
        self._model = CrossEncoder(config.CROSS_ENCODER_MODEL)
        self._default_batch_size = int(config.RERANK_BATCH_SIZE)
        self._model.predict([("预热", "预热")])

    def rerank(
        self,
        query: str,
        candidates: list[Chunk],
        top_k: int | None = None,
    ) -> list[Chunk]:
        """对候选 Chunk 逐对评分，分数注入 metadata["rerank_score"]，降序返回 top_k 条。

        Args:
            query: 查询文本。
            candidates: 待重排的 Chunk 列表。
            top_k: 返回数量，默认值由 RERANK_TOP_K 环境变量配置。

        Returns:
            按 rerank_score 降序排列的 Chunk 列表（最多 top_k 条）。
        """
        n_top = top_k if top_k is not None else int(config.RERANK_TOP_K)

        if not candidates:
            return []

        pairs = [(query, c.content) for c in candidates]
        scores = self._model.predict(
            pairs,
            batch_size=self._default_batch_size,
            show_progress_bar=False,
        )

        # 分数可能是 float 或 numpy array，统一转 float
        for i, chunk in enumerate(candidates):
            chunk.metadata["rerank_score"] = float(scores[i])

        candidates.sort(key=lambda c: c.metadata["rerank_score"], reverse=True)

        return candidates[:n_top]
