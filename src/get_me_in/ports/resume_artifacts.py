"""简历模板与 PDF 产物的临时端口，R7 将由 ArtifactService 取代。"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.get_me_in.ports.llm import CancellationSignal
from src.get_me_in.ports.process import ProcessResult
from src.get_me_in.ports.workspace import WorkspacePort
from src.get_me_in.domain.agents import AgentKey


@dataclass(frozen=True)
class TemplateCopyResult:
    files: tuple[Path, ...]
    target_dir: Path


class ResumeArtifactPort(Protocol):
    def copy_template(
        self, template: str, prefix: str, target_dir: Path, *, workspace: WorkspacePort, session_id: str, agent_key: AgentKey
    ) -> TemplateCopyResult: ...

    def build_pdf(
        self, path: Path, *, workspace: WorkspacePort, cancellation: CancellationSignal, session_id: str, agent_key: AgentKey
    ) -> ProcessResult: ...


class ResumeArtifactBackend(Protocol):
    def copy_template(self, template: str, prefix: str, target_dir: Path, *, workspace: WorkspacePort) -> TemplateCopyResult: ...
    def build_pdf(self, path: Path, *, workspace: WorkspacePort, cancellation: CancellationSignal) -> ProcessResult: ...
