"""Composition for the standalone CLI entry point."""

import os
from pathlib import Path
import sys
import logging

from dotenv import load_dotenv

from src.get_me_in.application.localization import Locale, parse_locale
from src.get_me_in.application.settings import (
    DEFAULT_LOCALES_DIR,
    Settings,
    SettingsValidationError,
    resolve_config_path,
)
from src.get_me_in.bootstrap import build_application
from src.get_me_in.cli.app import CliApp
from src.get_me_in.cli.commands import build_command_registry
from src.get_me_in.cli.input import InputController
from src.get_me_in.cli.localization import LocaleCatalogError, Translator, load_translator
from src.get_me_in.cli.renderer import Renderer
from src.get_me_in.cli.worker import WorkerRunner
from src.get_me_in.logging_setup import configure_logging


logger = logging.getLogger(__name__)
_FILE_ONLY_LOG = {"_get_me_in_file_only": True}


def main() -> int:
    """Build, run, and close the CLI for the production entry point."""
    _ensure_utf8()
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env")
    bootstrap_translator = _load_bootstrap_translator(project_root)
    translator = bootstrap_translator or _diagnostic_translator()
    renderer = Renderer(translator=translator)
    try:
        settings = Settings.from_env(os.environ, project_root=project_root)
    except SettingsValidationError as error:
        renderer.render_error(translator.text("startup.settings_error", detail=str(error)))
        return 1 if bootstrap_translator is None else 2
    _configure_model_loading(settings)

    application = None
    worker = None
    exit_code = 1
    logging_ready = False
    try:
        translator = load_translator(settings.locales_dir, settings.ui_locale)
        renderer = Renderer(
            translator=translator,
            show_thinking=settings.show_thinking,
            result_preview_chars=settings.cli_result_preview_chars,
            argument_preview_chars=settings.cli_argument_preview_chars,
        )
        log_path = configure_logging(
            settings.log_dir,
            settings.log_level,
            settings.log_file_name,
            settings.log_max_bytes,
            settings.log_backup_count,
        )
        logging_ready = True
        logger.info("CLI starting; log=%s level=%s", log_path, settings.log_level)
        application = build_application(settings)
        input_controller = InputController(translator=translator)
        commands = build_command_registry(
            application,
            input_controller,
            renderer,
            translator=translator,
            session_preview_chars=settings.session_preview_chars,
        )
        input_controller.set_completions(commands.completions)
        worker = WorkerRunner(
            application,
            renderer,
            translator=translator,
            poll_interval_seconds=settings.cli_worker_poll_interval_seconds,
        )
        app = CliApp(
            application,
            commands,
            input_controller,
            renderer,
            worker,
            translator=translator,
        )
        exit_code = app.run()
    except Exception:
        if logging_ready:
            logger.critical(
                "CLI startup or execution failed",
                exc_info=True,
                extra=_FILE_ONLY_LOG,
            )
        renderer.render_error(translator.text("startup.failed"))
        exit_code = 1
    finally:
        try:
            if worker is not None:
                try:
                    worker.close()
                except Exception:
                    logger.critical(
                        "CLI worker close failed",
                        exc_info=True,
                        extra=_FILE_ONLY_LOG,
                    )
                    renderer.render_error(translator.text("close.worker_failed"))
                    exit_code = 1
        finally:
            if application is not None:
                try:
                    close_report = application.close()
                except Exception:
                    logger.critical(
                        "CLI application close failed",
                        exc_info=True,
                        extra=_FILE_ONLY_LOG,
                    )
                    renderer.render_error(translator.text("close.application_failed"))
                    exit_code = 1
                else:
                    for issue in close_report.issues:
                        logger.critical(
                            "CLI resource close issue: resource=%s timed_out=%s message=%s",
                            issue.resource_name,
                            issue.timed_out,
                            issue.message,
                            extra=_FILE_ONLY_LOG,
                        )
                        key = "close.worker_timeout" if issue.timed_out else "close.resource_failed"
                        renderer.render_error(
                            translator.text(
                                key,
                                resource=issue.resource_name,
                                detail=issue.message,
                            )
                        )
                        exit_code = 1
            logger.info("CLI stopped")
    return exit_code


def _ensure_utf8() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]


def _configure_model_loading(settings: Settings) -> None:
    """Project typed model-loading settings into native library environment keys."""
    os.environ.update(
        {
            "HF_HUB_DISABLE_PROGRESS_BARS": "1"
            if settings.hf_hub_disable_progress_bars
            else "0",
            "TQDM_DISABLE": "1" if settings.tqdm_disable else "0",
            "TRANSFORMERS_VERBOSITY": settings.transformers_verbosity,
        }
    )
    configured_level = logging.getLevelNamesMapping()[settings.model_library_log_level]
    for logger_name in ("huggingface_hub", "transformers", "sentence_transformers"):
        logging.getLogger(logger_name).setLevel(configured_level)


def _diagnostic_translator() -> Translator:
    """Provide only the messages needed when the base catalog cannot load."""
    return Translator(
        Locale.EN_US,
        {
            "startup.settings_error": "Configuration error: {detail}",
            "startup.failed": "Startup failed; check the configuration or logs and try again.",
            "close.worker_failed": "CLI Worker close failed; check the logs.",
            "close.application_failed": "Application resource close failed; check the logs.",
            "close.worker_timeout": "Resource close timed out ({resource}): {detail}",
            "close.resource_failed": "Resource close failed ({resource}): {detail}",
        },
    )


def _load_bootstrap_translator(project_root: Path) -> Translator | None:
    """Load a catalog before Settings so configuration errors remain readable."""
    locales_dir = _bootstrap_locales_dir(project_root)
    try:
        ui_locale = parse_locale(
            os.environ.get("UI_LOCALE", Locale.ZH_CN.value),
            setting_name="UI_LOCALE",
        )
    except ValueError:
        ui_locale = Locale.ZH_CN
    try:
        return load_translator(locales_dir, ui_locale)
    except LocaleCatalogError:
        if ui_locale is Locale.ZH_CN:
            return None
        try:
            return load_translator(locales_dir, Locale.ZH_CN)
        except LocaleCatalogError:
            return None


def _bootstrap_locales_dir(project_root: Path) -> Path:
    """Resolve the raw bootstrap path without ever entering legacy data roots."""
    raw = os.environ.get("LOCALES_DIR", "").strip()
    if not raw:
        return project_root / DEFAULT_LOCALES_DIR
    try:
        return resolve_config_path("LOCALES_DIR", raw, project_root)
    except SettingsValidationError:
        return project_root / DEFAULT_LOCALES_DIR
