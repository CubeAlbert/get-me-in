"""ArtifactService contract tests."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.json_artifact_repository import JsonArtifactRepository
from src.get_me_in.application.artifact_service import ArtifactPartialFailure, ArtifactService
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.artifacts import ArtifactOperation, ArtifactOperationKind, ArtifactOperationStatus
from src.get_me_in.ports.process import ProcessResult
from src.get_me_in.ports.resume_artifacts import TemplateCopyResult


class ArtifactServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = _Workspace()
        self.backend = _Backend(self.workspace)
        self.repository = JsonArtifactRepository(Path(tempfile.mkdtemp()))
        self.service = ArtifactService(self.backend, self.repository, _Clock(), _Ids(), 64)

    def test_copy_retry_reconciles_pending_files_without_duplicate_writes(self) -> None:
        original_save = self.repository.save_operation
        failed = False
        def fail_first_commit(operation):
            nonlocal failed
            if operation.status is ArtifactOperationStatus.COMMITTED and not failed:
                failed = True
                raise OSError("metadata unavailable")
            original_save(operation)
        self.repository.save_operation = fail_first_commit
        with self.assertRaises(ArtifactPartialFailure):
            self.service.copy_template("chn", "resume", Path("."), workspace=self.workspace, session_id="s", agent_key=AgentKey.RESUME)

        self.repository.save_operation = original_save
        result = self.service.copy_template("chn", "resume", Path("."), workspace=self.workspace, session_id="s", agent_key=AgentKey.RESUME)

        self.assertEqual((Path("resume_CHN.tex"), Path("README.md")), result.files)
        self.assertEqual(1, self.backend.copy_calls)
        self.assertEqual(2, len(self.repository.list_artifacts()))

    def test_build_records_exception_and_reconciles_existing_pdf(self) -> None:
        self.workspace.files[Path("resume.tex")] = "source"
        self.backend.build_error = RuntimeError("compiler unavailable")
        with self.assertRaisesRegex(RuntimeError, "compiler unavailable"):
            self.service.build_pdf(Path("resume.tex"), workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME)
        attempt = self.repository.list_build_attempts()[0]
        self.assertIsNone(attempt.exit_code)
        self.assertIn("compiler unavailable", attempt.stderr)

        self.workspace.files[Path("resume2.tex")] = "source"
        self.workspace.files[Path("resume2.pdf")] = "pdf"
        revision = self.workspace.read(Path("resume2.tex")).revision
        key = ArtifactOperation.key_for(session_id="s", agent_key=AgentKey.RESUME, kind=ArtifactOperationKind.BUILD_PDF, path="resume2.tex", input_hash=revision)
        self.repository.save_operation(ArtifactOperation(1, key, "s", AgentKey.RESUME, ArtifactOperationKind.BUILD_PDF, "resume2.tex", revision, ArtifactOperationStatus.PENDING, _Clock().now()))
        result = self.service.build_pdf(Path("resume2.tex"), workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, len(self.repository.list_artifacts("resume2.pdf")))


class _Workspace:
    def __init__(self): self.files = {}
    def exists(self, path): return path in self.files
    def read(self, path): return type("Snapshot", (), {"content": self.files[path], "revision": "revision:" + self.files[path]})()
    def write(self, path, content): self.files[path] = content
    def resolve(self, path): return Path("C:/workspace") / path


class _Backend:
    def __init__(self, workspace): self.workspace, self.copy_calls, self.build_error = workspace, 0, None
    def copy_template(self, template, prefix, target_dir, *, workspace):
        tex, readme = target_dir / f"{prefix}_CHN.tex", target_dir / "README.md"
        if not workspace.exists(tex):
            self.copy_calls += 1
            workspace.write(tex, "template")
            workspace.write(readme, "readme")
        return TemplateCopyResult((tex, readme), target_dir)
    def build_pdf(self, path, *, workspace, cancellation):
        if self.build_error: raise self.build_error
        workspace.write(path.with_suffix(".pdf"), "pdf")
        return ProcessResult(0, "ok", "")


class _Clock:
    def now(self): return datetime(2026, 7, 27, tzinfo=timezone.utc)
class _Ids:
    def __init__(self): self.value = 0
    def new_id(self): self.value += 1; return str(self.value)
