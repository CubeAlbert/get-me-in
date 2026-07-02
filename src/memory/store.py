"""MemoryStore — 记忆文件的读写与事件发射。

Store 只负责文件系统操作和事件发射，不做任何语义理解或 RAG 索引。
外部模块通过 ``on_write()`` / ``on_delete()`` 注册回调，监听写/删事件
以实现后续处理（如索引入 RAG）。

用法:
    from src.config import config
    from src.memory.store import MemoryStore
    from src.memory.schemas import Memory

    store = MemoryStore()
    store.on_write(my_callback)

    file_path = store.write_memory("resume", memory)
    store.delete_memory("resume", file_path)
"""

from pathlib import Path

from src.config import config
from src.logger import get_logger
from src.memory.schemas import (
    Memory,
    MemoryWrittenEvent,
    MemoryDeletedEvent,
)
from src.utils.formatters import memory_to_markdown, timestamp_to_filename

logger = get_logger(__name__)


class MemoryStore:
    """记忆文件管理器 — 同步文件读写 + 观察者模式事件发射。

    每个 Memory 写入后生成一个时间戳命名的 ``.md`` 文件：
    ``{base_dir}/{agent}/{yyyyMMddHHmmss.fff}.md``。

    Attributes:
        base_dir: 存储根目录（绝对路径）。
    """

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or config.MEMORIES_BASE_DIR).resolve()
        self._write_callbacks: list[callable] = []
        self._delete_callbacks: list[callable] = []

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    def write_memory(self, agent: str, memory: Memory) -> str | None:
        """将一条 Memory 持久化为文件。

        取 ``memory.time`` 生成时间戳文件名，写入 front-matter
        （id / agent / time）+ 正文到 ``base_dir/agent/`` 目录下，
        成功后发射 ``MemoryWrittenEvent``。

        Args:
            agent: Agent 名称（决定子目录）。
            memory: 要写入的记忆对象。

        Returns:
            写入文件的绝对路径字符串；失败时返回 ``None`` 并记日志。
        """
        file_path = self.base_dir / agent / timestamp_to_filename(memory.time, memory.category)
        text = memory_to_markdown(agent, memory)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(text, encoding="utf-8")
        except Exception:
            logger.exception("写入记忆失败: %s", file_path)
            return None

        logger.info("记忆已写入: %s", file_path)
        self._emit_write(
            MemoryWrittenEvent(agent=agent, memory=memory, file_path=str(file_path))
        )
        return str(file_path)

    def delete_memory(self, agent: str, file_path: str) -> bool:
        """删除一个记忆文件。

        删除成功后发射 ``MemoryDeletedEvent``。

        Args:
            agent: Agent 名称。
            file_path: 要删除的文件绝对路径。

        Returns:
            删除成功返回 ``True``；文件不存在或异常返回 ``False`` 并记日志。
        """
        path = Path(file_path)
        try:
            path.unlink()
        except FileNotFoundError:
            logger.warning("删除记忆时文件不存在: %s", file_path)
            return False
        except Exception:
            logger.exception("删除记忆失败: %s", file_path)
            return False

        logger.info("记忆已删除: %s", file_path)
        self._emit_delete(
            MemoryDeletedEvent(agent=agent, file_path=str(file_path))
        )
        return True

    # ------------------------------------------------------------------
    # 事件注册
    # ------------------------------------------------------------------

    def on_write(self, callback) -> None:
        """注册写入事件回调。

        ``callback`` 签名需为 ``(MemoryWrittenEvent) -> None``，
        将在每次 ``write_memory()`` 成功后调用。

        Args:
            callback: 回调函数。
        """
        self._write_callbacks.append(callback)

    def on_delete(self, callback) -> None:
        """注册删除事件回调。

        ``callback`` 签名需为 ``(MemoryDeletedEvent) -> None``，
        将在每次 ``delete_memory()`` 成功后调用。

        Args:
            callback: 回调函数。
        """
        self._delete_callbacks.append(callback)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _emit_write(self, event: MemoryWrittenEvent) -> None:
        """发射 MemoryWrittenEvent，遍历所有写入回调。

        单个回调异常不影响其他回调，异常记日志后继续。
        """
        for callback in self._write_callbacks:
            try:
                callback(event)
            except Exception:
                logger.exception("write 回调执行失败: %s", callback.__name__)

    def _emit_delete(self, event: MemoryDeletedEvent) -> None:
        """发射 MemoryDeletedEvent，遍历所有删除回调。

        单个回调异常不影响其他回调，异常记日志后继续。
        """
        for callback in self._delete_callbacks:
            try:
                callback(event)
            except Exception:
                logger.exception("delete 回调执行失败: %s", callback.__name__)
