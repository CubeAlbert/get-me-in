"""Aggregate JSON artifact repository contracts."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.json_artifact_repository import ArtifactRepositoryError, JsonArtifactRepository
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.artifacts import Artifact, ArtifactKind, ArtifactOperation, ArtifactOperationKind, ArtifactOperationStatus
from src.get_me_in.application.artifact_service import ArtifactService
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.ports.process import ProcessResult


class JsonArtifactRepositoryTests(unittest.TestCase):
    def test_committed_operation_atomically_exposes_its_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonArtifactRepository(Path(temporary))
            pending = _operation(ArtifactOperationStatus.PENDING)
            repository.save_operation(pending)
            self.assertEqual((), repository.list_artifacts())

            committed = _operation(ArtifactOperationStatus.COMMITTED, artifacts=(_artifact(),))
            repository.save_operation(committed)

            self.assertEqual(committed, repository.get_operation(committed.operation_key))
            self.assertEqual((_artifact(),), repository.list_artifacts("resume.tex"))
            self.assertEqual(2, repository.next_version("resume.tex"))

    def test_operation_key_is_stable_for_canonical_inputs(self) -> None:
        self.assertEqual(
            ArtifactOperation.key_for(session_id="s", agent_key=AgentKey.RESUME, kind=ArtifactOperationKind.COPY_TEMPLATE, path="resume.tex", input_hash="h"),
            ArtifactOperation.key_for(session_id="s", agent_key=AgentKey.RESUME, kind=ArtifactOperationKind.COPY_TEMPLATE, path="resume.tex", input_hash="h"),
        )

    def test_corrupt_operation_is_typed_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "operations"
            root.mkdir()
            (root / "bad.json").write_text("{", encoding="utf-8")
            with self.assertRaises(ArtifactRepositoryError):
                JsonArtifactRepository(Path(temporary)).list_artifacts()

    def test_build_records_bounded_attempt_in_committed_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonArtifactRepository(Path(temporary))
            service = ArtifactService(_Backend(), repository, _Clock(), _Ids(), 64)
            result = service.build_pdf(Path("resume.tex"), workspace=_Workspace(), cancellation=CancellationToken(), session_id="s", agent_key=AgentKey.RESUME)
            attempt = repository.list_build_attempts()[0]
            self.assertEqual(0, result.exit_code)
            self.assertTrue(attempt.stdout_truncated)
            self.assertIn("<workspace>", attempt.stdout)


def _operation(status, artifacts=()):
    return ArtifactOperation(1, "operation", "session", AgentKey.RESUME, ArtifactOperationKind.COPY_TEMPLATE, "resume.tex", "hash", status, _now(), artifacts)


def _artifact():
    return Artifact(1, "artifact", "session", AgentKey.RESUME, ArtifactKind.LATEX, "resume.tex", 1, "hash", _now(), "CHN_Template.tex")


def _now():
    return datetime(2026, 7, 27, tzinfo=timezone.utc)

class _Clock:
    def now(self): return _now()
class _Ids:
    def __init__(self): self.value = 0
    def new_id(self): self.value += 1; return str(self.value)
class _Workspace:
    def read(self, path): return type("S", (), {"revision": "r", "content": "pdf"})()
    def exists(self, path): return path.suffix == ".pdf"
    def resolve(self, path): return Path("C:/workspace") / path
    def content_hash(self, path): return sha256(b"pdf").hexdigest()
class _Backend:
    def build_pdf(self, path, *, workspace, cancellation): return ProcessResult(0, "C:/workspace/" + "x" * 100, "")
