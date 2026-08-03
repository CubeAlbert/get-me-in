"""Typed CLI command parsing and dispatch without Runtime internals."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum

from src.get_me_in.application.app_commands import ApplicationCommand, BuildMemory, DumpSession, ExitSubAgent, ReloadKnowledge, RestoreSession, RewindSession
from src.get_me_in.application.events import RuntimeEvent


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
    DRIVE = "drive"
    RUN = "run"


@dataclass(frozen=True)
class CommandResult:
    action: CommandAction
    text: str | None = None
    approval_mode: ApprovalMode | None = None
    event: RuntimeEvent | None = None
    command: ApplicationCommand | None = None


CommandHandler = Callable[[str], CommandResult]
_CANCEL_SELECTION = "❌ 取消"


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
        entries = [
            (name, spec.description if name == spec.name else f"兼容别名；请参见 {spec.name} 的参数说明")
            for spec in self._specs.values()
            for name in (spec.name, *spec.aliases)
        ]
        return tuple(sorted(entries, key=lambda entry: entry[0]))

    def completions(self) -> tuple[str, ...]:
        return tuple(sorted(self._names))


def build_command_registry(
    application: object,
    input_controller: object,
    renderer: object,
    *,
    session_preview_chars: int | None = None,
) -> CommandRegistry:
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
            choices = _restore_choices(sessions)
            selected = input_controller.select("选择要恢复的会话:", (*choices, _CANCEL_SELECTION))
            if selected is None or selected == _CANCEL_SELECTION:
                return CommandResult(CommandAction.HANDLED)
            arguments = choices[selected]
        view = application.handle(RestoreSession(arguments))
        renderer.render_session(view)
        input_controller.replace_history(tuple(point.user_text for point in view.rewind_points))
        return CommandResult(CommandAction.HANDLED)

    def rewind_command(arguments: str) -> CommandResult:
        points = application.view().rewind_points
        if not arguments:
            if not points:
                return handled("没有可回退的用户输入。")
            choices = _rewind_choices(points, preview_chars=session_preview_chars)
            selected = input_controller.select("选择要回退的输入:", (*choices, _CANCEL_SELECTION))
            if selected is None or selected == _CANCEL_SELECTION:
                return CommandResult(CommandAction.HANDLED)
            arguments = choices[selected]
        prefill = next((point.user_text for point in points if point.turn_id == arguments), None)
        view = application.handle(RewindSession(arguments))
        renderer.render_session(view)
        input_controller.replace_history(tuple(point.user_text for point in view.rewind_points))
        return CommandResult(CommandAction.PREFILL, text=prefill) if prefill is not None else CommandResult(CommandAction.HANDLED)

    def unavailable_command(_: str) -> CommandResult:
        return handled("该命令将在 R6 提供，目前不可用。")

    def reload_command(arguments: str) -> CommandResult:
        return CommandResult(CommandAction.RUN, command=ReloadKnowledge(arguments or None))

    def build_memory_command(_: str) -> CommandResult:
        return CommandResult(CommandAction.RUN, command=BuildMemory())

    def exit_subagent_command(arguments: str) -> CommandResult:
        if not arguments:
            summarize = True
        elif arguments.casefold() in {"true", "false"}:
            summarize = arguments.casefold() == "true"
        else:
            return handled("用法：/exit_sub [true|false]；默认 true，会让子 Agent 总结后退回。")
        event = application.handle(ExitSubAgent(summarize=summarize))
        if not isinstance(event, RuntimeEvent):
            raise TypeError("ExitSubAgent must return a RuntimeEvent")
        return CommandResult(CommandAction.DRIVE, event=event)

    def approval_command(arguments: str) -> CommandResult:
        if not arguments:
            return CommandResult(CommandAction.SET_APPROVAL)
        try:
            mode = ApprovalMode(arguments.casefold())
        except ValueError:
            return handled("审批模式仅支持 prompt 或 auto；不带参数可直接切换。")
        return CommandResult(CommandAction.SET_APPROVAL, approval_mode=mode)

    registry = CommandRegistry()
    registry.register(CommandSpec("/help", "显示可用命令", help_command))
    registry.register(CommandSpec("/edit", "使用编辑器输入长文本", edit_command))
    registry.register(CommandSpec("/dump", "导出当前会话", dump_command))
    registry.register(CommandSpec("/restore", "恢复会话（可选 session_id）", restore_command))
    registry.register(CommandSpec("/rewind", "选择或指定 turn_id 回退到用户回合", rewind_command))
    registry.register(CommandSpec("/ragreload", "重载知识库（可选 target；R6 前不可用）", unavailable_command))
    registry.register(CommandSpec("/build-memory", "构建记忆（R6 前不可用）", unavailable_command))
    registry.register(CommandSpec("/exit_sub", "退出当前子 Agent（默认 true：总结后退回；false：用户主动退出）", exit_subagent_command))
    registry.register(CommandSpec("/approval", "切换审批模式（可选参数：prompt|auto）", approval_command))
    registry.register(CommandSpec("/exit", "退出 CLI", lambda _: CommandResult(CommandAction.EXIT)))
    registry.replace(CommandSpec("/ragreload", "重载知识库（可选 target）", reload_command))
    registry.replace(CommandSpec("/build-memory", "构建当前会话记忆", build_memory_command))
    return registry


def _validate_name(name: str) -> str:
    normalized = name.casefold()
    if not normalized.startswith("/") or len(normalized) == 1 or any(character.isspace() for character in normalized):
        raise ValueError(f"invalid command name: {name!r}")
    return normalized


def _rewind_choices(
    points: Iterable[object], *, preview_chars: int | None = None
) -> dict[str, str]:
    """Build human-readable rewind labels while keeping opaque turn ids internal."""
    choices: dict[str, str] = {}
    for index, point in enumerate(points, start=1):
        preview = " ".join(point.user_text.split()) or "（空白输入）"
        if preview_chars is not None and len(preview) > preview_chars:
            preview = f"{preview[:preview_chars - 1]}…"
        choices[f"{index}. {preview}"] = point.turn_id
    return choices


def _restore_choices(sessions: Iterable[object]) -> dict[str, str]:
    """Build session labels from the public preview without exposing raw history."""
    choices: dict[str, str] = {}
    for index, session in enumerate(sessions, start=1):
        preview = session.preview or "（没有用户输入）"
        timestamp = session.updated_at.strftime("%Y-%m-%d %H:%M")
        choices[f"{index}. {preview}  [{timestamp}]"] = session.session_id
    return choices
