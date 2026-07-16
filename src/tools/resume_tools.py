"""简历专属工具 — ResumeAgent 使用。"""

import shutil
from pathlib import Path

from src.agents.registry import RESUME_AGENT_KEY
from src.config import config
from src.tools.registry import ConfirmMode, tool
from src.tools.exceptions import ToolCallException
from src.tools.workspace_tools import _validate_path

_TEMPLATE_DIR = Path("data/resume/template")
_README_FILE = "README.md"

_TEX_TEMPLATES = {
    "chn": "CHN_Template.tex",
    "en": "EN_Template.tex",
}


def _copy_file(src: Path, dst: Path, *, overridable: bool = False) -> str:
    """复制单个文件。non-overridable 文件已存在时抛 ToolCallException。"""
    if dst.exists() and not overridable:
        raise ToolCallException(
            f"目标已存在: {dst.name}",
            suggestion=(
                "用 workspace_read 读取该文件内容展示给用户确认，"
                "用户确认后可 workspace_delete 删除，然后重新 copy_template"
            ),
        )
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return str(dst)


@tool(
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
    input_schema={
        "template": {
            "description": "模板语言: 'chn'（中文）、'en'（英文）、'all'（中英文都复制）",
        },
        "prefix": {
            "description": (
                "文件名前缀。chn → {prefix}_CHN.tex，en → {prefix}_EN.tex，"
                "all → {prefix}_CHN.tex + {prefix}_EN.tex"
            ),
        },
        "target_dir": {
            "description": "工作区目标子目录，默认 '.' 即根目录",
            "default": ".",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def copy_template(template: str, prefix: str, target_dir: str = ".") -> dict:
    valid = {"chn", "en", "all"}
    if template not in valid:
        raise ToolCallException(
            f"无效的 template: {template!r}",
            suggestion=f"可选: {', '.join(sorted(valid))}",
        )

    working_dir = Path(config.WORKING_DIR).resolve()
    dest_dir = working_dir / target_dir
    src_dir = Path.cwd() / _TEMPLATE_DIR

    files = []

    # 确定要复制的 .tex 模板
    targets: list[tuple[str, str]] = []  # [(源文件名, 目标文件名)]
    if template in ("chn", "all"):
        targets.append((_TEX_TEMPLATES["chn"], f"{prefix}_CHN.tex"))
    if template in ("en", "all"):
        targets.append((_TEX_TEMPLATES["en"], f"{prefix}_EN.tex"))

    # 复制 .tex 模板（不可覆盖）
    for src_name, dst_name in targets:
        src = src_dir / src_name
        if not src.exists():
            raise ToolCallException(
                f"模板文件不存在: {src_name}",
                suggestion="请检查 data/resume/template/ 目录",
            )
        dst = dest_dir / dst_name
        rel = _copy_file(src, dst, overridable=False)
        files.append(str(Path(rel).relative_to(working_dir)))

    # 复制模板操作手册（可覆盖）
    src = src_dir / _README_FILE
    if not src.exists():
        raise ToolCallException(
            f"操作手册不存在: {_README_FILE}",
            suggestion="请检查 data/resume/template/ 目录",
        )
    dst = dest_dir / _README_FILE
    rel = _copy_file(src, dst, overridable=True)
    files.append(str(Path(rel).relative_to(working_dir)))

    return {"files": files, "target_dir": target_dir}


@tool(
    purpose="编译工作区中的 .tex 文件为 PDF。",
    use_when="简历 LaTeX 文件填充完成后，需要生成 PDF 时",
    do_not_use_when=".tex 文件不存在 或 pdflatex 环境未安装时",
    expected_output='{"stdout": "...", "stderr": "...", "exit_code": 0}',
    input_schema={
        "path": {
            "description": "要编译的 .tex 文件相对路径，基于工作区根目录",
        },
    },
    agent=[RESUME_AGENT_KEY],
    confirm_mode=ConfirmMode.CONFIG,
)
def build_pdf(path: str) -> dict:
    full = _validate_path(path)
    if not full.is_file():
        raise ToolCallException(
            f"file not found: {path}",
            suggestion="用 workspace_list 确认目标路径",
        )
    if full.suffix.lower() != ".tex":
        raise ToolCallException(
            f"not a .tex file: {path}",
            suggestion="build_pdf 仅支持 .tex 文件编译",
        )

    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        raise ToolCallException(
            "系统中未找到 pdflatex，无法编译 PDF",
            suggestion="请安装 TeX Live 或 MiKTeX，确保 pdflatex 在 PATH 中。安装后重新调用 build_pdf",
        )

    import subprocess

    try:
        result = subprocess.run(
            [pdflatex, "-synctex=1", "-interaction=nonstopmode", full.name],
            capture_output=True,
            text=True,
            cwd=str(full.parent),
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise ToolCallException(
            "pdflatex 编译超时（60s），可能模板过大或 pdflatex 卡住",
            suggestion="请检查 .tex 文件是否有死循环或异常大的内容，或手动编译排查问题",
        ) from None

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    }
