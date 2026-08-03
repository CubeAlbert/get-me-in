"""Versioned, immutable Resume artifact persistence contracts."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json

from src.get_me_in.domain.agents import AgentKey


class ArtifactKind(StrEnum):
    LATEX = "latex"
    PDF = "pdf"
    README = "readme"


class ArtifactOperationKind(StrEnum):
    COPY_TEMPLATE = "copy_template"
    BUILD_PDF = "build_pdf"
    MERGE_PDFS = "merge_pdfs"


class ArtifactOperationStatus(StrEnum):
    PENDING = "pending"
    COMMITTED = "committed"


@dataclass(frozen=True)
class Artifact:
    schema_version: int
    artifact_id: str
    session_id: str
    agent_key: AgentKey
    kind: ArtifactKind
    path: str
    version: int
    content_hash: str
    created_at: datetime
    template_name: str | None = None
    page_count: int | None = None


@dataclass(frozen=True)
class ArtifactBuildAttempt:
    schema_version: int
    attempt_id: str
    operation_key: str
    session_id: str
    agent_key: AgentKey
    source_path: str
    exit_code: int | None
    stdout: str
    stderr: str
    stdout_original_bytes: int
    stderr_original_bytes: int
    stdout_truncated: bool
    stderr_truncated: bool
    timed_out: bool
    cancelled: bool
    created_at: datetime


@dataclass(frozen=True)
class ArtifactOperation:
    schema_version: int
    operation_key: str
    session_id: str
    agent_key: AgentKey
    kind: ArtifactOperationKind
    path: str
    input_hash: str
    status: ArtifactOperationStatus
    created_at: datetime
    artifacts: tuple[Artifact, ...] = ()
    build_attempts: tuple[ArtifactBuildAttempt, ...] = ()

    @staticmethod
    def key_for(*, session_id: str, agent_key: AgentKey, kind: ArtifactOperationKind, path: str, input_hash: str) -> str:
        payload = {"agent_key": agent_key.value, "input_hash": input_hash, "kind": kind.value, "path": path, "schema_version": 1, "session_id": session_id}
        return sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
