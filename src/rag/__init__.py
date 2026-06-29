"""RAG 模块入口 — 管理单例与装配。

用法:
    from src.rag import search, load, is_ready

    if is_ready():
        results = search("排序算法", collection="references")
    info = load("cs_fundamentals")  # 匹配重载
    info = load()                    # 全量重载
"""

import threading

from src.rag.chunker import Chunk
from src.rag.loader import LoaderState, RagLoader
from src.rag.reranker import Reranker
from src.rag.store import ChromaStore

_store: ChromaStore | None = None
_reranker: Reranker | None = None
_loader: RagLoader | None = None
_init_lock = threading.Lock()


def _ensure_init() -> None:
    """线程安全的懒加载初始化，仅执行一次。"""
    global _store, _reranker, _loader
    if _store is not None:
        return
    with _init_lock:
        if _store is not None:
            return
        _store = ChromaStore()
        _reranker = Reranker()
        _loader = RagLoader(store=_store, reranker=_reranker)
        t = threading.Thread(target=_loader.auto_load, daemon=True, name="rag-loader")
        t.start()


def is_ready() -> bool:
    """返回 RAG 是否就绪（可安全调用 search）。"""
    _ensure_init()
    return _loader.state == LoaderState.READY  # type: ignore[union-attr]


def search(query_text: str, collection: str = "references", top_k: int | None = None) -> list[Chunk]:
    """检索并重排，返回最终结果。

    Raises:
        RuntimeError: RAG 处于 LOADING 或 ERROR 状态时抛出。
    """
    _ensure_init()
    if _loader.state == LoaderState.LOADING:  # type: ignore[union-attr]
        raise RuntimeError("RAG 正在加载中，请稍后重试")
    if _loader.state == LoaderState.ERROR:  # type: ignore[union-attr]
        raise RuntimeError(f"RAG 加载失败: {_loader.error}")  # type: ignore[union-attr]
    candidates = _store.query(query_text, collection=collection)  # type: ignore[union-attr]
    return _reranker.rerank(query_text, candidates, top_k=top_k)  # type: ignore[union-attr]


def load(target: str | None = None) -> str:
    """加载/重载数据。target=None 全量重载；target 非空匹配路径重载。

    Returns:
        加载结果描述字符串。
    """
    _ensure_init()
    return _loader.reload(target)  # type: ignore[union-attr]
