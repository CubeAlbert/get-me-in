"""简历模板复制与 PDF 编译工具的 v2 定义。"""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolParameter, ToolPolicy, ToolSchema, ToolSuccess
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
            name="copy_template",
            purpose=(
                "复制 LaTeX 简历模板到工作区，README.md（模板操作手册）始终跟随复制。\n\n"
                "调用前应与用户确认：\n"
                "1. 语言选择：中文 / 英文 / 两者都要\n"
                "2. 文件名前缀（复制后文件名为 {prefix}_CHN.tex / {prefix}_EN.tex）\n"
                "3. 用 workspace_list 检查目标目录，若已有同名文件，"
                "用 workspace_read 展示给用户确认后 workspace_delete 删除\n\n"
                "复制完成后应 workspace_read(README.md) 阅读操作手册，了解模板结构和填充约束。"
            ),
            use_when="用户要求开始构建或修改简历时",
            do_not_use_when="目标目录已有同名 .tex 文件且未被用户确认删除时",
            expected_output='{"files": ["resume_CHN.tex", "README.md"], "target_dir": "."}',
            schema=ToolSchema(
                {
                    "template": ToolParameter(
                        str,
                        "模板语言: 'chn'（中文）、'en'（英文）、'all'（中英文都复制）",
                        allowed_values=("chn", "en", "all"),
                    ),
                    "prefix": ToolParameter(
                        str,
                        "文件名前缀。工具会自动拼接：chn → {prefix}_CHN.tex，en → {prefix}_EN.tex，all → {prefix}_CHN.tex + {prefix}_EN.tex。若用户已提供含 _CHN 或 _EN 的完整文件名，去掉后缀部分作为 prefix，避免出现 XXX_CHN_CHN.tex 双重后缀",
                    ),
                    "target_dir": ToolParameter(
                        str,
                        "工作区目标子目录，默认 '.' 即根目录",
                        default=".",
                    ),
                },
                frozenset({"template", "prefix"}),
            ),
            policy=ToolPolicy(
                frozenset(
                    {
                        Capability.RESUME_ARTIFACT,
                        Capability.WORKSPACE_WRITE,
                    }
                ),
                ConfirmationMode.ALWAYS,
            ),
            handler=_copy_template,
        ),
        ToolDefinition(
            name="build_pdf",
            purpose="编译工作区中的 .tex 文件为 PDF。",
            use_when="简历 LaTeX 文件填充完成后，需要生成 PDF 时",
            do_not_use_when=".tex 文件不存在或 pdflatex 环境未安装时",
            expected_output='{"stdout": "...", "stderr": "...", "exit_code": 0}',
            schema=ToolSchema(
                {
                    "path": ToolParameter(
                        str,
                        "要编译的 .tex 文件相对路径，基于工作区根目录",
                    )
                },
                frozenset({"path"}),
            ),
            policy=ToolPolicy(
                frozenset(
                    {
                        Capability.RESUME_ARTIFACT,
                        Capability.WORKSPACE_READ,
                    }
                ),
                ConfirmationMode.ALWAYS,
            ),
            handler=_build_pdf,
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
