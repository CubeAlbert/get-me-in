"""MemoryIndexer — 监听 MemoryStore 事件，桥接 RAG 索引。

观察者模式：构造时注册 on_write / on_delete 回调到 MemoryStore，
收到事件后同步调用 RAG 的 load_file / delete 完成索引同步。

用法:
    from src.memory.store import MemoryStore
    from src.memory.indexer import MemoryIndexer

    store = MemoryStore()
    indexer = MemoryIndexer(store)  # 构造即绑定，无需手动调用
"""

from src.logger import get_logger
from src.memory.schemas import MemoryWrittenEvent, MemoryDeletedEvent

logger = get_logger(__name__)


class MemoryIndexer:
    """监听 Store 写/删事件，同步更新 RAG 索引。

    构造时自动注册回调到 MemoryStore，此后每次 write_memory() /
    delete_memory() 成功后自动触发索引更新。无公开方法，纯事件驱动。
    """

    def __init__(self, store) -> None:
        """
        Args:
            store: MemoryStore 实例，注册 on_write / on_delete 回调。
        """
        store.on_write(self._on_write)
        store.on_delete(self._on_delete)
        logger.info("MemoryIndexer: 已注册 Store 回调")

    # ------------------------------------------------------------------
    # 回调
    # ------------------------------------------------------------------

    def _on_write(self, event: MemoryWrittenEvent) -> None:
        """接收 MemoryWritten 事件，将新文件增量索引入 RAG。

        异常记日志不抛出，匹配 Store 回调的防御性约定。
        """
        try:
            from src.rag import load_file

            load_file(event.file_path)
            logger.info("MemoryIndexer: 已索引 %s", event.file_path)
        except Exception:
            logger.exception(
                "MemoryIndexer: 索引失败 %s", event.file_path
            )

    def _on_delete(self, event: MemoryDeletedEvent) -> None:
        """接收 MemoryDeleted 事件，从 RAG 索引中移除对应 chunk。

        异常记日志不抛出，匹配 Store 回调的防御性约定。
        """
        try:
            from src.rag import delete

            deleted = delete(where={"source_file": event.file_path})
            logger.info(
                "MemoryIndexer: 已移除 %d 条索引 (%s)", deleted, event.file_path
            )
        except Exception:
            logger.exception(
                "MemoryIndexer: 移除索引失败 %s", event.file_path
            )
