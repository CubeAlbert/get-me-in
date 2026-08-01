"""Explicit logging setup for the independent v2 package."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys


_LOGGER_NAME = "src.get_me_in"
_HANDLER_MARKER = "_get_me_in_v2_handler"
_FILE_ONLY_MARKER = "_get_me_in_file_only"


class _StderrFormatter(logging.Formatter):
    """Keep terminal errors visible without adding ANSI to redirected output."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        is_tty = getattr(sys.stderr, "isatty", lambda: False)()
        if record.levelno >= logging.ERROR and is_tty:
            return f"\x1b[31m{message}\x1b[0m"
        return message


def configure_logging(
    log_dir: Path,
    level: str,
    file_name: str,
    max_bytes: int,
    backup_count: int,
) -> Path:
    """Configure rotating file and stderr handlers for v2 and return the log path."""
    normalized_level = level.strip().upper()
    configured_level = logging.getLevelNamesMapping().get(normalized_level)
    if not isinstance(configured_level, int):
        raise ValueError(f"Unsupported log level: {level!r}")

    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    if not file_name or Path(file_name).name != file_name or file_name in {".", ".."}:
        raise ValueError("file_name must be a single ordinary file name")
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")
    if backup_count < 0:
        raise ValueError("backup_count must not be negative")
    log_path = target_dir / file_name

    package_logger = logging.getLogger(_LOGGER_NAME)
    package_logger.setLevel(logging.DEBUG)
    package_logger.propagate = False
    _remove_existing_handlers(package_logger)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
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
    stderr_handler.addFilter(_exclude_file_only_records)
    stderr_handler.setFormatter(_StderrFormatter("%(levelname)s | %(message)s"))
    setattr(stderr_handler, _HANDLER_MARKER, True)

    package_logger.addHandler(file_handler)
    package_logger.addHandler(stderr_handler)
    return log_path


def _remove_existing_handlers(logger: logging.Logger) -> None:
    for handler in tuple(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.close()


def _exclude_file_only_records(record: logging.LogRecord) -> bool:
    return not bool(getattr(record, _FILE_ONLY_MARKER, False))
