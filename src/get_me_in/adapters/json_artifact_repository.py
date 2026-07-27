"""Atomic, versioned JSON storage for R7 artifacts."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.artifacts import Artifact, ArtifactBuildAttempt, ArtifactKind, ArtifactOperation, ArtifactOperationKind, ArtifactOperationStatus


class ArtifactRepositoryError(ValueError):
    pass


class JsonArtifactRepository:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._closed = False

    def get_operation(self, operation_key: str) -> ArtifactOperation | None:
        path = self._root / "operations" / f"{operation_key}.json"
        return None if not path.exists() else self._load_operation(path)

    def save_operation(self, operation: ArtifactOperation) -> None:
        self._validate_operation(operation)
        self._write(self._root / "operations" / f"{operation.operation_key}.json", operation)

    def next_version(self, path: str) -> int:
        return 1 + max((artifact.version for artifact in self.list_artifacts(path)), default=0)

    def list_artifacts(self, path: str | None = None) -> tuple[Artifact, ...]:
        records = tuple(
            artifact
            for file in self._files("operations")
            for artifact in self._load_operation(file).artifacts
        )
        return tuple(record for record in records if path is None or record.path == path)

    def list_build_attempts(self, source_path: str | None = None) -> tuple[ArtifactBuildAttempt, ...]:
        records = tuple(
            attempt
            for file in self._files("operations")
            for attempt in self._load_operation(file).build_attempts
        )
        return tuple(record for record in records if source_path is None or record.source_path == source_path)

    def close(self) -> None:
        self._closed = True

    def _files(self, directory: str) -> tuple[Path, ...]:
        root = self._root / directory
        return tuple(sorted(root.glob("*.json"))) if root.exists() else ()

    def _write(self, path: Path, value: object) -> None:
        if self._closed:
            raise RuntimeError("JsonArtifactRepository is closed")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(value), default=lambda item: item.value if hasattr(item, "value") else item.isoformat(), ensure_ascii=False, sort_keys=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            temporary.write(payload)
            temp_path = Path(temporary.name)
        temp_path.replace(path)

    @staticmethod
    def _read(path: Path) -> dict:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ArtifactRepositoryError(f"Artifact record must be an object: {path.name}")
            if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
                raise ArtifactRepositoryError(f"Unsupported artifact schema in {path.name}")
            return raw
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ArtifactRepositoryError(f"Corrupt artifact record: {path.name}") from error

    @classmethod
    def _load_operation(cls, path: Path) -> ArtifactOperation:
        try:
            operation = cls._operation(cls._read(path))
            cls._validate_operation(operation)
            return operation
        except ArtifactRepositoryError:
            raise
        except (AttributeError, KeyError, OverflowError, TypeError, ValueError) as error:
            raise ArtifactRepositoryError(f"Corrupt artifact record: {path.name}") from error

    @staticmethod
    def _operation(raw: dict) -> ArtifactOperation:
        operation = ArtifactOperation(
            1, raw["operation_key"], raw["session_id"], AgentKey(raw["agent_key"]),
            ArtifactOperationKind(raw["kind"]), raw["path"], raw["input_hash"],
            ArtifactOperationStatus(raw["status"]), datetime.fromisoformat(raw["created_at"]),
            tuple(JsonArtifactRepository._artifact(item) for item in raw.get("artifacts", ())),
            tuple(JsonArtifactRepository._attempt(item) for item in raw.get("build_attempts", ())),
        )
        return operation

    @staticmethod
    def _artifact(raw: dict) -> Artifact:
        if not isinstance(raw, dict) or type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
            raise ValueError("Unsupported nested artifact schema")
        return Artifact(1, raw["artifact_id"], raw["session_id"], AgentKey(raw["agent_key"]), ArtifactKind(raw["kind"]), raw["path"], raw["version"], raw["content_hash"], datetime.fromisoformat(raw["created_at"]), raw.get("template_name"))

    @staticmethod
    def _attempt(raw: dict) -> ArtifactBuildAttempt:
        if not isinstance(raw, dict) or type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
            raise ValueError("Unsupported nested build-attempt schema")
        return ArtifactBuildAttempt(1, raw["attempt_id"], raw["operation_key"], raw["session_id"], AgentKey(raw["agent_key"]), raw["source_path"], raw["exit_code"], raw["stdout"], raw["stderr"], raw["stdout_original_bytes"], raw["stderr_original_bytes"], raw["stdout_truncated"], raw["stderr_truncated"], raw["timed_out"], raw["cancelled"], datetime.fromisoformat(raw["created_at"]))

    @staticmethod
    def _validate_operation(operation: ArtifactOperation) -> None:
        if not isinstance(operation, ArtifactOperation):
            raise ArtifactRepositoryError("Artifact operation has an invalid type")
        if type(operation.schema_version) is not int or operation.schema_version != 1:
            raise ArtifactRepositoryError("Unsupported artifact operation schema")
        if (
            not _non_empty_string(operation.operation_key)
            or not _non_empty_string(operation.session_id)
            or not isinstance(operation.agent_key, AgentKey)
            or not isinstance(operation.kind, ArtifactOperationKind)
            or not _non_empty_string(operation.path)
            or not _non_empty_string(operation.input_hash)
            or not isinstance(operation.status, ArtifactOperationStatus)
            or not isinstance(operation.created_at, datetime)
        ):
            raise ArtifactRepositoryError("Artifact operation contains invalid fields")
        expected_key = ArtifactOperation.key_for(
            session_id=operation.session_id,
            agent_key=operation.agent_key,
            kind=operation.kind,
            path=operation.path,
            input_hash=operation.input_hash,
        )
        if operation.operation_key != expected_key:
            raise ArtifactRepositoryError("Artifact operation key does not match its inputs")
        if operation.status is ArtifactOperationStatus.PENDING and (
            operation.artifacts or operation.build_attempts
        ):
            raise ArtifactRepositoryError("Pending artifact operation cannot contain results")
        if operation.status is ArtifactOperationStatus.COMMITTED:
            if operation.kind is ArtifactOperationKind.COPY_TEMPLATE and (
                not operation.artifacts or operation.build_attempts
            ):
                raise ArtifactRepositoryError("Committed template copy has invalid results")
            if operation.kind is ArtifactOperationKind.BUILD_PDF and (
                len(operation.build_attempts) != 1
                or len(operation.artifacts) > 1
                or any(artifact.kind is not ArtifactKind.PDF for artifact in operation.artifacts)
            ):
                raise ArtifactRepositoryError("Committed PDF build has invalid results")
        if any(
            not isinstance(artifact, Artifact)
            or type(artifact.schema_version) is not int
            or artifact.schema_version != 1
            or not _non_empty_string(artifact.artifact_id)
            or artifact.session_id != operation.session_id
            or artifact.agent_key is not operation.agent_key
            or not isinstance(artifact.kind, ArtifactKind)
            or not _non_empty_string(artifact.path)
            or type(artifact.version) is not int
            or artifact.version < 1
            or not _non_empty_string(artifact.content_hash)
            or not isinstance(artifact.created_at, datetime)
            or artifact.template_name is not None
            and not _non_empty_string(artifact.template_name)
            for artifact in operation.artifacts
        ):
            raise ArtifactRepositoryError("Artifact result does not match its operation")
        if operation.kind is ArtifactOperationKind.COPY_TEMPLATE and any(
            artifact.kind not in {ArtifactKind.LATEX, ArtifactKind.README}
            for artifact in operation.artifacts
        ):
            raise ArtifactRepositoryError("Template copy contains an invalid artifact kind")
        if any(
            not isinstance(attempt, ArtifactBuildAttempt)
            or type(attempt.schema_version) is not int
            or attempt.schema_version != 1
            or not _non_empty_string(attempt.attempt_id)
            or attempt.operation_key != operation.operation_key
            or attempt.session_id != operation.session_id
            or attempt.agent_key is not operation.agent_key
            or attempt.source_path != operation.path
            or attempt.exit_code is not None
            and (type(attempt.exit_code) is not int)
            or not isinstance(attempt.stdout, str)
            or not isinstance(attempt.stderr, str)
            or type(attempt.stdout_original_bytes) is not int
            or attempt.stdout_original_bytes < 0
            or type(attempt.stderr_original_bytes) is not int
            or attempt.stderr_original_bytes < 0
            or not isinstance(attempt.stdout_truncated, bool)
            or not isinstance(attempt.stderr_truncated, bool)
            or not isinstance(attempt.timed_out, bool)
            or not isinstance(attempt.cancelled, bool)
            or not isinstance(attempt.created_at, datetime)
            for attempt in operation.build_attempts
        ):
            raise ArtifactRepositoryError("Build attempt does not match its operation")


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)
