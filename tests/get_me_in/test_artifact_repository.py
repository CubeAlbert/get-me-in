"""Aggregate JSON artifact repository contracts."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.json_artifact_repository import ArtifactRepositoryError, JsonArtifactRepository
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.artifacts import Artifact, ArtifactKind, ArtifactOperation, ArtifactOperationKind, ArtifactOperationStatus


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


def _operation(status, artifacts=()):
    return ArtifactOperation(1, "operation", "session", AgentKey.RESUME, ArtifactOperationKind.COPY_TEMPLATE, "resume.tex", "hash", status, _now(), artifacts)


def _artifact():
    return Artifact(1, "artifact", "session", AgentKey.RESUME, ArtifactKind.LATEX, "resume.tex", 1, "hash", _now(), "CHN_Template.tex")


def _now():
    return datetime(2026, 7, 27, tzinfo=timezone.utc)
