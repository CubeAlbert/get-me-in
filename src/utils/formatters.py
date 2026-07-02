"""通用格式化工具 — 记忆文件名生成与 front-matter 拼装。

用法:
    from src.utils.formatters import memory_to_markdown, timestamp_to_filename

    name = timestamp_to_filename(memory.time)
    text = memory_to_markdown("resume", memory)
"""

from datetime import datetime


def timestamp_to_filename(time: datetime) -> str:
    """根据 datetime 生成记忆文件名。

    格式：``yyyyMMddHHmmss.fff.md``，毫秒保留 3 位。
    """
    return time.strftime("%Y%m%d%H%M%S.") + f"{time.microsecond // 1000:03d}.md"


def memory_to_markdown(agent: str, memory) -> str:
    """将 Memory 对象格式化为带 front-matter 的 Markdown 文本。

    输出示例::

        ---
        id: a1b2c3d4...
        agent: resume
        time: 2026-07-02T15:30:45.123456
        ---

        正文内容...

    Args:
        agent: Agent 名称。
        memory: Memory 对象，需有 ``id``、``time``、``content`` 属性。

    Returns:
        格式化后的完整文本，可直接写入 ``.md`` 文件。
    """
    return "\n".join([
        "---",
        f"id: {memory.id}",
        f"agent: {agent}",
        f"time: {memory.time.isoformat()}",
        "---",
        "",
        memory.content,
    ])
