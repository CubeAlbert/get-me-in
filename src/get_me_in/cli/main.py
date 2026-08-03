"""Composition for the standalone CLI entry point."""

import os
from pathlib import Path
import sys
import logging

from dotenv import load_dotenv

from src.get_me_in.application.localization import Locale, parse_locale
from src.get_me_in.application.settings import Settings, SettingsValidationError
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
    renderer = Renderer()
    try:
        settings = Settings.from_env(os.environ, project_root=project_root)
    except SettingsValidationError as error:
        if bootstrap_translator is None:
            renderer.render_error(f"Configuration error: {error}")
            return 1
        renderer.render_error(bootstrap_translator.text("startup.settings_error", detail=str(error)))
        return 2
    _configure_model_loading(settings)

    application = None
    worker = None
    exit_code = 1
    logging_ready = False
    translator = bootstrap_translator
    try:
        translator = load_translator(settings.locales_dir, settings.ui_locale)
        renderer = Renderer(
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
        input_controller = InputController()
        commands = build_command_registry(
            application,
            input_controller,
            renderer,
            session_preview_chars=settings.session_preview_chars,
        )
        input_controller.set_completions(commands.completions)
        worker = WorkerRunner(
            application,
            renderer,
            poll_interval_seconds=settings.cli_worker_poll_interval_seconds,
        )
        app = CliApp(application, commands, input_controller, renderer, worker)
        exit_code = app.run()
    except Exception:
        if logging_ready:
            logger.critical(
                "CLI startup or execution failed",
                exc_info=True,
                extra=_FILE_ONLY_LOG,
            )
        if translator is None:
            renderer.render_error("Startup failed; check the configuration or logs and try again.")
        else:
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
                    renderer.render_error(
                        translator.text("close.worker_failed")
                        if translator is not None
                        else "CLI Worker close failed; check the logs."
                    )
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
                    renderer.render_error(
                        translator.text("close.application_failed")
                        if translator is not None
                        else "Application resource close failed; check the logs."
                    )
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
                        if translator is None:
                            renderer.render_error(
                                f"Resource close {'timed out' if issue.timed_out else 'failed'} "
                                f"({issue.resource_name}): {issue.message}"
                            )
                        else:
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
        return project_root / "data/locales"
    configured = Path(raw)
    resolved = configured if configured.is_absolute() else project_root / configured
    canonical = resolved.resolve(strict=False)
    for legacy in ("data/save", "data/memories", "data/chroma", "data/temp"):
        legacy_root = (project_root / legacy).resolve(strict=False)
        if canonical == legacy_root or legacy_root in canonical.parents:
            return project_root / "data/locales"
    return Path(os.path.normpath(str(resolved)))
