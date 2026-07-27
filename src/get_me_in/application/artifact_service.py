"""Resume artifact aggregate coordinator."""

from dataclasses import replace
from hashlib import sha256
import json
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
        path = target_dir.as_posix()
        input_hash = self._input_hash(template=template, prefix=prefix)
        key = ArtifactOperation.key_for(session_id=session_id, agent_key=agent_key, kind=ArtifactOperationKind.COPY_TEMPLATE, path=path, input_hash=input_hash)
        operation = self._operation(key, session_id, agent_key, ArtifactOperationKind.COPY_TEMPLATE, path, input_hash)
        existing = self._repository.get_operation(key)
        if existing is not None and existing.status is ArtifactOperationStatus.COMMITTED:
            return TemplateCopyResult(tuple(Path(item.path) for item in existing.artifacts), target_dir)
        if existing is None:
            self._repository.save_operation(operation)
        else:
            operation = existing
        result = self._backend.copy_template(template, prefix, target_dir, workspace=workspace)
        artifacts = tuple(self._artifact(path, session_id, agent_key, workspace, template) for path in result.files)
        try:
            self._repository.save_operation(replace(operation, status=ArtifactOperationStatus.COMMITTED, artifacts=artifacts))
        except Exception as error:
            raise ArtifactPartialFailure("metadata_commit_failed", result.files, str(error)) from error
        return result

    def build_pdf(self, path: Path, *, workspace, cancellation, session_id: str, agent_key) -> ProcessResult:
        revision = workspace.read(path).revision
        source_path = path.as_posix()
        key = ArtifactOperation.key_for(session_id=session_id, agent_key=agent_key, kind=ArtifactOperationKind.BUILD_PDF, path=source_path, input_hash=revision)
        operation = self._operation(key, session_id, agent_key, ArtifactOperationKind.BUILD_PDF, source_path, revision)
        existing = self._repository.get_operation(key)
        if existing is not None and existing.status is ArtifactOperationStatus.COMMITTED:
            attempt = existing.build_attempts[-1]
            return ProcessResult(attempt.exit_code, attempt.stdout, attempt.stderr, attempt.timed_out, attempt.cancelled)
        if existing is None:
            self._repository.save_operation(operation)
        else:
            operation = existing
        pdf = path.with_suffix(".pdf")
        if existing is not None and workspace.exists(pdf):
            return self._commit_reconciled_pdf(operation, path, pdf, workspace)
        backend_error: Exception | None = None
        try:
            result = self._backend.build_pdf(path, workspace=workspace, cancellation=cancellation)
        except Exception as error:
            backend_error = error
            result = ProcessResult(None, "", str(error))
        stdout, stdout_bytes, stdout_cut = self._bound_log(result.stdout, workspace)
        stderr, stderr_bytes, stderr_cut = self._bound_log(result.stderr, workspace)
        attempt = ArtifactBuildAttempt(1, self._ids.new_id(), operation.operation_key, session_id, agent_key, source_path, result.exit_code, stdout, stderr, stdout_bytes, stderr_bytes, stdout_cut, stderr_cut, result.timed_out, result.cancelled, self._clock.now())
        artifacts = ()
        if result.exit_code == 0 and workspace.exists(pdf):
            artifacts = (self._artifact(pdf, session_id, agent_key, workspace),)
        try:
            self._repository.save_operation(replace(operation, status=ArtifactOperationStatus.COMMITTED, artifacts=artifacts, build_attempts=(attempt,)))
        except Exception as error:
            changed = (pdf,) if artifacts else ()
            raise ArtifactPartialFailure("metadata_commit_failed", changed, str(error)) from error
        if backend_error is not None:
            raise backend_error
        return result

    def _bound_log(self, value: str, workspace) -> tuple[str, int, bool]:
        root = str(workspace.resolve(Path(".")))
        text = value.replace(root, "<workspace>").replace(root.replace("\\", "/"), "<workspace>")
        raw = text.encode("utf-8")
        if len(raw) <= self._log_max:
            return text, len(raw), False
        marker = b"\n...[truncated]...\n"
        payload_bytes = max(0, self._log_max - len(marker))
        head_bytes = payload_bytes // 2
        tail_bytes = payload_bytes - head_bytes
        return (raw[:head_bytes].decode("utf-8", "ignore") + marker.decode() + raw[-tail_bytes:].decode("utf-8", "ignore"), len(raw), True)

    def _operation(self, key, session_id, agent_key, kind, path, input_hash) -> ArtifactOperation:
        return ArtifactOperation(1, key, session_id, agent_key, kind, path, input_hash, ArtifactOperationStatus.PENDING, self._clock.now())

    def _artifact(self, path: Path, session_id: str, agent_key, workspace, template: str | None = None) -> Artifact:
        snapshot = workspace.read(path)
        kind = ArtifactKind.LATEX if path.suffix == ".tex" else ArtifactKind.PDF if path.suffix == ".pdf" else ArtifactKind.README
        template_name = None
        if kind is ArtifactKind.LATEX:
            template_name = {"chn": "CHN_Template.tex", "en": "EN_Template.tex"}.get(template)
        return Artifact(1, self._ids.new_id(), session_id, agent_key, kind, path.as_posix(), self._repository.next_version(path.as_posix()), sha256(snapshot.content.encode()).hexdigest(), self._clock.now(), template_name)

    def _commit_reconciled_pdf(self, operation: ArtifactOperation, path: Path, pdf: Path, workspace) -> ProcessResult:
        message = "Reconciled existing PDF output after an incomplete artifact operation."
        stdout, stdout_bytes, stdout_cut = self._bound_log(message, workspace)
        attempt = ArtifactBuildAttempt(1, self._ids.new_id(), operation.operation_key, operation.session_id, operation.agent_key, path.as_posix(), 0, stdout, "", stdout_bytes, 0, stdout_cut, False, False, False, self._clock.now())
        artifact = self._artifact(pdf, operation.session_id, operation.agent_key, workspace)
        try:
            self._repository.save_operation(replace(operation, status=ArtifactOperationStatus.COMMITTED, artifacts=(artifact,), build_attempts=(attempt,)))
        except Exception as error:
            raise ArtifactPartialFailure("metadata_commit_failed", (pdf,), str(error)) from error
        return ProcessResult(0, message, "")

    @staticmethod
    def _input_hash(**parameters: str) -> str:
        return sha256(json.dumps(parameters, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()

    def close(self) -> None:
        self._repository.close()
