"""read_customer_file — 读取用户文件系统任意位置的文件。

仅子 Agent 可用（排除 MainAgent），免审批，绝对路径。
支持 txt / md / pdf / docx，统一结构化输出。
"""

from pathlib import Path

from src.tools.registry import ConfirmMode, tool
from src.tools.exceptions import ToolCallException
from src.utils.file_reader import read_pdf, read_docx, read_text


def _text_to_lines(text: str, offset: int, limit: int) -> dict:
    """将纯文本按 \\n 拆分为结构化 lines 格式。"""
    all_lines = text.split("\n")
    total = len(all_lines)

    start = max(offset, 1)
    end = start + limit
    sliced = all_lines[start - 1 : end - 1]
    truncated = start + len(sliced) < total

    lines = [[start + i, sliced[i]] for i in range(len(sliced))]

    return {
        "total_lines": total,
        "offset": start,
        "limit": limit,
        "truncated": truncated,
        "lines": lines,
    }


@tool(
    purpose="读取用户文件系统中的文件（txt/md/pdf/docx），返回带行号的统一结构化内容。",
    use_when="需要读取用户提供的简历、JD 或其他文档时",
    do_not_use_when="需要读取工作区内的文件时 — 用 workspace_read",
    expected_output='{"path": "...", "format": "pdf", "total_lines": N, "lines": [[1, "..."], ...]}',
    input_schema={
        "path": {
            "description": (
                "文件的绝对路径（跨平台：Windows 用 C:\\...，Linux/macOS 用 /home/...）"
            ),
        },
        "offset": {
            "description": "起始行号（1-indexed），默认 1",
            "default": 1,
        },
        "limit": {
            "description": "最多返回的行数，默认 100",
            "default": 100,
        },
    },
    agent=["*"],
    confirm_mode=ConfirmMode.NEVER,
)
def read_customer_file(path: str, offset: int = 1, limit: int = 100) -> dict:
    p = Path(path)
    if not p.is_absolute():
        raise ToolCallException(
            f"path must be absolute, got: {path}",
            suggestion="请提供完整的绝对路径，如 C:\\Users\\xxx\\resume.pdf 或 /home/user/resume.pdf",
        )

    if not p.exists():
        raise ToolCallException(
            f"file not found: {path}",
            suggestion="请确认路径拼写正确且文件存在",
        )

    suffix = p.suffix.lower()

    if suffix in (".txt", ".md"):
        result = read_text(p, offset=offset, limit=limit)
        result["format"] = "text"
        return result

    if suffix == ".pdf":
        text = read_pdf(p)
        result = _text_to_lines(text, offset, limit)
        result["path"] = p.name
        result["format"] = "pdf"
        return result

    if suffix == ".docx":
        text = read_docx(p)
        result = _text_to_lines(text, offset, limit)
        result["path"] = p.name
        result["format"] = "docx"
        return result

    raise ToolCallException(
        f"unsupported format: {suffix}",
        suggestion="支持的格式: txt, md, pdf, docx",
    )
