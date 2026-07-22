"""Contract tests for the first R5 CLI command slice."""

from dataclasses import dataclass
import unittest

from src.get_me_in.application.app_commands import DumpSession, ExitSubAgent, RestoreSession, RewindSession
from src.get_me_in.cli.commands import (
    ApprovalMode,
    CommandAction,
    CommandRegistry,
    CommandResult,
    CommandSpec,
    build_command_registry,
)


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
        self.assertEqual(["会话已导出：export.md"], self.renderer.notices)


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


class _InputController:
    def __init__(self) -> None:
        self.editor_result: str | None = None
        self.history: tuple[str, ...] = ()

    def edit(self) -> str | None:
        return self.editor_result

    def replace_history(self, entries: tuple[str, ...]) -> None:
        self.history = entries


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
