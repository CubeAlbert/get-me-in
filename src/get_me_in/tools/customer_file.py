"""Authorized customer-file tool definition."""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolParameter, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.external_files import ExternalFileReaderPort


class CustomerFileContext(ToolHandlerContext, Protocol):
    external_files: ExternalFileReaderPort | None


def build_customer_file_tools() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition(
            name="read_customer_file",
            purpose="读取用户文件系统中的文件（txt/md/pdf/docx），返回带行号的统一结构化内容。",
            use_when="需要读取用户提供的简历、JD 或其他文档时",
            do_not_use_when="需要读取当前受限工作区内的文件时；本工具只读取用户明确提供的外部绝对路径",
            expected_output='{"path": "...", "format": "pdf", "total_lines": N, "lines": [[1, "..."], ...]}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "文件的绝对路径（跨平台：Windows 用 C:\\...，Linux/macOS 用 /home/...）",
                    ),
                    "offset": ToolParameter(
                        int,
                        "起始行号（1-indexed），默认 1",
                        default=1,
                    ),
                    "limit": ToolParameter(
                        int,
                        "最多返回的行数，默认 100",
                        default=100,
                    ),
                },
                frozenset({"path"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.EXTERNAL_FILE_READ}),
                ConfirmationMode.ALWAYS,
            ),
            handler=_read,
        ),
    )


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
