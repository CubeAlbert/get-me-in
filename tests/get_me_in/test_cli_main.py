"""Root-entry and CLI exit-code contracts for R8-E."""

import ast
from contextlib import redirect_stderr
from io import StringIO
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from src.get_me_in.application.app_results import CloseIssue, CloseReport
from src.get_me_in.application.localization import Locale
from src.get_me_in.application.settings import (
    KnowledgeIndexMode,
    Settings,
    SettingsValidationError,
)
from src.get_me_in.ports.llm import ModelProfile
from src.get_me_in.cli import main as cli_main


def _settings(
    *,
    log_dir: Path = Path("data/logs"),
    log_level: str = "INFO",
) -> Settings:
    return Settings(
        openai_api_key="key",
        openai_base_url="https://example.test",
        llm_pro_model="pro",
        llm_flash_model="flash",
        main_model_profile=ModelProfile.PRO,
        resume_model_profile=ModelProfile.PRO,
        memory_model_profile=ModelProfile.FLASH,
        web_search_model_profile=ModelProfile.PRO,
        main_temperature=0.1,
        resume_temperature=0.2,
        memory_temperature=0.0,
        llm_timeout_seconds=60,
        llm_thinking_enabled=True,
        hf_endpoint=None,
        reference_dir=Path("data/reference"),
        prompts_dir=Path("data/prompts"),
        resume_template_dir=Path("data/resume/template"),
        workspace_dir=Path("data/workspace"),
        sessions_dir=Path("data/runtime/sessions"),
        log_dir=log_dir,
        log_level=log_level,
        max_model_calls_per_run=100,
        cancel_grace_seconds=2.0,
        show_thinking=False,
        ui_locale=Locale.ZH_CN,
        response_locale=Locale.ZH_CN,
        locales_dir=Path("data/locales"),
        knowledge_index_mode=KnowledgeIndexMode.PERSISTENT,
        knowledge_manifest_path=Path("data/runtime/knowledge/manifest.json"),
        knowledge_chroma_dir=Path("data/runtime/knowledge/chroma"),
        memories_dir=Path("data/runtime/memories"),
        embedding_model="BAAI/bge-base-zh-v1.5",
        reranker_model="BAAI/bge-reranker-v2-m3",
        embedding_batch_size=32,
        rerank_batch_size=32,
        retrieval_top_k=8,
        shutdown_timeout_seconds=60.0,
        auto_memory_on_exit=False,
        artifacts_dir=Path("data/runtime/artifacts"),
        pdf_build_timeout_seconds=60.0,
        artifact_log_max_bytes=65536,
        model_format_repair_limit=3,
        web_search_max_tokens=4096,
        log_file_name="app.log",
        log_max_bytes=10485760,
        log_backup_count=5,
        cli_worker_poll_interval_seconds=0.1,
        subprocess_poll_interval_seconds=0.05,
        cli_result_preview_chars=500,
        cli_argument_preview_chars=160,
        session_preview_chars=80,
        workspace_read_default_limit=100,
        workspace_search_max_matches=50,
        workspace_file_search_max_results=50,
        customer_file_read_default_limit=100,
        retrieval_default_top_k=5,
        hf_hub_disable_progress_bars=True,
        tqdm_disable=True,
        transformers_verbosity="error",
        model_library_log_level="ERROR",
    )


class RootEntryTests(unittest.TestCase):
    def test_root_entry_only_delegates_to_package_main(self) -> None:
        root = Path(__file__).resolve().parents[2] / "main.py"
        tree = ast.parse(root.read_text(encoding="utf-8"), filename=str(root))
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        self.assertEqual(1, len(imports))
        self.assertEqual("src.get_me_in.cli.main", imports[0].module)
        self.assertEqual(["main"], [alias.name for alias in imports[0].names])


class CliMainTests(unittest.TestCase):
    def setUp(self) -> None:
        self._environment_patch = patch.dict(os.environ, {}, clear=True)
        self._environment_patch.start()
        self.addCleanup(self._environment_patch.stop)
        self._load_dotenv_patch = patch.object(cli_main, "load_dotenv")
        self._load_dotenv_patch.start()
        self.addCleanup(self._load_dotenv_patch.stop)

    def test_model_loading_progress_is_disabled_for_the_cli_process(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cli_main._configure_model_loading(_settings())

            observed = {
                name: os.environ.get(name)
                for name in (
                    "HF_HUB_DISABLE_PROGRESS_BARS",
                    "TQDM_DISABLE",
                    "TRANSFORMERS_VERBOSITY",
                )
            }

        self.assertEqual(
            {
                "HF_HUB_DISABLE_PROGRESS_BARS": "1",
                "TQDM_DISABLE": "1",
                "TRANSFORMERS_VERBOSITY": "error",
            },
            observed,
        )

    def test_settings_error_returns_two(self) -> None:
        renderer = Mock()
        with (
            patch.object(cli_main, "_ensure_utf8"),
            patch.object(cli_main, "Renderer", return_value=renderer),
            patch.object(cli_main, "Settings") as settings_type,
        ):
            settings_type.from_env.side_effect = SettingsValidationError("missing key")
            self.assertEqual(2, cli_main.main())

        renderer.render_error.assert_called_once_with("配置错误：missing key")

    def test_startup_error_returns_one_without_traceback(self) -> None:
        renderer = Mock()
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            try:
                with redirect_stderr(stderr):
                    with (
                        patch.object(cli_main, "_ensure_utf8"),
                        patch.object(cli_main, "Renderer", return_value=renderer),
                        patch.object(cli_main, "Settings") as settings_type,
                        patch.object(
                            cli_main,
                            "build_application",
                            side_effect=RuntimeError("broken startup"),
                        ),
                    ):
                        settings_type.from_env.return_value = _settings(
                            log_dir=Path(temporary),
                            log_level="ERROR",
                        )
                        self.assertEqual(1, cli_main.main())
                log = (Path(temporary) / "app.log").read_text(encoding="utf-8")
            finally:
                _close_get_me_in_handlers()

        renderer.render_error.assert_called_once_with("启动失败；请检查配置或日志后重试。")
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertIn("Traceback", log)
        self.assertIn("broken startup", log)

    def test_logging_setup_error_returns_one_without_traceback(self) -> None:
        initial_renderer = Mock()
        configured_renderer = Mock()
        stderr = StringIO()
        with redirect_stderr(stderr):
            with (
                patch.object(cli_main, "_ensure_utf8"),
                patch.object(
                    cli_main,
                    "Renderer",
                    side_effect=(initial_renderer, configured_renderer),
                ),
                patch.object(cli_main, "Settings") as settings_type,
                patch.object(
                    cli_main,
                    "configure_logging",
                    side_effect=OSError("log directory unavailable"),
                ),
            ):
                settings_type.from_env.return_value = _settings()
                self.assertEqual(1, cli_main.main())

        configured_renderer.render_error.assert_called_once_with(
            "启动失败；请检查配置或日志后重试。"
        )
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_normal_exit_returns_zero_and_closes_resources(self) -> None:
        initial_renderer = Mock()
        configured_renderer = Mock()
        application = Mock()
        worker = Mock()
        app = Mock()
        app.run.return_value = 0
        application.close.return_value = CloseReport(closed=("application",))
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

    def test_close_issue_returns_one_and_is_visible(self) -> None:
        initial_renderer = Mock()
        configured_renderer = Mock()
        application = Mock()
        worker = Mock()
        app = Mock()
        app.run.return_value = 0
        application.close.return_value = CloseReport(
            issues=(CloseIssue("background_worker", "still running", timed_out=True),)
        )
        with (
            patch.object(cli_main, "_ensure_utf8"),
            patch.object(
                cli_main,
                "Renderer",
                side_effect=(initial_renderer, configured_renderer),
            ),
            patch.object(cli_main, "Settings") as settings_type,
            patch.object(cli_main, "configure_logging"),
            patch.object(cli_main, "build_application", return_value=application),
            patch.object(cli_main, "InputController"),
            patch.object(cli_main, "build_command_registry") as commands_builder,
            patch.object(cli_main, "WorkerRunner", return_value=worker),
            patch.object(cli_main, "CliApp", return_value=app),
            patch.object(cli_main.logger, "critical"),
        ):
            settings_type.from_env.return_value = _settings()
            commands_builder.return_value.completions = Mock()
            self.assertEqual(1, cli_main.main())

        configured_renderer.render_error.assert_called_once_with(
            "资源关闭超时（background_worker）：still running"
        )
        worker.close.assert_called_once_with()
        application.close.assert_called_once_with()

    def test_close_exceptions_return_one_and_both_owners_are_attempted(self) -> None:
        initial_renderer = Mock()
        configured_renderer = Mock()
        application = Mock()
        application.close.side_effect = RuntimeError("application close failed")
        worker = Mock()
        worker.close.side_effect = RuntimeError("worker close failed")
        app = Mock()
        app.run.return_value = 0
        with (
            patch.object(cli_main, "_ensure_utf8"),
            patch.object(
                cli_main,
                "Renderer",
                side_effect=(initial_renderer, configured_renderer),
            ),
            patch.object(cli_main, "Settings") as settings_type,
            patch.object(cli_main, "configure_logging"),
            patch.object(cli_main, "build_application", return_value=application),
            patch.object(cli_main, "InputController"),
            patch.object(cli_main, "build_command_registry") as commands_builder,
            patch.object(cli_main, "WorkerRunner", return_value=worker),
            patch.object(cli_main, "CliApp", return_value=app),
            patch.object(cli_main.logger, "critical"),
        ):
            settings_type.from_env.return_value = _settings()
            commands_builder.return_value.completions = Mock()
            self.assertEqual(1, cli_main.main())

        configured_renderer.render_error.assert_has_calls(
            (
                call("CLI Worker 关闭失败；请检查日志。"),
                call("应用资源关闭失败；请检查日志。"),
            )
        )
        worker.close.assert_called_once_with()
        application.close.assert_called_once_with()


def _close_get_me_in_handlers() -> None:
    package_logger = logging.getLogger("src.get_me_in")
    for handler in tuple(package_logger.handlers):
        package_logger.removeHandler(handler)
        handler.close()
