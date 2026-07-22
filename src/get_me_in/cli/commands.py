"""Typed CLI command parsing and dispatch without Runtime internals."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum

from src.get_me_in.application.app_commands import DumpSession, ExitSubAgent, RestoreSession, RewindSession


class ApprovalMode(StrEnum):
    """The CLI-owned policy used when an approval event is rendered."""

    PROMPT = "prompt"
    AUTO = "auto"


class CommandAction(StrEnum):
    """Effects a command handler may request from :class:`CliApp`."""

    HANDLED = "handled"
    EXIT = "exit"
    SUBMIT = "submit"
    PREFILL = "prefill"
    SET_APPROVAL = "set_approval"


@dataclass(frozen=True)
class CommandResult:
    action: CommandAction
    text: str | None = None
    approval_mode: ApprovalMode | None = None


CommandHandler = Callable[[str], CommandResult]


@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str
    handler: CommandHandler
    aliases: tuple[str, ...] = ()


class CommandRegistry:
    """Owns command names, aliases, help text, and replaceable handlers."""

    def __init__(self, specs: Iterable[CommandSpec] = ()) -> None:
        self._specs: dict[str, CommandSpec] = {}
        self._names: dict[str, str] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: CommandSpec) -> None:
        """Add a command, rejecting duplicate names and aliases."""
        name = _validate_name(spec.name)
        aliases = tuple(_validate_name(alias) for alias in spec.aliases)
        names = (name, *aliases)
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate command alias in {name}")
        duplicate = next((item for item in names if item in self._names), None)
        if duplicate is not None:
            raise ValueError(f"command name already registered: {duplicate}")
        normalized = CommandSpec(name, spec.description, spec.handler, aliases)
        self._specs[name] = normalized
        self._names.update({item: name for item in names})

    def replace(self, spec: CommandSpec) -> None:
        """Replace one registered command while retaining its command name."""
        name = _validate_name(spec.name)
        if name not in self._specs:
            raise KeyError(f"command is not registered: {name}")
        previous = self._specs[name]
        for item in (previous.name, *previous.aliases):
            del self._names[item]
        del self._specs[name]
        try:
            self.register(spec)
        except Exception:
            self.register(previous)
            raise

    def dispatch(self, text: str) -> CommandResult | None:
        """Dispatch one slash command, or return ``None`` for ordinary input."""
        if not text.startswith("/"):
            return None
        command, _, arguments = text.strip().partition(" ")
        target = self._names.get(command.casefold())
        if target is None:
            return CommandResult(CommandAction.HANDLED, text=f"未知命令：{command}")
        return self._specs[target].handler(arguments.strip())

    def help_entries(self) -> tuple[tuple[str, str], ...]:
        return tuple((spec.name, spec.description) for spec in self._specs.values())

    def completions(self) -> tuple[str, ...]:
        return tuple(self._names)


def build_command_registry(application: object, input_controller: object, renderer: object) -> CommandRegistry:
    """Build R5 commands using only public Application and frontend APIs."""

    def handled(message: str | None = None) -> CommandResult:
        return CommandResult(CommandAction.HANDLED, text=message)

    def help_command(_: str) -> CommandResult:
        renderer.render_help(registry.help_entries())
        return CommandResult(CommandAction.HANDLED)

    def edit_command(_: str) -> CommandResult:
        text = input_controller.edit()
        return CommandResult(CommandAction.SUBMIT, text=text) if text else CommandResult(CommandAction.HANDLED)

    def dump_command(_: str) -> CommandResult:
        path = application.handle(DumpSession())
        return handled(f"会话已导出：{path}")

    def restore_command(arguments: str) -> CommandResult:
        if not arguments:
            sessions = application.list_sessions()
            if not sessions:
                return handled("没有可恢复的会话。")
            arguments = input_controller.select("选择要恢复的会话:", tuple(session.session_id for session in sessions))
            if arguments is None:
                return CommandResult(CommandAction.HANDLED)
        view = application.handle(RestoreSession(arguments))
        renderer.render_session(view)
        input_controller.replace_history(tuple(point.user_text for point in view.rewind_points))
        return CommandResult(CommandAction.HANDLED)

    def rewind_command(arguments: str) -> CommandResult:
        if not arguments:
            points = application.view().rewind_points
            if not points:
                return handled("没有可回退的用户输入。")
            arguments = input_controller.select("选择要回退的输入:", tuple(point.turn_id for point in points))
            if arguments is None:
                return CommandResult(CommandAction.HANDLED)
        view = application.handle(RewindSession(arguments))
        renderer.render_session(view)
        input_controller.replace_history(tuple(point.user_text for point in view.rewind_points))
        text = next((point.user_text for point in view.rewind_points if point.turn_id == arguments), None)
        return CommandResult(CommandAction.PREFILL, text=text) if text is not None else CommandResult(CommandAction.HANDLED)

    def unavailable_command(_: str) -> CommandResult:
        return handled("该命令将在 R6 提供，目前不可用。")

    def exit_subagent_command(_: str) -> CommandResult:
        event = application.handle(ExitSubAgent())
        renderer.render_event(event)
        return CommandResult(CommandAction.HANDLED)

    def approval_command(arguments: str) -> CommandResult:
        try:
            mode = ApprovalMode(arguments.casefold())
        except ValueError:
            return handled("审批模式仅支持 prompt 或 auto。")
        return CommandResult(CommandAction.SET_APPROVAL, approval_mode=mode)

    registry = CommandRegistry()
    registry.register(CommandSpec("/help", "显示可用命令", help_command))
    registry.register(CommandSpec("/edit", "使用编辑器输入长文本", edit_command))
    registry.register(CommandSpec("/dump", "导出当前会话", dump_command))
    registry.register(CommandSpec("/restore", "按 session_id 恢复会话", restore_command))
    registry.register(CommandSpec("/rewind", "回退到指定用户回合", rewind_command))
    registry.register(CommandSpec("/ragreload", "重载知识库（R6 前不可用）", unavailable_command))
    registry.register(CommandSpec("/build-memory", "构建记忆（R6 前不可用）", unavailable_command))
    registry.register(CommandSpec("/exit_sub", "退出当前子 Agent", exit_subagent_command))
    registry.register(CommandSpec("/approval", "设置审批模式：prompt 或 auto", approval_command, ("/auto-approve-switch",)))
    registry.register(CommandSpec("/exit", "退出 CLI", lambda _: CommandResult(CommandAction.EXIT)))
    return registry


def _validate_name(name: str) -> str:
    normalized = name.casefold()
    if not normalized.startswith("/") or len(normalized) == 1 or any(character.isspace() for character in normalized):
        raise ValueError(f"invalid command name: {name!r}")
    return normalized
