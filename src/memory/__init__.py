"""记忆模块入口 — 统一 Facade，管理单例与装配。

用法:
    from src.llm import get_client
    from src.memory import build_memories, search_memories, delete_memory

    llm = get_client()

    # 从对话构建记忆（sync/async）
    memories = build_memories(conversation, agent="main", llm=llm)

    # 语义检索
    results = search_memories("Python 后端", agent="main")

    # 删除记忆
    delete_memory("main", "data/memories/main/20260702143000.123.md")
"""

import threading

from src.logger import get_logger
from src.llm.client import LLMClient
from src.message import Message
from src.memory.builder import MemoryBuilder
from src.memory.indexer import MemoryIndexer
from src.memory.retriever import MemoryRetriever
from src.memory.schemas import Memory
from src.memory.store import MemoryStore

logger = get_logger(__name__)

_store: MemoryStore | None = None
_indexer: MemoryIndexer | None = None
_retriever: MemoryRetriever | None = None
_init_lock = threading.Lock()

_pending_threads: set[threading.Thread] = set()
_pending_lock = threading.Lock()


def _ensure_init() -> None:
    """线程安全的懒加载初始化，仅执行一次。"""
    global _store, _indexer, _retriever
    if _store is not None:
        return
    with _init_lock:
        if _store is not None:
            return
        _store = MemoryStore()
        _indexer = MemoryIndexer(_store)
        _retriever = MemoryRetriever()
        from src.lifecycle import register_shutdown
        register_shutdown(hook=_shutdown_wait_pending, name="memory")
        logger.info("memory: 单例初始化完成（Store + Indexer + Retriever）")


def init() -> None:
    """显式初始化记忆模块（可选，首次调用自动懒加载）。"""
    _ensure_init()


def build_memories(
    conversation: list[Message],
    agent: str,
    llm: LLMClient,
    sync_mode: bool = True,
) -> list[Memory] | None:
    """从对话构建记忆并持久化。

    内部串联 MemoryBuilder.build() → MemoryStore.write_memory()，
    写入后 MemoryIndexer 自动同步 RAG 索引。

    Args:
        conversation: Message 列表，按时间顺序排列。
        agent: 所属 Agent 名称。
        llm: LLM 客户端实例。
        sync_mode: True 同步执行返回 Memory 列表；False daemon 线程后台执行返回 None。

    Returns:
        sync_mode=True 返回 Memory 列表（可能为空）；sync_mode=False 返回 None。
    """
    _ensure_init()
    if sync_mode:
        return _build_sync(conversation, agent, llm)

    logger.info("build_memories: async 模式，启动 daemon 线程")

    def _run():
        try:
            _build_sync(conversation, agent, llm)
        finally:
            with _pending_lock:
                _pending_threads.discard(t)

    t = threading.Thread(
        target=_run,
        daemon=True,
        name=f"memory-builder-{agent}",
    )
    with _pending_lock:
        _pending_threads.add(t)
    t.start()
    return None


def search_memories(
    query: str,
    agent: str | None = None,
    top_k: int = 5,
) -> list[Memory]:
    """语义检索记忆。

    Args:
        query: 查询文本。
        agent: 限定 Agent 范围，None 表示跨 Agent 全量检索。
        top_k: 返回数量。

    Returns:
        匹配的 Memory 列表，按相关度降序。
    """
    _ensure_init()
    return _retriever.search(query, agent=agent, top_k=top_k)  # type: ignore[union-attr]


def delete_memory(agent: str, file_path: str) -> bool:
    """删除一条记忆文件，同步移除 RAG 索引。

    Args:
        agent: Agent 名称。
        file_path: 要删除的文件绝对路径。

    Returns:
        删除成功返回 True；文件不存在或异常返回 False。
    """
    _ensure_init()
    return _store.delete_memory(agent, file_path)  # type: ignore[union-attr]


def _shutdown_wait_pending(timeout: float = 10) -> None:
    """等待所有后台记忆固化线程完成。注册为 lifecycle shutdown hook。"""
    with _pending_lock:
        threads = list(_pending_threads)

    if not threads:
        return

    logger.info("memory: 等待 %d 个后台记忆固化线程完成...", len(threads))
    for t in threads:
        t.join(timeout)
        if t.is_alive():
            logger.warning("memory: 线程 %s 超时未完成", t.name)
    logger.info("memory: 后台线程等待完成")


def _build_sync(
    conversation: list[Message],
    agent: str,
    llm: LLMClient,
) -> list[Memory]:
    """同步构建记忆 → 逐条写入 Store。"""
    builder = MemoryBuilder(llm)
    memories = builder.build(conversation, agent)

    if not memories:
        logger.info("build_memories: agent=%s 未提取到记忆", agent)
        return []

    for m in memories:
        _store.write_memory(agent, m)  # type: ignore[union-attr]

    logger.info("build_memories: agent=%s 写入 %d 条记忆", agent, len(memories))
    return memories
