"""Composition for the standalone v2 CLI entry point."""

import os
from pathlib import Path
import sys
import logging

from dotenv import load_dotenv

from src.get_me_in.application.settings import Settings, SettingsValidationError
from src.get_me_in.bootstrap import build_application
from src.get_me_in.cli.app import CliApp
from src.get_me_in.cli.commands import build_command_registry
from src.get_me_in.cli.input import InputController
from src.get_me_in.cli.renderer import Renderer
from src.get_me_in.cli.worker import WorkerRunner
from src.get_me_in.logging_setup import configure_logging


logger = logging.getLogger(__name__)
_FILE_ONLY_LOG = {"_get_me_in_file_only": True}


def main() -> int:
    """Build, run, and close the v2 CLI for the production entry point."""
    _ensure_utf8()
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env")
    renderer = Renderer()
    try:
        settings = Settings.from_env(os.environ, project_root=project_root)
    except SettingsValidationError as error:
        renderer.render_error(str(error))
        return 2

    application = None
    worker = None
    exit_code = 1
    logging_ready = False
    try:
        renderer = Renderer(show_thinking=settings.show_thinking)
        log_path = configure_logging(settings.log_dir, settings.log_level)
        logging_ready = True
        logger.info("v2 CLI starting; log=%s level=%s", log_path, settings.log_level)
        application = build_application(settings)
        input_controller = InputController()
        commands = build_command_registry(application, input_controller, renderer)
        input_controller.set_completions(commands.completions)
        worker = WorkerRunner(application, renderer)
        app = CliApp(application, commands, input_controller, renderer, worker)
        exit_code = app.run()
    except Exception:
        if logging_ready:
            logger.critical(
                "v2 CLI startup or execution failed",
                exc_info=True,
                extra=_FILE_ONLY_LOG,
            )
        renderer.render_error("启动失败；请检查配置或日志后重试。")
        exit_code = 1
    finally:
        try:
            if worker is not None:
                try:
                    worker.close()
                except Exception:
                    logger.critical(
                        "v2 CLI worker close failed",
                        exc_info=True,
                        extra=_FILE_ONLY_LOG,
                    )
                    renderer.render_error("CLI Worker 关闭失败；请检查日志。")
                    exit_code = 1
        finally:
            if application is not None:
                try:
                    close_report = application.close()
                except Exception:
                    logger.critical(
                        "v2 CLI application close failed",
                        exc_info=True,
                        extra=_FILE_ONLY_LOG,
                    )
                    renderer.render_error("应用资源关闭失败；请检查日志。")
                    exit_code = 1
                else:
                    for issue in close_report.issues:
                        logger.critical(
                            "v2 CLI resource close issue: resource=%s timed_out=%s message=%s",
                            issue.resource_name,
                            issue.timed_out,
                            issue.message,
                            extra=_FILE_ONLY_LOG,
                        )
                        label = "资源关闭超时" if issue.timed_out else "资源关闭失败"
                        renderer.render_error(
                            f"{label}（{issue.resource_name}）：{issue.message}"
                        )
                        exit_code = 1
            logger.info("v2 CLI stopped")
    return exit_code


def _ensure_utf8() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
