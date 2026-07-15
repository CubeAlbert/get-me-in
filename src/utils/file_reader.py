"""文件读取底层工具 — 纯函数，不关心权限/审批/沙箱。

上层工具（workspace_*, read_customer_file）各自加约束。
"""

import fnmatch
import re

from pathlib import Path

from charset_normalizer import from_path


def read_text(path: Path, offset: int = 1, limit: int = 100) -> dict:
    """读取文本文件，返回结构化结果。

    Args:
        path: 文件绝对路径。
        offset: 起始行号（1-indexed），默认 1。
        limit: 最多返回行数，默认 100。

    Returns:
        {
            "path": str,           # 文件名（不含路径前缀）
            "total_lines": int,    # 文件总行数
            "offset": int,         # 本次起始行号
            "limit": int,          # 本次请求的最大行数
            "truncated": bool,     # true = 还有更多行未返回
            "lines": [[int, str]]  # [[行号, 内容], ...]，空行内容为 ""
        }

    Raises:
        FileNotFoundError: 文件不存在。
        IsADirectoryError: path 是目录。
        UnicodeDecodeError: 编码检测后仍无法解码。
    """
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"path is a directory: {path}")

    detected = from_path(path)
    content = str(detected.best())

    all_lines = content.split("\n")
    total = len(all_lines)

    start = max(offset, 1)
    end = start + limit
    sliced = all_lines[start - 1 : end - 1]
    truncated = start + len(sliced) < total

    lines = [[start + i, sliced[i]] for i in range(len(sliced))]

    return {
        "path": path.name,
        "total_lines": total,
        "offset": start,
        "limit": limit,
        "truncated": truncated,
        "lines": lines,
    }


def list_directory(path: Path) -> dict:
    """列出目录内容（单层，不递归）。

    Args:
        path: 目录绝对路径。

    Returns:
        {
            "path": str,
            "entries": [
                {"name": "sections", "type": "dir"},
                {"name": "main.tex", "type": "file"},
            ]
        }
        排序：目录在前文件在后，同类型按名称升序。

    Raises:
        FileNotFoundError: 目录不存在。
        NotADirectoryError: path 不是目录。
    """
    if not path.exists():
        raise FileNotFoundError(f"directory not found: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"path is not a directory: {path}")

    entries = []
    for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        entries.append({
            "name": entry.name,
            "type": "dir" if entry.is_dir() else "file",
        })

    return {
        "path": path.name or ".",
        "entries": entries,
    }


def read_pdf(path: Path) -> str:
    """用 pdfplumber 提取 PDF 纯文本。

    逐页提取，以 ``\\n\\n--- page N ---\\n\\n`` 分隔各页。
    不 OCR，不恢复排版，不做结构化。

    Returns:
        str: 提取的纯文本内容。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: PDF 损坏、加密或提取失败。
    """
    import pdfplumber

    try:
        with pdfplumber.open(path) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    pages.append(f"--- page {i} ---\n{text}")
            return "\n\n".join(pages)
    except Exception as e:
        raise ValueError(f"failed to extract text from PDF: {e}") from e


def read_docx(path: Path) -> str:
    """用 python-docx 提取 DOCX 纯文本。

    逐段落提取，段落间以 ``\\n\\n`` 分隔。
    仅支持 .docx，不支持旧版 .doc。

    Returns:
        str: 提取的纯文本内容。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 不支持 .doc 格式或解析失败。
    """
    from docx import Document

    if path.suffix.lower() == ".doc":
        raise ValueError("不支持 .doc 格式，请用 Word/WPS 另存为 .docx")

    try:
        doc = Document(str(path))
        paragraphs = [para.text for para in doc.paragraphs]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"failed to extract text from DOCX: {e}") from e


def search_text(
    root: Path,
    pattern: str,
    path: str = ".",
    glob: str | None = None,
    regex: bool = False,
    max_matches: int = 50,
) -> dict:
    """在工作区目录下搜索文本，返回结构化结果。

    Args:
        root: 工作区根目录（绝对路径）。
        pattern: 搜索字符串（或正则表达式）。
        path: 搜索范围（相对路径），文件或目录，默认 "."。
        glob: 文件名过滤 fnmatch 模式，如 "*.tex"。
        regex: pattern 是否为正则表达式。
        max_matches: 匹配结果上限，默认 50。

    Returns:
        {
            "pattern": str,
            "regex": bool,
            "path": str,
            "glob": str | null,
            "total_matches": int,
            "truncated": bool,
            "max_matches": int,
            "files": [{"path": str, "matches": [[int, str]]}],
        }

    Raises:
        FileNotFoundError: path 不存在。
        re.error: 正则语法错误。
    """
    root = root.resolve()
    target = (root / path).resolve()
    if not target.exists():
        raise FileNotFoundError(f"path not found: {path}")

    def _is_text_file(p: Path) -> bool:
        try:
            from_path(p)
            return True
        except Exception:
            return False

    def _glob_match(name: str) -> bool:
        if glob is None:
            return True
        return fnmatch.fnmatch(name, glob)

    # 收集要搜索的文件
    if target.is_file():
        files = [target]
    else:
        files = []
        for f in target.rglob("*"):
            if f.is_file() and _is_text_file(f) and _glob_match(f.name):
                files.append(f)

    # 用正则编译 pattern（如果 regex=True）
    compiled: re.Pattern | None = None
    if regex:
        compiled = re.compile(pattern)

    total_matches = 0
    truncated = False
    results: list[dict] = []

    for file_path in sorted(files, key=lambda p: str(p)):
        if truncated:
            break

        file_matches: list[list] = []
        try:
            detected = from_path(file_path)
            content = str(detected.best())
        except Exception:
            continue

        for line_num, line in enumerate(content.split("\n"), start=1):
            if truncated:
                break

            if compiled:
                matched = bool(compiled.search(line))
            else:
                matched = pattern in line

            if matched:
                total_matches += 1
                file_matches.append([line_num, line])
                if total_matches >= max_matches:
                    truncated = True
                    break

        if file_matches:
            rel_path = str(file_path.relative_to(root))
            results.append({"path": rel_path, "matches": file_matches})

    return {
        "pattern": pattern,
        "regex": regex,
        "path": path,
        "glob": glob,
        "total_matches": total_matches,
        "truncated": truncated,
        "max_matches": max_matches,
        "files": results,
    }
