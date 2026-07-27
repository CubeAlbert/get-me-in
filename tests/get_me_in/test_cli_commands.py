"""Contract tests for the first R5 CLI command slice."""

from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
import unittest
from unittest.mock import patch

from rich.console import Console

from src.get_me_in.application.app_commands import BuildMemory, DumpSession, ExitSubAgent, ReloadKnowledge, RestoreSession, RewindSession
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
from src.get_me_in.application.events import Completed, Failed, ToolFinished, ToolStarted
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus
from src.get_me_in.domain.sessions import SessionPreview


class CommandRegistryTests(unittest.TestCase):
    def test_dispatches_alias_and_keeps_non_commands_for_cli_app(self) -> None:
        registry = CommandRegistry((CommandSpec("/hello", "greet", lambda value: CommandResult(CommandAction.SUBMIT, value), ("/hi",)),))

        self.assertEqual(CommandResult(CommandAction.SUBMIT, "Ada"), registry.dispatch("/HI Ada"))
        self.assertIsNone(registry.dispatch("hello"))

    def test_help_completions_and_replace_are_derived_from_specs(self) -> None:
        registry = CommandRegistry((CommandSpec("/known", "old", lambda _: CommandResult(CommandAction.HANDLED), ("/k",)),))
        registry.replace(CommandSpec("/known", "new", lambda _: CommandResult(CommandAction.EXIT), ("/new",)))

        self.assertEqual(
            (("/known", "new"), ("/new", "兼容别名；请参见 /known 的参数说明")),
            registry.help_entries(),
        )
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
        self.assertEqual(("1. first", "2. second", "❌ 取消"), self.input_controller.selection_choices)
        self.assertEqual([RewindSession("turn-2")], self.application.commands)

    def test_interactive_restore_and_rewind_cancel_without_calling_application(self) -> None:
        self.input_controller.selected = "❌ 取消"

        restored = self.registry.dispatch("/restore")
        rewound = self.registry.dispatch("/rewind")

        self.assertEqual(CommandResult(CommandAction.HANDLED), restored)
        self.assertEqual(CommandResult(CommandAction.HANDLED), rewound)
        self.assertEqual([], self.application.commands)

    def test_rewind_prefills_the_target_even_when_it_is_absent_from_the_rewound_view(self) -> None:
        self.application.rewound_view = _View(())

        rewound = self.registry.dispatch("/rewind turn-1")

        self.assertEqual(CommandResult(CommandAction.PREFILL, "first"), rewound)
        self.assertEqual([RewindSession("turn-1")], self.application.commands)
        self.assertEqual((), self.input_controller.history)

    def test_interactive_restore_displays_preview_but_uses_the_matching_session_id(self) -> None:
        self.input_controller.selected = "2. second session  [2026-07-22 09:00]"

        restored = self.registry.dispatch("/restore")

        self.assertEqual(CommandAction.HANDLED, restored.action)
        self.assertEqual(
            ("1. first session  [2026-07-22 08:00]", "2. second session  [2026-07-22 09:00]", "❌ 取消"),
            self.input_controller.selection_choices,
        )
        self.assertEqual([RestoreSession("session-2")], self.application.commands)

    def test_r6_commands_return_typed_application_commands(self) -> None:
        self.assertEqual(
            CommandResult(CommandAction.RUN, command=ReloadKnowledge("references")),
            self.registry.dispatch("/ragreload references"),
        )
        self.assertEqual(
            CommandResult(CommandAction.RUN, command=BuildMemory()),
            self.registry.dispatch("/build-memory"),
        )

    def test_approval_and_exit_commands_have_typed_results(self) -> None:
        self.assertEqual(CommandResult(CommandAction.SET_APPROVAL), self.registry.dispatch("/approval"))
        self.assertEqual(ApprovalMode.AUTO, self.registry.dispatch("/approval auto").approval_mode)
        self.assertIn("仅支持", self.registry.dispatch("/approval on").text)
        self.assertEqual(CommandAction.EXIT, self.registry.dispatch("/exit").action)

    def test_help_entries_are_alphabetical_and_describe_approval_toggle(self) -> None:
        entries = self.registry.help_entries()

        self.assertEqual(tuple(sorted(command for command, _ in entries)), tuple(command for command, _ in entries))
        self.assertNotIn("/auto-approve-switch", tuple(command for command, _ in entries))
        self.assertIn(("/approval", "切换审批模式（可选参数：prompt|auto）"), entries)

    def test_edit_dump_and_exit_subagent_delegate_only_to_public_dependencies(self) -> None:
        self.input_controller.editor_result = "long input"

        self.assertEqual(CommandResult(CommandAction.SUBMIT, "long input"), self.registry.dispatch("/edit"))
        self.registry.dispatch("/dump")
        result = self.registry.dispatch("/exit_sub")

        self.assertEqual([DumpSession(), ExitSubAgent()], self.application.commands)
        self.assertEqual([], self.renderer.notices)
        self.assertEqual(CommandAction.DRIVE, result.action)
        self.assertEqual(ToolFinished("call", "switch_to_subagent", "closed"), result.event)


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

    def test_confirm_uses_explicit_approve_and_reject_choices(self) -> None:
        controller = InputController(editor=lambda: None)

        with patch("src.get_me_in.cli.input.questionary.select") as select:
            select.return_value.ask.return_value = "✅ 执行"
            self.assertTrue(controller.confirm("Approve tool write_file?"))
            select.return_value.ask.return_value = "❌ 取消"
            self.assertFalse(controller.confirm("Approve tool write_file?"))

        self.assertEqual(("✅ 执行", "❌ 取消"), select.call_args_list[0].kwargs["choices"])
        self.assertEqual("", select.call_args_list[0].kwargs["qmark"])


class RendererTests(unittest.TestCase):
    def test_renders_stable_welcome_banner(self) -> None:
        output = StringIO()
        renderer = Renderer(console=_console(output))

        self.assertIsNone(renderer.render_welcome())

        text = output.getvalue()
        self.assertIn("get-me-in", text)
        self.assertIn("AI 求职助手", text)
        self.assertIn("输入 /help 查看所有命令", text)

    def test_renders_typed_terminal_events_without_returning_commands(self) -> None:
        output = StringIO()
        renderer = Renderer(console=_console(output))
        message = MessageRecord("event", Role.ASSISTANT, "**done**", _now(), "turn")

        self.assertIsNone(renderer.render_event(Completed(message)))
        self.assertIsNone(renderer.render_event(Failed("bad", "problem")))

        text = output.getvalue()
        self.assertIn("done", text)
        self.assertIn("bad: problem", text)

    def test_renders_redacted_arguments_result_preview_and_plan_projection(self) -> None:
        output = StringIO()
        renderer = Renderer(console=_console(output))
        plan = Plan("plan", (PlanItem("item", "查询广州 Java 薪资", PlanStatus.IN_PROGRESS),))

        renderer.render_event(ToolStarted("call", "web_search", {"query": "广州 Java 薪资", "api_key": "secret"}))
        renderer.render_event(ToolFinished("call", "web_search", "搜索结果 " * 200))
        renderer.render_event(ToolFinished("plan", "create_plan", "ignored", plan))

        text = output.getvalue()
        self.assertIn("query=广州 Java 薪资", text)
        self.assertIn("api_key=***", text)
        self.assertNotIn("secret", text)
        self.assertIn("工具结果 · web_search", text)
        self.assertIn("执行计划", text)
        self.assertIn("查询广州 Java 薪资", text)

    def test_renders_thinking_only_when_enabled(self) -> None:
        hidden_output = StringIO()
        shown_output = StringIO()
        message = MessageRecord("event", Role.ASSISTANT, "done", _now(), "turn", "final summary")

        Renderer(console=_console(hidden_output)).render_event(Completed(message))
        Renderer(console=_console(shown_output), show_thinking=True).render_event(ToolStarted("call", "search", thinking="tool summary"))
        Renderer(console=_console(shown_output), show_thinking=True).render_event(Completed(message))

        self.assertNotIn("final summary", hidden_output.getvalue())
        self.assertIn("思考摘要", shown_output.getvalue())
        self.assertIn("tool summary", shown_output.getvalue())
        self.assertIn("final summary", shown_output.getvalue())
        self.assertLess(
            shown_output.getvalue().index("final summary"),
            shown_output.getvalue().index("done"),
        )


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
        self.rewound_view: _View | None = None

    def handle(self, command: object) -> object:
        self.commands.append(command)
        if isinstance(command, RewindSession) and self.rewound_view is not None:
            return self.rewound_view
        if isinstance(command, DumpSession):
            return "export.md"
        if isinstance(command, ExitSubAgent):
            return ToolFinished("call", "switch_to_subagent", "closed")
        return _View()

    def view(self) -> _View:
        return _View()

    def list_sessions(self) -> tuple[SessionPreview, ...]:
        return (
            SessionPreview("session-1", AgentKey.MAIN, datetime(2026, 7, 22, 8, tzinfo=timezone.utc), "first session"),
            SessionPreview("session-2", AgentKey.MAIN, datetime(2026, 7, 22, 9, tzinfo=timezone.utc), "second session"),
        )


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
