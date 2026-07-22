"""Composition for the standalone v2 CLI entry point."""

import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from src.get_me_in.application.settings import Settings, SettingsValidationError
from src.get_me_in.bootstrap import build_application
from src.get_me_in.cli.app import CliApp
from src.get_me_in.cli.commands import build_command_registry
from src.get_me_in.cli.input import InputController
from src.get_me_in.cli.renderer import Renderer
from src.get_me_in.cli.worker import WorkerRunner


def main() -> int:
    """Build, run, and close the v2 CLI without changing the legacy entry point."""
    _ensure_utf8()
    project_root = Path(__file__).resolve().parents[3]
    load_dotenv(project_root / ".env")
    renderer = Renderer()
    try:
        settings = Settings.from_env(os.environ, project_root=project_root)
    except SettingsValidationError as error:
        renderer.render_error(str(error))
        return 2

    application = build_application(settings)
    input_controller = InputController()
    commands = build_command_registry(application, input_controller, renderer)
    input_controller.set_completions(commands.completions)
    worker = WorkerRunner(application, renderer)
    app = CliApp(application, commands, input_controller, renderer, worker)
    try:
        return app.run()
    finally:
        worker.close()
        application.close()


def _ensure_utf8() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
