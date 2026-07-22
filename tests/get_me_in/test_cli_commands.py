"""Contract tests for the first R5 CLI command slice."""

from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
import unittest
from unittest.mock import patch

from rich.console import Console

from src.get_me_in.application.app_commands import DumpSession, ExitSubAgent, RestoreSession, RewindSession
from src.get_me_in.cli.commands import (
    ApprovalMode,
    CommandAction,
    CommandRegistry,
    CommandResult,
    CommandSpec,
    build_command_registry,
)
from src.get_me_in.cli.input import InputController
from src.get_me_in.cli.renderer import Renderer
from src.get_me_in.application.events import Completed, Failed
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role


class CommandRegistryTests(unittest.TestCase):
    def test_dispatches_alias_and_keeps_non_commands_for_cli_app(self) -> None:
        registry = CommandRegistry((CommandSpec("/hello", "greet", lambda value: CommandResult(CommandAction.SUBMIT, value), ("/hi",)),))

        self.assertEqual(CommandResult(CommandAction.SUBMIT, "Ada"), registry.dispatch("/HI Ada"))
        self.assertIsNone(registry.dispatch("hello"))

    def test_help_completions_and_replace_are_derived_from_specs(self) -> None:
        registry = CommandRegistry((CommandSpec("/known", "old", lambda _: CommandResult(CommandAction.HANDLED), ("/k",)),))
        registry.replace(CommandSpec("/known", "new", lambda _: CommandResult(CommandAction.EXIT), ("/new",)))

        self.assertEqual((("/known", "new"),), registry.help_entries())
        self.assertEqual(("/known", "/new"), registry.completions())
        self.assertEqual(CommandAction.EXIT, registry.dispatch("/new").action)
        self.assertEqual("未知命令：/k", registry.dispatch("/k").text)

    def test_duplicate_registered_names_are_rejected(self) -> None:
        registry = CommandRegistry((CommandSpec("/help", "help", lambda _: CommandResult(CommandAction.HANDLED)),))

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(CommandSpec("/other", "other", lambda _: CommandResult(CommandAction.HANDLED), ("/help",)))


class CoreCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.application = _Application()
        self.input_controller = _InputController()
        self.renderer = _Renderer()
        self.registry = build_command_registry(self.application, self.input_controller, self.renderer)

    def test_restore_and_rewind_use_public_application_api_and_refresh_history(self) -> None:
        restored = self.registry.dispatch("/restore session-2")
        rewound = self.registry.dispatch("/rewind turn-1")

        self.assertEqual(CommandAction.HANDLED, restored.action)
        self.assertEqual(CommandAction.PREFILL, rewound.action)
        self.assertEqual("first", rewound.text)
        self.assertEqual([RestoreSession("session-2"), RewindSession("turn-1")], self.application.commands)
        self.assertEqual(("first", "second"), self.input_controller.history)

    def test_interactive_rewind_displays_previews_but_uses_the_matching_turn_id(self) -> None:
        self.input_controller.selected = "2. second"

        rewound = self.registry.dispatch("/rewind")

        self.assertEqual(CommandResult(CommandAction.PREFILL, "second"), rewound)
        self.assertEqual(("1. first", "2. second"), self.input_controller.selection_choices)
        self.assertEqual([RewindSession("turn-2")], self.application.commands)

    def test_unavailable_approval_and_exit_commands_have_typed_results(self) -> None:
        self.assertIn("R6", self.registry.dispatch("/ragreload references").text)
        self.assertEqual(ApprovalMode.AUTO, self.registry.dispatch("/auto-approve-switch auto").approval_mode)
        self.assertEqual(CommandAction.EXIT, self.registry.dispatch("/exit").action)

    def test_edit_dump_and_exit_subagent_delegate_only_to_public_dependencies(self) -> None:
        self.input_controller.editor_result = "long input"

        self.assertEqual(CommandResult(CommandAction.SUBMIT, "long input"), self.registry.dispatch("/edit"))
        self.registry.dispatch("/dump")
        self.registry.dispatch("/exit_sub")

        self.assertEqual([DumpSession(), ExitSubAgent()], self.application.commands)
        self.assertEqual([], self.renderer.notices)


class InputControllerTests(unittest.TestCase):
    def test_read_uses_latest_completion_provider_value_each_time(self) -> None:
        controller = InputController(editor=lambda: None)
        completions = ("/first",)
        controller.set_completions(lambda: completions)
        prompts: list[object] = []

        with patch("src.get_me_in.cli.input.questionary.autocomplete") as autocomplete:
            autocomplete.return_value.ask.return_value = "/first"
            controller.read()
            completions = ("/second",)
            autocomplete.return_value.ask.return_value = "/second"
            controller.read()
            prompts = autocomplete.call_args_list

        self.assertEqual(("/first",), prompts[0].kwargs["choices"])
        self.assertEqual(("/second",), prompts[1].kwargs["choices"])

    def test_editor_and_history_remain_process_local(self) -> None:
        controller = InputController(editor=lambda: "  long text  ")
        controller.remember("first")
        controller.remember("/help")
        controller.replace_history(("restored", "/exit", "  "))

        self.assertEqual("long text", controller.edit())
        self.assertEqual(["restored"], controller._history)


class RendererTests(unittest.TestCase):
    def test_renders_typed_terminal_events_without_returning_commands(self) -> None:
        output = StringIO()
        renderer = Renderer(console=_console(output))
        message = MessageRecord("event", Role.ASSISTANT, "**done**", _now(), "turn")

        self.assertIsNone(renderer.render_event(Completed(message)))
        self.assertIsNone(renderer.render_event(Failed("bad", "problem")))

        text = output.getvalue()
        self.assertIn("done", text)
        self.assertIn("bad: problem", text)


@dataclass(frozen=True)
class _Turn:
    turn_id: str
    user_text: str


@dataclass(frozen=True)
class _View:
    rewind_points: tuple[_Turn, ...] = (_Turn("turn-1", "first"), _Turn("turn-2", "second"))


class _Application:
    def __init__(self) -> None:
        self.commands: list[object] = []

    def handle(self, command: object) -> object:
        self.commands.append(command)
        if isinstance(command, DumpSession):
            return "export.md"
        if isinstance(command, ExitSubAgent):
            return "event"
        return _View()

    def view(self) -> _View:
        return _View()


class _InputController:
    def __init__(self) -> None:
        self.editor_result: str | None = None
        self.history: tuple[str, ...] = ()
        self.selected: str | None = None
        self.selection_choices: tuple[str, ...] = ()

    def edit(self) -> str | None:
        return self.editor_result

    def replace_history(self, entries: tuple[str, ...]) -> None:
        self.history = entries

    def select(self, prompt: str, choices: tuple[str, ...]) -> str | None:
        self.selection_choices = choices
        return self.selected


class _Renderer:
    def __init__(self) -> None:
        self.notices: list[str] = []

    def render_notice(self, message: str) -> None:
        self.notices.append(message)

    def render_help(self, entries: tuple[tuple[str, str], ...]) -> None:
        pass

    def render_session(self, view: _View) -> None:
        pass

    def render_event(self, event: object) -> None:
        pass


def _console(output: StringIO) -> Console:
    return Console(file=output, force_terminal=False, color_system=None)


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
