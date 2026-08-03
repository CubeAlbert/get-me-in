"""基于静态模板和 ProcessRunner 的简历产物适配器。"""

import os
import re
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import pypdf

from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.process import ProcessResult, ProcessRunner
from src.get_me_in.ports.resume_artifacts import PdfMergeResult, TemplateCopyResult
from src.get_me_in.ports.workspace import WorkspacePort


class ResumeArtifactError(ValueError):
    """简历产物适配器可预期的业务失败。"""


class LocalResumeArtifacts:
    """执行模板复制与 XeLaTeX 编译，但不持久化 Artifact 记录。"""

    _templates = {"chn": "CHN_Template.tex", "en": "EN_Template.tex"}

    def __init__(self, template_dir: Path, process_runner: ProcessRunner, build_timeout_seconds: float) -> None:
        self._template_dir = template_dir
        self._process_runner = process_runner
        self._build_timeout_seconds = build_timeout_seconds

    def copy_template(
        self, template: str, prefix: str, target_dir: Path, *, workspace: WorkspacePort
    ) -> TemplateCopyResult:
        if template not in {"chn", "en", "all"}:
            raise ResumeArtifactError("template 必须是 chn、en 或 all")
        prefix = re.sub(r"(_CHN|_EN)+$", "", prefix)
        if not prefix:
            raise ResumeArtifactError("prefix 不能为空")
        targets: list[tuple[Path, Path]] = []
        if template in {"chn", "all"}:
            targets.append((self._template_dir / self._templates["chn"], target_dir / f"{prefix}_CHN.tex"))
        if template in {"en", "all"}:
            targets.append((self._template_dir / self._templates["en"], target_dir / f"{prefix}_EN.tex"))
        readme = self._template_dir / "README.md"
        for source, destination in targets:
            if not source.is_file():
                raise ResumeArtifactError(f"模板文件不存在: {source.name}")
            if workspace.exists(destination) and workspace.read(destination).content != source.read_text(encoding="utf-8"):
                raise ResumeArtifactError(f"目标文件已存在: {destination}")
        if not readme.is_file():
            raise ResumeArtifactError("模板说明不存在: README.md")
        for source, destination in targets:
            content = source.read_text(encoding="utf-8")
            if not workspace.exists(destination):
                workspace.write(destination, content)
        workspace.write(target_dir / "README.md", readme.read_text(encoding="utf-8"))
        return TemplateCopyResult(tuple(destination for _, destination in targets) + (target_dir / "README.md",), target_dir)

    def build_pdf(
        self, path: Path, *, workspace: WorkspacePort, cancellation: CancellationSignal
    ) -> ProcessResult:
        source = workspace.resolve(path)
        if not source.is_file():
            raise ResumeArtifactError(f"文件不存在: {path}")
        if source.suffix.lower() != ".tex":
            raise ResumeArtifactError("build_pdf 仅支持 .tex 文件")
        xelatex = shutil.which("xelatex")
        if xelatex is None:
            raise ResumeArtifactError("系统中未找到 xelatex，无法编译 PDF")
        return self._process_runner.run(
            (
                xelatex,
                "-no-shell-escape",
                "-synctex=1",
                "-interaction=nonstopmode",
                source.name,
            ),
            cwd=source.parent,
            timeout_seconds=self._build_timeout_seconds,
            cancellation=cancellation,
        )

    def merge_pdfs(
        self,
        first: Path,
        second: Path,
        output: Path,
        *,
        workspace: WorkspacePort,
    ) -> PdfMergeResult:
        first, second, output = (
            _ensure_pdf_suffix(path) for path in (first, second, output)
        )
        first_path = workspace.resolve(first)
        second_path = workspace.resolve(second)
        output_path = workspace.resolve(output)
        for label, path in (("first", first_path), ("second", second_path)):
            if not path.is_file():
                raise ResumeArtifactError(f"PDF 文件不存在 ({label}): {path.name}")
        if first_path == second_path:
            raise ResumeArtifactError("两份源 PDF 路径相同，无法合并")
        if output_path in {first_path, second_path}:
            raise ResumeArtifactError("输出 PDF 不能覆盖任一源 PDF")

        writer = pypdf.PdfWriter()
        total_pages = 0
        try:
            for label, path in (("first", first_path), ("second", second_path)):
                try:
                    reader = pypdf.PdfReader(path)
                    for page in reader.pages:
                        writer.add_page(page)
                        total_pages += 1
                except Exception as error:
                    raise ResumeArtifactError(
                        f"读取 PDF 失败 ({label}): {path.name} — {error}"
                    ) from error

            output_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path: Path | None = None
            try:
                with NamedTemporaryFile(
                    "wb", dir=output_path.parent, delete=False
                ) as temporary:
                    temporary_path = Path(temporary.name)
                    writer.write(temporary)
                os.replace(temporary_path, output_path)
            except Exception as error:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)
                raise ResumeArtifactError(
                    f"写入合并 PDF 失败: {output.name} — {error}"
                ) from error
        finally:
            writer.close()
        return PdfMergeResult(first, second, output, total_pages)


def _ensure_pdf_suffix(path: Path) -> Path:
    return path if path.suffix.lower() == ".pdf" else path.with_name(f"{path.name}.pdf")
