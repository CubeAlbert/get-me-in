"""Resume artifact aggregate coordinator."""

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from src.get_me_in.domain.artifacts import Artifact, ArtifactBuildAttempt, ArtifactKind, ArtifactOperation, ArtifactOperationKind, ArtifactOperationStatus
from src.get_me_in.ports.process import ProcessResult
from src.get_me_in.ports.resume_artifacts import ResumeArtifactBackend, TemplateCopyResult


class ArtifactPartialFailure(RuntimeError):
    def __init__(self, code: str, changed_paths: tuple[Path, ...], message: str) -> None:
        super().__init__(message)
        self.code, self.changed_paths = code, changed_paths


class ArtifactService:
    def __init__(self, backend: ResumeArtifactBackend, repository: object, clock: object, id_generator: object, log_max_bytes: int) -> None:
        self._backend, self._repository, self._clock, self._ids, self._log_max = backend, repository, clock, id_generator, log_max_bytes

    def copy_template(self, template: str, prefix: str, target_dir: Path, *, workspace, session_id: str, agent_key) -> TemplateCopyResult:
        key = ArtifactOperation.key_for(session_id=session_id, agent_key=agent_key, kind=ArtifactOperationKind.COPY_TEMPLATE, path=str(target_dir), input_hash=f"{template}:{prefix}")
        operation = ArtifactOperation(1, key, session_id, agent_key, ArtifactOperationKind.COPY_TEMPLATE, str(target_dir), f"{template}:{prefix}", ArtifactOperationStatus.PENDING, self._clock.now())
        self._repository.save_operation(operation)
        result = self._backend.copy_template(template, prefix, target_dir, workspace=workspace)
        artifacts = tuple(Artifact(1, self._ids.new_id(), session_id, agent_key, ArtifactKind.LATEX if path.suffix == ".tex" else ArtifactKind.README, str(path), self._repository.next_version(str(path)), sha256(workspace.read(path).content.encode()).hexdigest(), self._clock.now(), template if path.suffix == ".tex" else None) for path in result.files)
        try:
            self._repository.save_operation(replace(operation, status=ArtifactOperationStatus.COMMITTED, artifacts=artifacts))
        except Exception as error:
            raise ArtifactPartialFailure("metadata_commit_failed", result.files, str(error)) from error
        return result

    def build_pdf(self, path: Path, *, workspace, cancellation, session_id: str, agent_key) -> ProcessResult:
        revision = workspace.read(path).revision
        key = ArtifactOperation.key_for(session_id=session_id, agent_key=agent_key, kind=ArtifactOperationKind.BUILD_PDF, path=str(path), input_hash=revision)
        operation = ArtifactOperation(1, key, session_id, agent_key, ArtifactOperationKind.BUILD_PDF, str(path), revision, ArtifactOperationStatus.PENDING, self._clock.now())
        self._repository.save_operation(operation)
        result = self._backend.build_pdf(path, workspace=workspace, cancellation=cancellation)
        stdout, stdout_bytes, stdout_cut = self._bound_log(result.stdout, workspace)
        stderr, stderr_bytes, stderr_cut = self._bound_log(result.stderr, workspace)
        attempt = ArtifactBuildAttempt(1, self._ids.new_id(), key, session_id, agent_key, str(path), result.exit_code, stdout, stderr, stdout_bytes, stderr_bytes, stdout_cut, stderr_cut, result.timed_out, result.cancelled, self._clock.now())
        artifacts = ()
        pdf = path.with_suffix(".pdf")
        if result.exit_code == 0 and workspace.exists(pdf):
            snapshot = workspace.read(pdf)
            artifacts = (Artifact(1, self._ids.new_id(), session_id, agent_key, ArtifactKind.PDF, str(pdf), self._repository.next_version(str(pdf)), sha256(snapshot.content.encode()).hexdigest(), self._clock.now()),)
        try:
            self._repository.save_operation(replace(operation, status=ArtifactOperationStatus.COMMITTED, artifacts=artifacts, build_attempts=(attempt,)))
        except Exception as error:
            changed = (pdf,) if artifacts else ()
            raise ArtifactPartialFailure("metadata_commit_failed", changed, str(error)) from error
        return result

    def _bound_log(self, value: str, workspace) -> tuple[str, int, bool]:
        root = str(workspace.resolve(Path(".")))
        text = value.replace(root, "<workspace>").replace(root.replace("\\", "/"), "<workspace>")
        raw = text.encode("utf-8")
        if len(raw) <= self._log_max:
            return text, len(raw), False
        half = self._log_max // 2
        return (raw[:half].decode("utf-8", "ignore") + "\n...[truncated]...\n" + raw[-half:].decode("utf-8", "ignore"), len(raw), True)

    def close(self) -> None:
        self._repository.close()
