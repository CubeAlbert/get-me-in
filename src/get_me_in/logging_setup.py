"""Explicit logging setup for the independent v2 package."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys


_LOGGER_NAME = "src.get_me_in"
_HANDLER_MARKER = "_get_me_in_v2_handler"


def configure_logging(log_dir: Path, level: str) -> Path:
    """Configure rotating file and stderr handlers for v2 and return the log path."""
    normalized_level = level.strip().upper()
    configured_level = logging.getLevelNamesMapping().get(normalized_level)
    if not isinstance(configured_level, int):
        raise ValueError(f"Unsupported log level: {level!r}")

    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / "app.log"

    package_logger = logging.getLogger(_LOGGER_NAME)
    package_logger.setLevel(logging.DEBUG)
    package_logger.propagate = False
    _remove_existing_handlers(package_logger)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(configured_level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    setattr(file_handler, _HANDLER_MARKER, True)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    setattr(stderr_handler, _HANDLER_MARKER, True)

    package_logger.addHandler(file_handler)
    package_logger.addHandler(stderr_handler)
    return log_path


def _remove_existing_handlers(logger: logging.Logger) -> None:
    for handler in tuple(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.close()
