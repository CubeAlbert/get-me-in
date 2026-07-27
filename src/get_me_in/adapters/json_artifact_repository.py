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
            if raw.get("schema_version") != 1:
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
        if raw.get("schema_version") != 1:
            raise ValueError("Unsupported nested artifact schema")
        return Artifact(1, raw["artifact_id"], raw["session_id"], AgentKey(raw["agent_key"]), ArtifactKind(raw["kind"]), raw["path"], raw["version"], raw["content_hash"], datetime.fromisoformat(raw["created_at"]), raw.get("template_name"))

    @staticmethod
    def _attempt(raw: dict) -> ArtifactBuildAttempt:
        if raw.get("schema_version") != 1:
            raise ValueError("Unsupported nested build-attempt schema")
        return ArtifactBuildAttempt(1, raw["attempt_id"], raw["operation_key"], raw["session_id"], AgentKey(raw["agent_key"]), raw["source_path"], raw["exit_code"], raw["stdout"], raw["stderr"], raw["stdout_original_bytes"], raw["stderr_original_bytes"], raw["stdout_truncated"], raw["stderr_truncated"], raw["timed_out"], raw["cancelled"], datetime.fromisoformat(raw["created_at"]))

    @staticmethod
    def _validate_operation(operation: ArtifactOperation) -> None:
        if operation.schema_version != 1:
            raise ArtifactRepositoryError("Unsupported artifact operation schema")
        if operation.status is ArtifactOperationStatus.PENDING and (
            operation.artifacts or operation.build_attempts
        ):
            raise ArtifactRepositoryError("Pending artifact operation cannot contain results")
        if any(
            artifact.schema_version != 1
            or artifact.session_id != operation.session_id
            or artifact.agent_key is not operation.agent_key
            for artifact in operation.artifacts
        ):
            raise ArtifactRepositoryError("Artifact result does not match its operation")
        if any(
            attempt.schema_version != 1
            or attempt.operation_key != operation.operation_key
            or attempt.session_id != operation.session_id
            or attempt.agent_key is not operation.agent_key
            for attempt in operation.build_attempts
        ):
            raise ArtifactRepositoryError("Build attempt does not match its operation")
