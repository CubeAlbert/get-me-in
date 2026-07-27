"""简历模板复制与 PDF 编译工具的 v2 定义。"""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.resume_artifacts import ResumeArtifactPort
from src.get_me_in.application.artifact_service import ArtifactPartialFailure
from src.get_me_in.ports.workspace import WorkspacePort


class ResumeToolContext(ToolHandlerContext, Protocol):
    resume_artifacts: ResumeArtifactPort | None
    workspace: WorkspacePort | None
    cancellation: object


def build_resume_tools() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition(
            "copy_template", "复制中文、英文或双语 LaTeX 简历模板及说明文件。",
            ToolSchema({"template": str, "prefix": str, "target_dir": str}, frozenset({"template", "prefix"})),
            ToolPolicy(frozenset({Capability.RESUME_ARTIFACT, Capability.WORKSPACE_WRITE}), ConfirmationMode.ALWAYS), _copy_template,
        ),
        ToolDefinition(
            "build_pdf", "使用 pdflatex 编译工作区内的 LaTeX 简历。",
            ToolSchema({"path": str}, frozenset({"path"})),
            ToolPolicy(frozenset({Capability.RESUME_ARTIFACT, Capability.WORKSPACE_READ}), ConfirmationMode.ALWAYS), _build_pdf,
        ),
    )


def _copy_template(arguments: Mapping[str, object], context: ResumeToolContext) -> ToolSuccess | ToolFailure:
    artifacts = _artifacts(context)
    if isinstance(artifacts, ToolFailure):
        return artifacts
    if context.workspace is None:
        return ToolFailure("workspace_unavailable", "This tool requires a configured workspace")
    try:
        result = artifacts.copy_template(
            arguments["template"], arguments["prefix"], Path(arguments.get("target_dir", ".")), workspace=context.workspace, session_id=context.session_id, agent_key=context.agent_key,
        )
    except ArtifactPartialFailure as error:
        return _partial_failure(error)
    except Exception as error:
        return ToolFailure("copy_template_failed", str(error))
    return ToolSuccess({"files": tuple(str(path) for path in result.files), "target_dir": str(result.target_dir)})


def _build_pdf(arguments: Mapping[str, object], context: ResumeToolContext) -> ToolSuccess | ToolFailure:
    artifacts = _artifacts(context)
    if isinstance(artifacts, ToolFailure):
        return artifacts
    if context.workspace is None:
        return ToolFailure("workspace_unavailable", "This tool requires a configured workspace")
    try:
        result = artifacts.build_pdf(Path(arguments["path"]), workspace=context.workspace, cancellation=context.cancellation, session_id=context.session_id, agent_key=context.agent_key)
    except ArtifactPartialFailure as error:
        return _partial_failure(error)
    except Exception as error:
        return ToolFailure("build_pdf_failed", str(error))
    if result.cancelled:
        return ToolFailure("build_pdf_cancelled", "PDF build was cancelled")
    if result.timed_out:
        return ToolFailure("build_pdf_timed_out", "PDF build timed out")
    if result.exit_code is None:
        message = result.stderr or result.stdout or "PDF build failed before producing an exit code"
        return ToolFailure("build_pdf_failed", message)
    return ToolSuccess({"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code})


def _partial_failure(error: ArtifactPartialFailure) -> ToolFailure:
    changed = ", ".join(path.as_posix() for path in error.changed_paths)
    suggestion = f"Files may have changed: {changed}" if changed else None
    return ToolFailure("artifact_partial_failure", f"{error.code}: {error}", suggestion)


def _artifacts(context: ResumeToolContext) -> ResumeArtifactPort | ToolFailure:
    if context.resume_artifacts is None:
        return ToolFailure("resume_artifacts_unavailable", "This application has no resume artifact adapter")
    return context.resume_artifacts
