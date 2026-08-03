"""R3 简历工具的端口契约测试。"""

import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

import pypdf

from src.get_me_in.adapters.local_resume_artifacts import LocalResumeArtifacts, ResumeArtifactError
from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.application.artifact_service import ArtifactPartialFailure
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolApproval, ToolFailure, ToolSuccess
from src.get_me_in.ports.process import ProcessResult
from src.get_me_in.ports.resume_artifacts import PdfMergeResult, TemplateCopyResult
from src.get_me_in.tools.resume import build_resume_tools


class ResumeToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = _Artifacts()
        self.executor = ToolExecutor(ToolCatalog(build_resume_tools()))
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken(), workspace=_Workspace(), resume_artifacts=self.artifacts)

    def test_copy_template_requires_approval_then_uses_injected_port(self) -> None:
        pending = self.executor.execute("call", "copy_template", {"template": "chn", "prefix": "resume"}, self.context)
        outcome = self.executor.execute("call", "copy_template", {"template": "chn", "prefix": "resume"}, self.context.__class__(**{**self.context.__dict__, "approved": True}))

        self.assertIsInstance(pending, ToolApproval)
        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual("chn", self.artifacts.template)
        self.assertEqual(("resume_CHN.tex", "README.md"), outcome.output["files"])

    def test_build_pdf_returns_process_result(self) -> None:
        approved = self.context.__class__(**{**self.context.__dict__, "approved": True})
        outcome = self.executor.execute("call", "build_pdf", {"path": "resume.tex"}, approved)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual(0, outcome.output["exit_code"])
        self.assertEqual(Path("resume.tex"), self.artifacts.build_path)

    def test_cancelled_build_is_a_typed_failure(self) -> None:
        self.artifacts.result = ProcessResult(None, "", "", cancelled=True)
        approved = self.context.__class__(**{**self.context.__dict__, "approved": True})

        outcome = self.executor.execute("call", "build_pdf", {"path": "resume.tex"}, approved)

        self.assertEqual(ToolFailure("build_pdf_cancelled", "PDF build was cancelled"), outcome)

    def test_build_exception_result_is_a_typed_failure(self) -> None:
        self.artifacts.result = ProcessResult(None, "", "compiler unavailable")
        approved = self.context.__class__(**{**self.context.__dict__, "approved": True})

        outcome = self.executor.execute("call", "build_pdf", {"path": "resume.tex"}, approved)

        self.assertEqual(
            ToolFailure("build_pdf_failed", "compiler unavailable"),
            outcome,
        )

    def test_merge_pdfs_requires_approval_and_normalizes_suffixes(self) -> None:
        pending = self.executor.execute(
            "call",
            "merge_pdfs",
            {"first": "resume_CHN", "second": "resume_EN.pdf", "output": "combined"},
            self.context,
        )
        approved = self.context.__class__(
            **{**self.context.__dict__, "approved": True}
        )

        outcome = self.executor.execute(
            "call",
            "merge_pdfs",
            {"first": "resume_CHN", "second": "resume_EN.pdf", "output": "combined"},
            approved,
        )

        self.assertIsInstance(pending, ToolApproval)
        self.assertEqual(
            ToolSuccess(
                {
                    "output": "combined.pdf",
                    "first": "resume_CHN.pdf",
                    "second": "resume_EN.pdf",
                    "total_pages": 4,
                }
            ),
            outcome,
        )
        self.assertEqual(
            (Path("resume_CHN.pdf"), Path("resume_EN.pdf"), Path("combined.pdf")),
            self.artifacts.merge_paths,
        )

    def test_partial_failure_reports_changed_paths(self) -> None:
        self.artifacts.error = ArtifactPartialFailure(
            "metadata_commit_failed",
            (Path("resume.tex"), Path("resume.pdf")),
            "metadata unavailable",
        )
        approved = self.context.__class__(**{**self.context.__dict__, "approved": True})

        outcome = self.executor.execute("call", "build_pdf", {"path": "resume.tex"}, approved)

        self.assertEqual(
            ToolFailure(
                "artifact_partial_failure",
                "metadata_commit_failed: metadata unavailable",
                "Files may have changed: resume.tex, resume.pdf",
            ),
            outcome,
        )

    def test_local_adapter_copies_requested_template_and_overwrites_readme(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            templates = root / "templates"
            templates.mkdir()
            (templates / "CHN_Template.tex").write_text("中文", encoding="utf-8")
            (templates / "EN_Template.tex").write_text("English", encoding="utf-8")
            (templates / "README.md").write_text("说明", encoding="utf-8")
            workspace = LocalWorkspace(root / "workspace")
            workspace.write(Path("resume/README.md"), "旧说明")
            adapter = LocalResumeArtifacts(templates, _Runner(), 60)

            result = adapter.copy_template("all", "candidate_CHN", Path("resume"), workspace=workspace)

            self.assertEqual((Path("resume/candidate_CHN.tex"), Path("resume/candidate_EN.tex"), Path("resume/README.md")), result.files)
            self.assertEqual("中文", workspace.read(Path("resume/candidate_CHN.tex")).content)
            self.assertEqual("说明", workspace.read(Path("resume/README.md")).content)

    def test_local_adapter_reports_missing_xelatex(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = LocalWorkspace(root / "workspace")
            workspace.write(Path("resume.tex"), "\\documentclass{article}")
            adapter = LocalResumeArtifacts(root, _Runner(), 60)

            with patch("src.get_me_in.adapters.local_resume_artifacts.shutil.which", return_value=None):
                with self.assertRaisesRegex(ResumeArtifactError, "未找到 xelatex"):
                    adapter.build_pdf(Path("resume.tex"), workspace=workspace, cancellation=CancellationToken())

    def test_local_adapter_uses_xelatex_and_preserves_process_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = LocalWorkspace(root / "workspace")
            workspace.write(Path("resume.tex"), "\\documentclass{article}")
            runner = _RecordingRunner()
            adapter = LocalResumeArtifacts(root, runner, 37)
            cancellation = CancellationToken()

            with patch("src.get_me_in.adapters.local_resume_artifacts.shutil.which", return_value="xelatex.exe"):
                result = adapter.build_pdf(Path("resume.tex"), workspace=workspace, cancellation=cancellation)

            self.assertEqual(ProcessResult(0, "", ""), result)
            self.assertEqual(
                ("xelatex.exe", "-no-shell-escape", "-synctex=1", "-interaction=nonstopmode", "resume.tex"),
                runner.command,
            )
            self.assertEqual(workspace.resolve(Path(".")), runner.cwd)
            self.assertEqual(37, runner.timeout_seconds)
            self.assertIs(cancellation, runner.cancellation)

    def test_local_adapter_merges_pdf_pages_in_requested_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = LocalWorkspace(root / "workspace")
            first = workspace.resolve(Path("resume_CHN.pdf"))
            second = workspace.resolve(Path("resume_EN.pdf"))
            first_writer = pypdf.PdfWriter()
            first_writer.add_blank_page(width=100, height=200)
            first_writer.write(first)
            first_writer.close()
            second_writer = pypdf.PdfWriter()
            second_writer.add_blank_page(width=300, height=400)
            second_writer.add_blank_page(width=500, height=600)
            second_writer.write(second)
            second_writer.close()
            adapter = LocalResumeArtifacts(root, _Runner(), 60)

            result = adapter.merge_pdfs(
                Path("resume_CHN"),
                Path("resume_EN.pdf"),
                Path("combined"),
                workspace=workspace,
            )

            merged = pypdf.PdfReader(workspace.resolve(result.output))
            self.assertEqual(3, result.total_pages)
            self.assertEqual(
                [(100, 200), (300, 400), (500, 600)],
                [
                    (int(page.mediabox.width), int(page.mediabox.height))
                    for page in merged.pages
                ],
            )

    def test_local_adapter_rejects_output_that_overwrites_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = LocalWorkspace(root / "workspace")
            writer = pypdf.PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(workspace.resolve(Path("resume.pdf")))
            writer.close()
            writer = pypdf.PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.write(workspace.resolve(Path("other.pdf")))
            writer.close()
            adapter = LocalResumeArtifacts(root, _Runner(), 60)

            with self.assertRaisesRegex(ResumeArtifactError, "不能覆盖"):
                adapter.merge_pdfs(
                    Path("resume.pdf"),
                    Path("other.pdf"),
                    Path("resume.pdf"),
                    workspace=workspace,
                )


class _Workspace:
    pass


class _Artifacts:
    template: str | None = None
    build_path: Path | None = None
    result = ProcessResult(0, "ok", "", False, False)
    error: ArtifactPartialFailure | None = None
    merge_paths: tuple[Path, Path, Path] | None = None

    def copy_template(self, template: str, prefix: str, target_dir: Path, *, workspace: _Workspace, session_id: str, agent_key: AgentKey) -> TemplateCopyResult:
        if self.error:
            raise self.error
        self.template = template
        return TemplateCopyResult((Path("resume_CHN.tex"), Path("README.md")), Path("."))

    def build_pdf(self, path: Path, *, workspace: _Workspace, cancellation: CancellationToken, session_id: str, agent_key: AgentKey) -> ProcessResult:
        if self.error:
            raise self.error
        self.build_path = path
        return self.result

    def merge_pdfs(self, first: Path, second: Path, output: Path, *, workspace: _Workspace, session_id: str, agent_key: AgentKey) -> PdfMergeResult:
        if self.error:
            raise self.error
        self.merge_paths = (first, second, output)
        return PdfMergeResult(first, second, output, 4)


class _Runner:
    def run(self, *args: object, **kwargs: object) -> ProcessResult:
        return ProcessResult(0, "", "")


class _RecordingRunner:
    command: tuple[str, ...] | None = None
    cwd: Path | None = None
    timeout_seconds: float | None = None
    cancellation: object | None = None

    def run(
        self,
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        cancellation: object,
    ) -> ProcessResult:
        self.command = command
        self.cwd = cwd
        self.timeout_seconds = timeout_seconds
        self.cancellation = cancellation
        return ProcessResult(0, "", "")
