"""Authorized customer-file tool definition."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.external_files import ExternalFileReaderPort


class CustomerFileContext(ToolHandlerContext, Protocol):
    external_files: ExternalFileReaderPort | None


def build_customer_file_tools() -> tuple[ToolDefinition, ...]:
    return (ToolDefinition("read_customer_file", "读取用户显式授权的 txt、md、pdf 或 docx 文件。", ToolSchema({"path": str, "offset": int, "limit": int}, frozenset({"path"})), ToolPolicy(frozenset({Capability.EXTERNAL_FILE_READ}), ConfirmationMode.ALWAYS), _read),)


def _read(arguments: Mapping[str, object], context: CustomerFileContext) -> ToolSuccess | ToolFailure:
    if context.external_files is None:
        return ToolFailure("external_files_unavailable", "No user-authorized file reader is configured")
    path = Path(arguments["path"])
    if not path.is_absolute():
        return ToolFailure("external_path_not_absolute", "Customer file path must be absolute")
    offset, limit = arguments.get("offset", 1), arguments.get("limit", 100)
    if offset < 1 or limit < 1:
        return ToolFailure("invalid_range", "offset and limit must be positive")
    try:
        content = context.external_files.read(path)
    except (OSError, PermissionError, UnicodeError, ValueError) as error:
        return ToolFailure("external_file_read_failed", str(error))
    lines = content.text.splitlines()
    sliced = lines[offset - 1 : offset - 1 + limit]
    return ToolSuccess({"path": str(content.path), "format": content.format, "total_lines": len(lines), "offset": offset, "limit": limit, "truncated": offset - 1 + len(sliced) < len(lines), "lines": tuple((offset + index, value) for index, value in enumerate(sliced))})
