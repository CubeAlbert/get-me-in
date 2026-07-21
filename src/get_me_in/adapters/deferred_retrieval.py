"""R6 前用于保留检索工具边界的临时适配器。"""

from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.retrieval import RetrievalResult


class DeferredRetrievalAdapter:
    """明确拒绝运行期检索，避免 v2 依赖旧版全局 RAG 状态。"""

    def search(
        self,
        query: str,
        *,
        collection: str,
        category: str | None,
        top_k: int,
        cancellation: CancellationSignal,
    ) -> tuple[RetrievalResult, ...]:
        del query, collection, category, top_k
        if cancellation.is_cancelled:
            raise InterruptedError
        raise RuntimeError("检索后端将在 R6 接入；当前 v2 尚不可用")
