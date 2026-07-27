"""R3 简历工具的端口契约测试。"""

import unittest
from pathlib import Path
import tempfile

from src.get_me_in.adapters.local_resume_artifacts import LocalResumeArtifacts
from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolFailure, ToolInteraction, ToolSuccess
from src.get_me_in.ports.process import ProcessResult
from src.get_me_in.ports.resume_artifacts import TemplateCopyResult
from src.get_me_in.tools.resume import build_resume_tools


class ResumeToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = _Artifacts()
        self.executor = ToolExecutor(ToolCatalog(build_resume_tools()))
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken(), workspace=_Workspace(), resume_artifacts=self.artifacts)

    def test_copy_template_requires_approval_then_uses_injected_port(self) -> None:
        pending = self.executor.execute("call", "copy_template", {"template": "chn", "prefix": "resume"}, self.context)
        outcome = self.executor.execute("call", "copy_template", {"template": "chn", "prefix": "resume"}, self.context.__class__(**{**self.context.__dict__, "approved": True}))

        self.assertIsInstance(pending, ToolInteraction)
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
            adapter = LocalResumeArtifacts(templates, _Runner())

            result = adapter.copy_template("all", "candidate_CHN", Path("resume"), workspace=workspace)

            self.assertEqual((Path("resume/candidate_CHN.tex"), Path("resume/candidate_EN.tex"), Path("resume/README.md")), result.files)
            self.assertEqual("中文", workspace.read(Path("resume/candidate_CHN.tex")).content)
            self.assertEqual("说明", workspace.read(Path("resume/README.md")).content)


class _Workspace:
    pass


class _Artifacts:
    template: str | None = None
    build_path: Path | None = None
    result = ProcessResult(0, "ok", "", False, False)

    def copy_template(self, template: str, prefix: str, target_dir: Path, *, workspace: _Workspace, session_id: str, agent_key: AgentKey) -> TemplateCopyResult:
        self.template = template
        return TemplateCopyResult((Path("resume_CHN.tex"), Path("README.md")), Path("."))

    def build_pdf(self, path: Path, *, workspace: _Workspace, cancellation: CancellationToken, session_id: str, agent_key: AgentKey) -> ProcessResult:
        self.build_path = path
        return self.result


class _Runner:
    def run(self, *args: object, **kwargs: object) -> ProcessResult:
        return ProcessResult(0, "", "")
