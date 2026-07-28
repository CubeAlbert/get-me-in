"""The thin v2 CLI event driver."""

from src.get_me_in.application.commands import Approve, CancelSelection, Continue, Reject, SubmitSelection, UserMessage
from src.get_me_in.application.app_results import ApplicationResult
from src.get_me_in.application.events import (
    ApprovalRequested,
    Cancelled,
    Completed,
    Failed,
    HandoffRequested,
    Paused,
    Progress,
    RuntimeEvent,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.cli.commands import ApprovalMode, CommandAction, CommandResult


class CliApp:
    """Owns the outer terminal loop while delegating all business work publicly."""

    def __init__(self, application: object, commands: object, input_controller: object, renderer: object, worker: object) -> None:
        self._application = application
        self._commands = commands
        self._input = input_controller
        self._renderer = renderer
        self._worker = worker
        self._approval_mode = ApprovalMode.PROMPT

    def run(self) -> int:
        """Read text, process CLI commands, and drive one RuntimeEvent at a time."""
        prefill: str | None = None
        try:
            self._renderer.render_welcome()
            while True:
                text = self._input.read(prefill)
                prefill = None
                if text is None:
                    return 0
                text = text.strip()
                if not text:
                    continue
                try:
                    result = self._commands.dispatch(text)
                except Exception as error:
                    self._renderer.render_error(f"命令执行失败：{error}")
                    continue
                if result is None:
                    self._input.remember(text)
                    self._drive(self._worker.run(UserMessage(text)))
                    continue
                if result.action is CommandAction.EXIT:
                    return 0
                if result.action is CommandAction.SUBMIT:
                    if result.text:
                        self._input.remember(result.text)
                        self._drive(self._worker.run(UserMessage(result.text)))
                    continue
                if result.action is CommandAction.PREFILL:
                    prefill = result.text
                    continue
                if result.action is CommandAction.SET_APPROVAL:
                    self._approval_mode = (
                        result.approval_mode
                        or (ApprovalMode.AUTO if self._approval_mode is ApprovalMode.PROMPT else ApprovalMode.PROMPT)
                    )
                    self._renderer.render_notice(f"审批模式：{self._approval_mode}")
                    continue
                if result.action is CommandAction.DRIVE:
                    if result.event is None:
                        self._renderer.render_error("命令未返回可驱动的运行事件。")
                    else:
                        self._drive(result.event)
                    continue
                if result.action is CommandAction.RUN:
                    if result.command is None:
                        self._renderer.render_error("命令未返回可执行的应用命令。")
                        continue
                    application_result = self._worker.run(result.command)
                    if not isinstance(application_result, ApplicationResult):
                        self._renderer.render_error("应用命令未返回强类型结果。")
                    else:
                        self._renderer.render_application_result(application_result)
                    continue
                if result.text:
                    self._renderer.render_notice(result.text)
        except KeyboardInterrupt:
            return 0

    def _drive(self, event: RuntimeEvent) -> None:
        while True:
            self._renderer.render_event(event)
            if isinstance(event, (Progress, ToolStarted, ToolFinished, HandoffRequested)):
                event = self._worker.run(Continue())
                continue
            if isinstance(event, ApprovalRequested):
                if self._approval_mode is ApprovalMode.AUTO:
                    event = self._worker.run(Approve(event.call_id))
                else:
                    approved = self._input.confirm(event.summary)
                    event = self._worker.run(Approve(event.call_id) if approved else Reject(event.call_id, "User rejected approval"))
                continue
            if isinstance(event, SelectionRequested):
                value = self._input.select(event.prompt, event.choices, allow_custom=True)
                command = (
                    SubmitSelection(event.request_id, value)
                    if value is not None
                    else CancelSelection(event.request_id)
                )
                event = self._worker.run(command)
                continue
            if isinstance(event, (Completed, Failed, Paused, Cancelled)):
                self._snapshot_after_terminal_event()
                return
            raise TypeError(f"Unsupported RuntimeEvent: {type(event).__name__}")

    def _snapshot_after_terminal_event(self) -> None:
        try:
            result = self._application.finalize_turn()
            if result.snapshot_error:
                self._renderer.render_error(f"会话保存失败：{result.snapshot_error}")
            if result.memory_error:
                self._renderer.render_error(f"自动构建记忆失败：{result.memory_error}")
        except Exception as error:
            self._renderer.render_error(f"会话保存失败：{error}")
