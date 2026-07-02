"""记忆模块数据结构 — Memory、事件数据类及 Chunk 转换。

用法:
    from src.memory.schemas import (
        Memory,
        MemoryWrittenEvent, MemoryDeletedEvent,
        chunk_to_memory,
    )
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.logger import get_logger
from src.utils.chunker import Chunk

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 核心数据类
# ---------------------------------------------------------------------------


@dataclass
class Memory:
    """一条记忆，由 Agent 从对话中构建并持久化到文件。

    Attributes:
        content: 记忆正文，纯 Markdown 文本。
        agent: 所属 Agent 名称（如 ``"main"``、``"resume"``）。
        time: 记忆创建时间。
        id: uuid4 hex 字符串，全局唯一标识。
    """

    content: str
    agent: str = ""
    time: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


# ---------------------------------------------------------------------------
# 事件数据类（MemoryStore → MemoryIndexer 通信）
# ---------------------------------------------------------------------------


@dataclass
class MemoryWrittenEvent:
    """MemoryStore.write_memory() 完成后发射的事件。

    Attributes:
        agent: 所属 Agent 名称。
        memory: 写入的 Memory 对象。
        file_path: 写入的绝对文件路径。
    """

    agent: str
    memory: Memory
    file_path: str


@dataclass
class MemoryDeletedEvent:
    """MemoryStore.delete_memory() 完成后发射的事件。

    Attributes:
        agent: 所属 Agent 名称。
        file_path: 被删除的文件路径。
    """

    agent: str
    file_path: str


# ---------------------------------------------------------------------------
# 转换函数
# ---------------------------------------------------------------------------


def chunk_to_memory(chunk: Chunk) -> Memory:
    """将 RAG 检索返回的 Chunk 还原为 Memory 对象。

    从 ``chunk.metadata`` 提取 ``id``、``agent``、``time`` 字段，
    ``chunk.content`` 作为正文。metadata 缺失字段时使用默认值并记录警告。

    Args:
        chunk: RAG 检索返回的 Chunk，其 metadata 应包含 ``id``、``agent``、``time``。

    Returns:
        还原的 Memory 对象。
    """
    meta = chunk.metadata

    memory_id = meta.get("id", chunk.id)
    agent = meta.get("agent", "")
    if not agent:
        logger.warning("chunk_to_memory: metadata 缺少 agent，id=%s", memory_id)

    time_str = meta.get("time", "")
    try:
        time = datetime.fromisoformat(time_str)
    except (ValueError, TypeError):
        logger.warning(
            "chunk_to_memory: metadata.time 不可解析，使用当前时间，id=%s time=%s",
            memory_id,
            time_str,
        )
        time = datetime.now()

    return Memory(
        id=memory_id,
        agent=agent,
        time=time,
        content=chunk.content,
    )
