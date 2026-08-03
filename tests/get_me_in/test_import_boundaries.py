"""Development-time checks for one-way import rules."""

import ast
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "get_me_in"
FORBIDDEN_PREFIXES = (
    "src.agents",
    "src.cli",
    "src.config",
    "src.lifecycle",
    "src.llm",
    "src.logger",
    "src.message",
    "src.memory",
    "src.prompts",
    "src.tools",
    "src.rag",
    "src.request",
    "src.response",
    "src.utils",
)
LAYER_PREFIXES = {
    "domain": ("src.get_me_in.domain",),
    "ports": ("src.get_me_in.domain", "src.get_me_in.ports"),
    "application": (
        "src.get_me_in.domain",
        "src.get_me_in.ports",
        "src.get_me_in.application",
    ),
    "adapters": (
        "src.get_me_in.domain",
        "src.get_me_in.ports",
        "src.get_me_in.adapters",
    ),
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


class ImportBoundaryTests(unittest.TestCase):
    def test_package_never_imports_legacy_runtime_modules(self) -> None:
        violations: list[str] = []
        for path in PACKAGE_ROOT.rglob("*.py"):
            for imported in _imports(path):
                if imported.startswith(FORBIDDEN_PREFIXES):
                    violations.append(f"{path.relative_to(PACKAGE_ROOT)} -> {imported}")

        self.assertEqual([], violations)

    def test_layers_only_import_permitted_package_layers(self) -> None:
        violations: list[str] = []
        for layer, allowed_prefixes in LAYER_PREFIXES.items():
            for path in (PACKAGE_ROOT / layer).rglob("*.py"):
                for imported in _imports(path):
                    if not imported.startswith("src.get_me_in"):
                        continue
                    if not imported.startswith(allowed_prefixes):
                        violations.append(
                            f"{path.relative_to(PACKAGE_ROOT)} -> {imported}"
                        )

        self.assertEqual([], violations)
