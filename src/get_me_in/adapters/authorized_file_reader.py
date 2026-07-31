"""Local reader for files approved by the customer-file tool."""

from pathlib import Path

from charset_normalizer import from_bytes

from src.get_me_in.ports.external_files import ExternalFileContent


class AuthorizedFileReader:
    def read(self, path: Path) -> ExternalFileContent:
        resolved = path.resolve()
        if not resolved.is_absolute():
            raise ValueError("External file path must be absolute")
        suffix = resolved.suffix.lower()
        if suffix in {".txt", ".md"}:
            match = from_bytes(resolved.read_bytes()).best()
            if match is None:
                raise UnicodeError(f"Cannot detect text encoding for {path}")
            return ExternalFileContent(resolved, "text", str(match))
        if suffix == ".pdf":
            import pdfplumber
            with pdfplumber.open(resolved) as pdf:
                text = "\n\n".join(f"--- page {index} ---\n{page.extract_text() or ''}" for index, page in enumerate(pdf.pages, 1))
            return ExternalFileContent(resolved, "pdf", text)
        if suffix == ".docx":
            from docx import Document
            document = Document(str(resolved))
            return ExternalFileContent(resolved, "docx", "\n\n".join(item.text for item in document.paragraphs))
        raise ValueError(f"Unsupported external file format: {suffix}")
