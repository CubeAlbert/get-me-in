"""RAG 模块入口 — 管理单例与装配。

用法:
    from src.rag import start, search, load, load_file, is_ready

    start()  # 程序入口调用一次，后台加载模型+数据，不阻塞

    if is_ready():
        results = search("排序算法", collection="references")
    info = load("cs_fundamentals")  # 匹配重载
    info = load()                    # 全量重载
    load_file(Path("data/memories/main/20260702143000.000.md"))  # 增量索引
"""

import os

# 必须在 sentence_transformers import 之前设置，否则进度条不受控
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TQDM_DISABLE"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import threading
from pathlib import Path

from src.logger import get_logger
from src.utils.chunker import Chunk
from src.rag.loader import LoaderState, RagLoader
from src.rag.reranker import Reranker
from src.rag.store import ChromaStore

logger = get_logger(__name__)

_store: ChromaStore | None = None
_reranker: Reranker | None = None
_loader: RagLoader | None = None
_init_lock = threading.Lock()


def _ensure_init() -> None:
    """线程安全的懒加载初始化，仅执行一次。"""
    global _store, _reranker, _loader
    if _loader is not None:
        return
    with _init_lock:
        if _loader is not None:
            return
        _store = ChromaStore()
        _reranker = Reranker()
        _loader = RagLoader(store=_store, reranker=_reranker)
        t = threading.Thread(target=_loader.auto_load, daemon=True, name="rag-loader")
        t.start()
        logger.info("RAG: 单例初始化完成，启动 daemon 加载线程")


def start() -> None:
    """启动 RAG 后台初始化（模型加载 + 数据入库），不阻塞调用方。"""
    logger.info("RAG: 启动后台初始化")
    t = threading.Thread(target=_ensure_init, daemon=True, name="rag-start")
    t.start()


def is_ready() -> bool:
    """返回 RAG 是否就绪（可安全调用 search）。"""
    _ensure_init()
    return _loader.state == LoaderState.READY  # type: ignore[union-attr]


def search(
    query_text: str,
    collection: str = "references",
    filter: dict | None = None,
    top_k: int | None = None,
) -> list[Chunk]:
    """检索并重排，返回最终结果。

    Args:
        query_text: 查询文本。
        collection: 目标 collection，默认 ``"references"``。
        filter: Chroma where 条件，透传至 store.query()。None 表示全库检索。
        top_k: 返回数量，默认由 RERANK_TOP_K 环境变量控制。

    Raises:
        RuntimeError: RAG 处于 LOADING 或 ERROR 状态时抛出。
    """
    _ensure_init()
    if _loader.state == LoaderState.LOADING:  # type: ignore[union-attr]
        logger.warning("RAG: 未就绪 (state=%s)，拒绝查询", _loader.state.value)  # type: ignore[union-attr]
        raise RuntimeError("RAG 正在加载中，请稍后重试")
    if _loader.state == LoaderState.ERROR:  # type: ignore[union-attr]
        logger.warning("RAG: 未就绪 (state=%s)，拒绝查询", _loader.state.value)  # type: ignore[union-attr]
        raise RuntimeError(f"RAG 加载失败: {_loader.error}")  # type: ignore[union-attr]
    candidates = _store.query(query_text, collection=collection, filter=filter)  # type: ignore[union-attr]
    return _reranker.rerank(query_text, candidates, top_k=top_k)  # type: ignore[union-attr]


def delete(where: dict, collection: str = "memories") -> int:
    """按 metadata 条件删除 chunk。

    Args:
        where: Chroma where 条件，空 ``{}`` 抛 ValueError。
        collection: 目标 collection，默认 ``"memories"``。

    Returns:
        删除条数。

    Raises:
        ValueError: where 为空。
        RuntimeError: RAG 处于 LOADING 状态。
    """
    _ensure_init()
    if _loader.state == LoaderState.LOADING:  # type: ignore[union-attr]
        raise RuntimeError("RAG 正在加载中，请稍后重试")
    return _store.delete_by_filter(where, collection=collection)  # type: ignore[union-attr]


def load(target: str | None = None) -> str:
    """加载/重载数据。target=None 全量重载；target 非空匹配路径重载。

    Returns:
        加载结果描述字符串。
    """
    _ensure_init()
    return _loader.reload(target)  # type: ignore[union-attr]


def load_file(path: str | Path) -> None:
    """增量加载单个文件到 RAG 索引（MemoryIndexer 回调用）。

    底层调用 ``RagLoader.load_file()``，内部 remove 旧 chunk → chunk → add。
    MemoryStore 写入/删除文件后，由 MemoryIndexer 通过此函数同步索引。

    Args:
        path: 要索引的文件路径（绝对路径）。

    Raises:
        RuntimeError: RAG 处于 ERROR 状态。
    """
    _ensure_init()
    if _loader.state == LoaderState.ERROR:  # type: ignore[union-attr]
        raise RuntimeError(f"RAG 加载失败，无法索引文件: {_loader.error}")  # type: ignore[union-attr]
    _loader.load_file(Path(path))  # type: ignore[union-attr]
