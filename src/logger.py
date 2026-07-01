"""日志模块 — 横切基础设施，封装 logging 标准库。

提供 get_logger(name) 单一入口，首次调用自动初始化 handler 和格式。
所有模块通过 `logger = get_logger(__name__)` 获取 logger，
禁止使用 print() 调试。

用法:
    from src.logger import get_logger

    logger = get_logger(__name__)
    logger.info("RAG 加载完成，共 156 条记录")
    logger.warning("Chroma 查询返回空结果，降级为纯 LLM 回复")
    logger.error("写入记忆文件失败", exc_info=True)
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from src.config import config

_initialized = False


def get_logger(name: str) -> logging.Logger:
    """获取命名 logger，首次调用自动初始化日志系统。

    初始化是幂等的 — 后续调用不会重复创建 handler。
    """
    global _initialized
    if not _initialized:
        _setup()
        _initialized = True
    return logging.getLogger(name)


def _setup() -> None:
    """内部初始化：读 config → 创建 handler → 绑定 root logger。

    - 文件 handler：RotatingFileHandler，10MB × 5 备份，写入 data/logs/app.log
    - 控制台 handler：StreamHandler(stderr)，仅 WARNING+ 级别，不干扰 rich 的 stdout
    """
    log_dir = Path(config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # root 设最低，由各 handler 控制实际级别

    # 文件 handler — 记录所有 >= LOG_LEVEL 的消息
    fh = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # stderr handler — WARNING+ 输出到控制台，不干扰 rich 的 stdout
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(fmt)
    root.addHandler(ch)
