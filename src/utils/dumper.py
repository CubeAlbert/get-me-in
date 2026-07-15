"""消息历史 dump 工具 — 将对话历史序列化为 JSON 文件，用于调试上下文丢失问题。"""

import json
from datetime import datetime
from pathlib import Path

from src.config import config
from src.logger import get_logger
from src.message import Message

logger = get_logger(__name__)


def dump_history(agent_name: str, history: list[Message]) -> str | None:
    """将对话历史 dump 到日志目录。

    Args:
        agent_name: Agent 名称（用于文件名前缀）。
        history: Message 列表。

    Returns:
        dump 文件的绝对路径，失败返回 None。
    """
    try:
        log_dir = Path(config.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent_name}_{ts}_message.dump"
        filepath = log_dir / filename

        data = [m.to_json() for m in history]
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.info("history dumped: %s (%d messages)", filepath, len(history))
        return str(filepath)
    except Exception:
        logger.exception("failed to dump history for %s", agent_name)
        return None
