"""ArtifactService contract tests."""

from datetime import datetime, timezone
from hashlib import sha256
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

    def test_copy_hash_failure_after_write_is_a_partial_failure(self) -> None:
        self.workspace.hash_error = OSError("hash unavailable")

        with self.assertRaises(ArtifactPartialFailure) as raised:
            self.service.copy_template("chn", "resume", Path("."), workspace=self.workspace, session_id="s", agent_key=AgentKey.RESUME)

        self.assertEqual("metadata_commit_failed", raised.exception.code)
        self.assertEqual((Path("resume_CHN.tex"), Path("README.md")), raised.exception.changed_paths)
        self.assertIn(Path("resume_CHN.tex"), self.workspace.files)

    def test_build_records_exception_and_pending_retry_rebuilds_existing_pdf(self) -> None:
        self.workspace.files[Path("resume.tex")] = "source"
        self.backend.build_error = RuntimeError("compiler unavailable")
        first = self.service.build_pdf(Path("resume.tex"), workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME)
        replay = self.service.build_pdf(Path("resume.tex"), workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME)
        attempt = self.repository.list_build_attempts()[0]
        self.assertEqual(first, replay)
        self.assertIsNone(attempt.exit_code)
        self.assertIn("compiler unavailable", attempt.stderr)
        self.assertEqual(1, self.backend.build_calls)

        self.workspace.files[Path("resume2.tex")] = "source"
        self.workspace.files[Path("resume2.pdf")] = "stale-pdf"
        revision = self.workspace.read(Path("resume2.tex")).revision
        key = ArtifactOperation.key_for(session_id="s", agent_key=AgentKey.RESUME, kind=ArtifactOperationKind.BUILD_PDF, path="resume2.tex", input_hash=revision)
        self.repository.save_operation(ArtifactOperation(1, key, "s", AgentKey.RESUME, ArtifactOperationKind.BUILD_PDF, "resume2.tex", revision, ArtifactOperationStatus.PENDING, _Clock().now()))
        self.backend.build_error = None
        result = self.service.build_pdf(Path("resume2.tex"), workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME)
        self.assertEqual(0, result.exit_code)
        self.assertEqual("pdf", self.workspace.files[Path("resume2.pdf")])
        self.assertEqual(2, self.backend.build_calls)
        self.assertEqual(1, len(self.repository.list_artifacts("resume2.pdf")))

    def test_build_hash_failure_after_pdf_write_is_a_partial_failure(self) -> None:
        self.workspace.files[Path("resume.tex")] = "source"
        self.workspace.hash_error = OSError("hash unavailable")

        with self.assertRaises(ArtifactPartialFailure) as raised:
            self.service.build_pdf(Path("resume.tex"), workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME)

        self.assertEqual("metadata_commit_failed", raised.exception.code)
        self.assertEqual((Path("resume.pdf"),), raised.exception.changed_paths)
        self.assertIn(Path("resume.pdf"), self.workspace.files)

    def test_build_persists_non_success_process_outcomes_without_pdf_artifacts(self) -> None:
        cases = (
            ("failed.tex", ProcessResult(1, "out", "error")),
            ("timed.tex", ProcessResult(None, "out", "timeout", timed_out=True)),
            ("cancelled.tex", ProcessResult(None, "out", "cancelled", cancelled=True)),
        )
        self.backend.build_error = None
        for name, expected in cases:
            path = Path(name)
            self.workspace.files[path] = name
            self.backend.result = expected
            self.assertEqual(expected, self.service.build_pdf(path, workspace=self.workspace, cancellation=object(), session_id="s", agent_key=AgentKey.RESUME))

        attempts = {item.source_path: item for item in self.repository.list_build_attempts()}
        self.assertEqual((1, False, False), (attempts["failed.tex"].exit_code, attempts["failed.tex"].timed_out, attempts["failed.tex"].cancelled))
        self.assertEqual((None, True, False), (attempts["timed.tex"].exit_code, attempts["timed.tex"].timed_out, attempts["timed.tex"].cancelled))
        self.assertEqual((None, False, True), (attempts["cancelled.tex"].exit_code, attempts["cancelled.tex"].timed_out, attempts["cancelled.tex"].cancelled))
        self.assertEqual((), tuple(item for item in self.repository.list_artifacts() if item.kind.value == "pdf"))


class _Workspace:
    def __init__(self): self.files, self.hash_error = {}, None
    def exists(self, path): return path in self.files
    def read(self, path): return type("Snapshot", (), {"content": self.files[path], "revision": "revision:" + self.files[path]})()
    def write(self, path, content): self.files[path] = content
    def resolve(self, path): return Path("C:/workspace") / path
    def content_hash(self, path):
        if self.hash_error:
            raise self.hash_error
        return sha256(self.files[path].encode()).hexdigest()


class _Backend:
    def __init__(self, workspace): self.workspace, self.copy_calls, self.build_calls, self.build_error, self.result = workspace, 0, 0, None, ProcessResult(0, "ok", "")
    def copy_template(self, template, prefix, target_dir, *, workspace):
        tex, readme = target_dir / f"{prefix}_CHN.tex", target_dir / "README.md"
        if not workspace.exists(tex):
            self.copy_calls += 1
            workspace.write(tex, "template")
            workspace.write(readme, "readme")
        return TemplateCopyResult((tex, readme), target_dir)
    def build_pdf(self, path, *, workspace, cancellation):
        self.build_calls += 1
        if self.build_error: raise self.build_error
        if self.result.exit_code == 0:
            workspace.write(path.with_suffix(".pdf"), "pdf")
        return self.result


class _Clock:
    def now(self): return datetime(2026, 7, 27, tzinfo=timezone.utc)
class _Ids:
    def __init__(self): self.value = 0
    def new_id(self): self.value += 1; return str(self.value)
