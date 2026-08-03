"""CliApp protocol tests for typed command and event driving."""

import unittest
from pathlib import Path

from src.get_me_in.application.commands import Approve, CancelSelection, Continue, Reject, UserMessage
from src.get_me_in.application.app_commands import ReloadKnowledge
from src.get_me_in.application.app_results import ApplicationResult, TurnFinalizationResult
from src.get_me_in.application.localization import Locale
from src.get_me_in.application.events import ApprovalRequested, Cancelled, Completed, Failed, HandoffRequested, Paused, Progress, SelectionRequested, ToolFinished
from src.get_me_in.cli.app import CliApp
from src.get_me_in.cli.commands import ApprovalMode, CommandAction, CommandResult
from src.get_me_in.cli.localization import load_translator
from src.get_me_in.domain.messages import MessageRecord, Role
from datetime import datetime, timezone


def _translator(locale: Locale = Locale.ZH_CN):
    return load_translator(
        Path(__file__).resolve().parents[2] / "data/locales",
        locale,
    )


class CliAppTests(unittest.TestCase):
    def test_renders_welcome_once_before_first_input(self) -> None:
        trace: list[str] = []
        renderer = _Renderer(trace)
        app = CliApp(
            _Application(),
            _Commands((CommandResult(CommandAction.EXIT),)),
            _Input(("/exit",), trace=trace),
            renderer,
            _Worker(()),
            translator=_translator(),
        )

        self.assertEqual(0, app.run())

        self.assertEqual(["welcome", "read"], trace)
        self.assertEqual(1, renderer.welcomes)

    def test_drives_handoff_with_continue_and_snapshots_terminal_event(self) -> None:
        application = _Application()
        worker = _Worker((HandoffRequested("call", "main", "resume", "context"), Completed(_message())))
        app = CliApp(
            application,
            _Commands((None, CommandResult(CommandAction.EXIT))),
            _Input(("hello", "/exit")),
            _Renderer(),
            worker,
            translator=_translator(),
        )

        self.assertEqual(0, app.run())
        self.assertEqual((UserMessage("hello"), Continue()), worker.commands)
        self.assertEqual(1, application.snapshots)

    def test_auto_approval_uses_typed_approve_without_prompting(self) -> None:
        application = _Application()
        worker = _Worker((ApprovalRequested("call", "write file"), Completed(_message())))
        input_controller = _Input(("/approval auto", "hello", "/exit"))
        app = CliApp(
            application,
            _Commands((CommandResult(CommandAction.SET_APPROVAL, approval_mode=ApprovalMode.AUTO), None, CommandResult(CommandAction.EXIT))),
            input_controller,
            _Renderer(),
            worker,
            translator=_translator(),
        )

        app.run()

        self.assertEqual((UserMessage("hello"), Approve("call")), worker.commands)
        self.assertEqual(0, input_controller.confirms)

    def test_rejected_approval_returns_to_input_without_continuing_model_loop(self) -> None:
        application = _Application()
        worker = _Worker((ApprovalRequested("call", "web search"), Paused("approval_rejected", "User rejected approval")))
        input_controller = _Input(("hello", "/exit"), approved=False)
        app = CliApp(
            application,
            _Commands((None, CommandResult(CommandAction.EXIT))),
            input_controller,
            _Renderer(),
            worker,
            translator=_translator(),
        )

        app.run()

        self.assertEqual(
            (UserMessage("hello"), Reject("call", "User rejected approval")),
            worker.commands,
        )
        self.assertEqual(1, application.snapshots)

    def test_subagent_failure_returns_to_user_without_continuing_main_model_loop(self) -> None:
        application = _Application()
        worker = _Worker((Paused("invalid_model_reply", "Model response remained invalid after one repair attempt"),))
        app = CliApp(
            application,
            _Commands((None, CommandResult(CommandAction.EXIT))),
            _Input(("hello", "/exit")),
            _Renderer(),
            worker,
            translator=_translator(),
        )

        app.run()

        self.assertEqual((UserMessage("hello"),), worker.commands)
        self.assertEqual(1, application.snapshots)

    def test_cancelled_selection_returns_to_cli_until_next_user_message(self) -> None:
        application = _Application()
        worker = _Worker(
            (
                SelectionRequested("choice-call", "pick", ("a", "b")),
                Paused("selection_cancelled", "Selection cancelled by user"),
            )
        )
        app = CliApp(
            application,
            _Commands((None, CommandResult(CommandAction.EXIT))),
            _Input(("hello", "/exit")),
            _Renderer(),
            worker,
            translator=_translator(),
        )

        app.run()

        self.assertEqual(
            (
                UserMessage("hello"),
                CancelSelection("choice-call"),
            ),
            worker.commands,
        )
        self.assertEqual(1, application.snapshots)

    def test_prefill_command_passes_rewound_input_to_the_next_prompt(self) -> None:
        input_controller = _Input(("/rewind", "/exit"))
        app = CliApp(
            _Application(),
            _Commands((CommandResult(CommandAction.PREFILL, "rewound input"), CommandResult(CommandAction.EXIT))),
            input_controller,
            _Renderer(),
            _Worker(()),
            translator=_translator(),
        )

        app.run()

        self.assertEqual([None, "rewound input"], input_controller.prefills)

    def test_command_runtime_event_is_driven_until_terminal(self) -> None:
        application = _Application()
        event = ToolFinished("call", "switch_to_subagent", "closed")
        worker = _Worker((Completed(_message()),))
        app = CliApp(
            application,
            _Commands((CommandResult(CommandAction.DRIVE, event=event), CommandResult(CommandAction.EXIT))),
            _Input(("/exit_sub", "/exit")),
            _Renderer(),
            worker,
            translator=_translator(),
        )

        app.run()

        self.assertEqual((Continue(),), worker.commands)
        self.assertEqual(1, application.snapshots)

    def test_command_failure_is_rendered_and_input_loop_remains_available(self) -> None:
        renderer = _Renderer()
        app = CliApp(
            _Application(),
            _FailingCommands(),
            _Input(("/exit_sub", "/exit")),
            renderer,
            _Worker(()),
            translator=_translator(),
        )

        self.assertEqual(0, app.run())

        self.assertEqual(["命令执行失败：No sub-agent handoff is active"], renderer.errors)

    def test_approval_without_argument_toggles_from_prompt_to_auto(self) -> None:
        application = _Application()
        renderer = _Renderer()
        app = CliApp(
            application,
            _Commands((CommandResult(CommandAction.SET_APPROVAL), CommandResult(CommandAction.EXIT))),
            _Input(("/approval", "/exit")),
            renderer,
            _Worker(()),
            translator=_translator(),
        )

        app.run()

        self.assertEqual(["审批模式：auto"], renderer.notices)

    def test_english_approval_notice_uses_translator(self) -> None:
        application = _Application()
        renderer = _Renderer()
        app = CliApp(
            application,
            _Commands((CommandResult(CommandAction.SET_APPROVAL), CommandResult(CommandAction.EXIT))),
            _Input(("/approval", "/exit")),
            renderer,
            _Worker(()),
            translator=_translator(Locale.EN_US),
        )

        app.run()

        self.assertEqual(["Approval mode: auto"], renderer.notices)

    def test_snapshot_failure_is_rendered_without_replacing_completed_event(self) -> None:
        application = _Application(fail_snapshot=True)
        renderer = _Renderer()
        app = CliApp(
            application,
            _Commands((None, CommandResult(CommandAction.EXIT))),
            _Input(("hello", "/exit")),
            renderer,
            _Worker((Completed(_message()),)),
            translator=_translator(),
        )

        app.run()

        self.assertEqual(1, application.snapshots)
        self.assertIn("会话保存失败", renderer.errors[0])

    def test_run_command_renders_only_a_typed_application_result(self) -> None:
        renderer = _Renderer()
        result = _ApplicationResult()
        worker = _Worker((result,))
        app = CliApp(
            _Application(),
            _Commands((CommandResult(CommandAction.RUN, command=ReloadKnowledge()), CommandResult(CommandAction.EXIT))),
            _Input(("/ragreload", "/exit")),
            renderer,
            worker,
            translator=_translator(),
        )

        app.run()

        self.assertEqual((ReloadKnowledge(),), worker.commands)
        self.assertEqual([result], renderer.application_results)


class _Application:
    def __init__(self, fail_snapshot: bool = False) -> None:
        self.fail_snapshot = fail_snapshot
        self.snapshots = 0

    def finalize_turn(self) -> TurnFinalizationResult:
        self.snapshots += 1
        if self.fail_snapshot:
            return TurnFinalizationResult(snapshot_error="disk full")
        return TurnFinalizationResult()


class _Worker:
    def __init__(self, events: tuple[object, ...]) -> None:
        self.events = list(events)
        self.commands: tuple[object, ...] = ()

    def run(self, command: object) -> object:
        self.commands += (command,)
        return self.events.pop(0)


class _Commands:
    def __init__(self, results: tuple[CommandResult | None, ...]) -> None:
        self.results = list(results)

    def dispatch(self, text: str) -> CommandResult | None:
        return self.results.pop(0)


class _FailingCommands:
    def __init__(self) -> None:
        self._failed = False

    def dispatch(self, text: str) -> CommandResult:
        if not self._failed:
            self._failed = True
            raise ValueError("No sub-agent handoff is active")
        return CommandResult(CommandAction.EXIT)


class _Input:
    def __init__(self, values: tuple[str, ...], *, approved: bool = True, trace: list[str] | None = None) -> None:
        self.values = list(values)
        self.approved = approved
        self.confirms = 0
        self.prefills: list[str | None] = []
        self.trace = trace

    def read(self, prefill: str | None) -> str | None:
        if self.trace is not None:
            self.trace.append("read")
        self.prefills.append(prefill)
        return self.values.pop(0)

    def remember(self, text: str) -> None:
        pass

    def confirm(self, prompt: str) -> bool:
        self.confirms += 1
        return self.approved

    def select(self, prompt: str, choices: tuple[str, ...], allow_custom: bool = False) -> str | None:
        return None


class _Renderer:
    def __init__(self, trace: list[str] | None = None) -> None:
        self.errors: list[str] = []
        self.notices: list[str] = []
        self.application_results: list[ApplicationResult] = []
        self.trace = trace
        self.welcomes = 0

    def render_welcome(self) -> None:
        self.welcomes += 1
        if self.trace is not None:
            self.trace.append("welcome")

    def render_event(self, event: object) -> None:
        pass

    def render_notice(self, message: str) -> None:
        self.notices.append(message)

    def render_error(self, message: str) -> None:
        self.errors.append(message)

    def render_application_result(self, result: ApplicationResult) -> None:
        self.application_results.append(result)


class _ApplicationResult(ApplicationResult):
    pass


def _message() -> MessageRecord:
    return MessageRecord("event", Role.ASSISTANT, "done", datetime(2026, 7, 22, tzinfo=timezone.utc), "turn")
