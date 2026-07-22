"""CliApp protocol tests for typed command and event driving."""

import unittest

from src.get_me_in.application.commands import Approve, Continue, UserMessage
from src.get_me_in.application.events import ApprovalRequested, Completed, HandoffRequested, Progress
from src.get_me_in.cli.app import CliApp
from src.get_me_in.cli.commands import ApprovalMode, CommandAction, CommandResult
from src.get_me_in.domain.messages import MessageRecord, Role
from datetime import datetime, timezone


class CliAppTests(unittest.TestCase):
    def test_drives_handoff_with_continue_and_snapshots_terminal_event(self) -> None:
        application = _Application()
        worker = _Worker((HandoffRequested("call", "main", "resume", "context"), Completed(_message())))
        app = CliApp(application, _Commands((None, CommandResult(CommandAction.EXIT))), _Input(("hello", "/exit")), _Renderer(), worker)

        self.assertEqual(0, app.run())
        self.assertEqual((UserMessage("hello"), Continue()), worker.commands)
        self.assertEqual(1, application.snapshots)

    def test_auto_approval_uses_typed_approve_without_prompting(self) -> None:
        application = _Application()
        worker = _Worker((ApprovalRequested("call", "write file"), Completed(_message())))
        input_controller = _Input(("/approval auto", "hello", "/exit"))
        app = CliApp(application, _Commands((CommandResult(CommandAction.SET_APPROVAL, approval_mode=ApprovalMode.AUTO), None, CommandResult(CommandAction.EXIT))), input_controller, _Renderer(), worker)

        app.run()

        self.assertEqual((UserMessage("hello"), Approve("call")), worker.commands)
        self.assertEqual(0, input_controller.confirms)

    def test_approval_without_argument_toggles_from_prompt_to_auto(self) -> None:
        application = _Application()
        renderer = _Renderer()
        app = CliApp(application, _Commands((CommandResult(CommandAction.SET_APPROVAL), CommandResult(CommandAction.EXIT))), _Input(("/approval", "/exit")), renderer, _Worker(()))

        app.run()

        self.assertEqual(["审批模式：auto"], renderer.notices)

    def test_snapshot_failure_is_rendered_without_replacing_completed_event(self) -> None:
        application = _Application(fail_snapshot=True)
        renderer = _Renderer()
        app = CliApp(application, _Commands((None, CommandResult(CommandAction.EXIT))), _Input(("hello", "/exit")), renderer, _Worker((Completed(_message()),)))

        app.run()

        self.assertEqual(1, application.snapshots)
        self.assertIn("会话保存失败", renderer.errors[0])


class _Application:
    def __init__(self, fail_snapshot: bool = False) -> None:
        self.fail_snapshot = fail_snapshot
        self.snapshots = 0

    def snapshot(self) -> None:
        self.snapshots += 1
        if self.fail_snapshot:
            raise OSError("disk full")


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


class _Input:
    def __init__(self, values: tuple[str, ...]) -> None:
        self.values = list(values)
        self.confirms = 0

    def read(self, prefill: str | None) -> str | None:
        return self.values.pop(0)

    def remember(self, text: str) -> None:
        pass

    def confirm(self, prompt: str) -> bool:
        self.confirms += 1
        return True

    def select(self, prompt: str, choices: tuple[str, ...], allow_custom: bool = False) -> str | None:
        return None


class _Renderer:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notices: list[str] = []

    def render_event(self, event: object) -> None:
        pass

    def render_notice(self, message: str) -> None:
        self.notices.append(message)

    def render_error(self, message: str) -> None:
        self.errors.append(message)


def _message() -> MessageRecord:
    return MessageRecord("event", Role.ASSISTANT, "done", datetime(2026, 7, 22, tzinfo=timezone.utc), "turn")
