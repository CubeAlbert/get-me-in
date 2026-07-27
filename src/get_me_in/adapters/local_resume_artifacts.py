"""基于静态模板和 ProcessRunner 的简历产物适配器。"""

import re
import shutil
from pathlib import Path

from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.process import ProcessResult, ProcessRunner
from src.get_me_in.ports.resume_artifacts import TemplateCopyResult
from src.get_me_in.ports.workspace import WorkspacePort


class ResumeArtifactError(ValueError):
    """简历产物适配器可预期的业务失败。"""


class LocalResumeArtifacts:
    """在 R7 前执行模板复制与 pdflatex 编译，但不持久化 Artifact 记录。"""

    _templates = {"chn": "CHN_Template.tex", "en": "EN_Template.tex"}

    def __init__(self, template_dir: Path, process_runner: ProcessRunner) -> None:
        self._template_dir = template_dir
        self._process_runner = process_runner

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
        pdflatex = shutil.which("pdflatex")
        if pdflatex is None:
            raise ResumeArtifactError("系统中未找到 pdflatex，无法编译 PDF")
        return self._process_runner.run(
            (pdflatex, "-synctex=1", "-interaction=nonstopmode", source.name),
            cwd=source.parent,
            timeout_seconds=60,
            cancellation=cancellation,
        )
