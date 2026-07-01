"""RAG Embedder — bi-encoder 文本向量化。

用法:
    from src.rag.embedder import Embedder

    emb = Embedder()
    vectors = emb.embed(["Python GIL", "快速排序"])
"""

from src.config import config
from src.logger import get_logger

from sentence_transformers import SentenceTransformer

logger = get_logger(__name__)


class Embedder:
    """封装 bi-encoder 模型，将文本转为归一化稠密向量。

    模型名由 BI_ENCODER_MODEL 配置，batch_size 由 EMBED_BATCH_SIZE 配置。
    """

    def __init__(self) -> None:
        model_name = config.BI_ENCODER_MODEL
        logger.info("开始加载 bi-encoder 模型: %s", model_name)
        self._model = SentenceTransformer(model_name)
        logger.info("bi-encoder 模型加载完成")

        self._default_batch_size = int(config.EMBED_BATCH_SIZE)

    def embed(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """将文本列表转为归一化向量列表。

        Args:
            texts: 待向量化的文本列表。
            batch_size: 批处理大小，默认值为 EMBED_BATCH_SIZE 环境变量。

        Returns:
            与 texts 等长的向量列表。
        """
        bs = batch_size if batch_size is not None else self._default_batch_size
        logger.info("向量化 %d 条文本，batch_size=%d", len(texts), bs)
        result = self._model.encode(
            texts,
            batch_size=bs,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vec.tolist() for vec in result]
