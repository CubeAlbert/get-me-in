"""提示词加载器 — 模板拼接与占位符替换。"""

import re
from pathlib import Path

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


class PromptLoader:
    """加载提示词模板并替换占位符。

    get()      — Agent 用：拼接 general_agent/ 下所有 .md 文件
    get_raw()  — 非 Agent 用：加载指定文件，跳过公共前缀
    """

    def __init__(self, prompts_dir: str | Path = "data/prompts"):
        self._prompts_dir = Path(prompts_dir)
        self._general_agent_dir = self._prompts_dir / "general_agent"

    # ---- public API -------------------------------------------------------

    def get(self, **variables: str) -> str:
        """拼接 general_agent/ 下所有 .md 文件并替换占位符。

        Raises:
            FileNotFoundError: general_agent/ 目录为空或不存在。
            KeyError: 模板中的占位符在 variables 中没有提供对应的值。
        """
        md_files = sorted(self._general_agent_dir.glob("*.md"))
        if not md_files:
            raise FileNotFoundError(
                f"No .md files found in {self._general_agent_dir}"
            )

        parts: list[str] = []
        for f in md_files:
            parts.append(f.read_text(encoding="utf-8"))

        template = "\n".join(parts)
        return self._substitute(template, variables)

    def get_raw(self, name: str, **variables: str) -> str:
        """加载 data/prompts/<name>.md 并替换变量，不拼接公共前缀。

        Raises:
            FileNotFoundError: 指定文件不存在。
            KeyError: 模板中的占位符在 variables 中没有提供对应的值。
        """
        file_path = self._prompts_dir / f"{name}.md"
        if not file_path.is_file():
            raise FileNotFoundError(f"Template not found: {file_path}")

        template = file_path.read_text(encoding="utf-8")
        return self._substitute(template, variables)

    def list(self) -> list[str]:
        """列出 general_agent/ 下所有 .md 文件（按文件名排序）。"""
        if not self._general_agent_dir.is_dir():
            return []
        return sorted(
            f.name for f in self._general_agent_dir.glob("*.md")
        )

    # ---- internals --------------------------------------------------------

    @staticmethod
    def _substitute(template: str, variables: dict[str, str]) -> str:
        """替换模板中的 {{PLACEHOLDER}} 占位符。

        Args:
            template: 包含 {{NAME}} 占位符的模板字符串。
            variables: 占位符名 → 值的映射。

        Returns:
            替换后的字符串。

        Raises:
            KeyError: 模板中的某个占位符在 variables 中没有提供对应的值。
        """
        required = set(_PLACEHOLDER_RE.findall(template))
        missing = required - set(variables)
        if missing:
            raise KeyError(
                f"Missing placeholder values: {', '.join(sorted(missing))}"
            )

        def _replace(m: re.Match) -> str:
            return variables[m.group(1)]

        return _PLACEHOLDER_RE.sub(_replace, template)
