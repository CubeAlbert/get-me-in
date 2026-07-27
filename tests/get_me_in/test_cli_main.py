"""Root-entry and v2 CLI exit-code contracts for R8-E."""

import ast
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from src.get_me_in.application.settings import Settings, SettingsValidationError
from src.get_me_in.cli import main as cli_main


def _settings() -> Settings:
    return Settings(
        openai_api_key="key",
        openai_base_url="https://example.test",
        llm_pro_model="pro",
        llm_flash_model="flash",
        llm_timeout_seconds=60,
        llm_thinking_enabled=True,
        hf_endpoint=None,
        reference_dir=Path("data/reference"),
        prompts_dir=Path("data/prompts"),
        resume_template_dir=Path("data/resume/template"),
        workspace_dir=Path("data/workspace"),
        sessions_dir=Path("data/v2/sessions"),
    )


class RootEntryTests(unittest.TestCase):
    def test_root_entry_only_delegates_to_v2_main(self) -> None:
        root = Path(__file__).resolve().parents[2] / "main.py"
        tree = ast.parse(root.read_text(encoding="utf-8"), filename=str(root))
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertEqual(1, len(imports))
        self.assertEqual("src.get_me_in.cli.main", imports[0].module)
        self.assertEqual(["main"], [alias.name for alias in imports[0].names])


class CliMainTests(unittest.TestCase):
    def test_settings_error_returns_two(self) -> None:
        renderer = Mock()
        with (
            patch.object(cli_main, "_ensure_utf8"),
            patch.object(cli_main, "Renderer", return_value=renderer),
            patch.object(cli_main, "Settings") as settings_type,
        ):
            settings_type.from_env.side_effect = SettingsValidationError("missing key")
            self.assertEqual(2, cli_main.main())

        renderer.render_error.assert_called_once_with("missing key")

    def test_startup_error_returns_one_without_traceback(self) -> None:
        renderer = Mock()
        stderr = StringIO()
        with redirect_stderr(stderr):
            with (
                patch.object(cli_main, "_ensure_utf8"),
                patch.object(cli_main, "Renderer", return_value=renderer),
                patch.object(cli_main, "Settings") as settings_type,
                patch.object(cli_main, "build_application", side_effect=RuntimeError("broken startup")),
            ):
                settings_type.from_env.return_value = _settings()
                self.assertEqual(1, cli_main.main())

        renderer.render_error.assert_called_once_with("启动失败；请检查配置或日志后重试。")
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_normal_exit_returns_zero_and_closes_resources(self) -> None:
        initial_renderer = Mock()
        configured_renderer = Mock()
        application = Mock()
        worker = Mock()
        app = Mock()
        app.run.return_value = 0
        with (
            patch.object(cli_main, "_ensure_utf8"),
            patch.object(cli_main, "Renderer", side_effect=(initial_renderer, configured_renderer)),
            patch.object(cli_main, "Settings") as settings_type,
            patch.object(cli_main, "configure_logging"),
            patch.object(cli_main, "build_application", return_value=application),
            patch.object(cli_main, "InputController") as input_type,
            patch.object(cli_main, "build_command_registry") as commands_builder,
            patch.object(cli_main, "WorkerRunner", return_value=worker),
            patch.object(cli_main, "CliApp", return_value=app),
        ):
            settings_type.from_env.return_value = _settings()
            commands_builder.return_value.completions = Mock()
            self.assertEqual(0, cli_main.main())

        input_type.return_value.set_completions.assert_called_once_with(
            commands_builder.return_value.completions
        )
        worker.close.assert_called_once_with()
        application.close.assert_called_once_with()
