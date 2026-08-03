"""Typed CLI command parsing and dispatch without Runtime internals."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum

from src.get_me_in.application.app_commands import ApplicationCommand, BuildMemory, DumpSession, ExitSubAgent, ReloadKnowledge, RestoreSession, RewindSession
from src.get_me_in.application.events import RuntimeEvent
from src.get_me_in.cli.localization import Translator


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
@dataclass(frozen=True)
class CommandSpec:
    name: str
    description: str
    handler: CommandHandler
    aliases: tuple[str, ...] = ()


class CommandRegistry:
    """Owns command names, aliases, help text, and replaceable handlers."""

    def __init__(
        self,
        specs: Iterable[CommandSpec] = (),
        *,
        translator: Translator | None = None,
    ) -> None:
        self._translator = translator
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
            message = (
                self._translator.text("command.unknown", command=command)
                if self._translator is not None
                else f"未知命令：{command}"
            )
            return CommandResult(CommandAction.HANDLED, text=message)
        return self._specs[target].handler(arguments.strip())

    def help_entries(self) -> tuple[tuple[str, str], ...]:
        entries = [
            (
                name,
                spec.description
                if name == spec.name
                else (
                    self._translator.text("command.alias", command=spec.name)
                    if self._translator is not None
                    else f"兼容别名；请参见 {spec.name} 的参数说明"
                ),
            )
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
    translator: Translator,
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
        return handled(translator.text("command.exported", path=path))

    def restore_command(arguments: str) -> CommandResult:
        if not arguments:
            sessions = application.list_sessions()
            if not sessions:
                return handled(translator.text("command.restore.no_sessions"))
            choices = _restore_choices(sessions, translator=translator)
            cancel = translator.text("input.cancel")
            selected = input_controller.select(
                translator.text("command.restore.select"),
                (*choices, cancel),
            )
            if selected is None or selected == cancel:
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
                return handled(translator.text("command.rewind.no_points"))
            choices = _rewind_choices(
                points,
                preview_chars=session_preview_chars,
                translator=translator,
            )
            cancel = translator.text("input.cancel")
            selected = input_controller.select(
                translator.text("command.rewind.select"),
                (*choices, cancel),
            )
            if selected is None or selected == cancel:
                return CommandResult(CommandAction.HANDLED)
            arguments = choices[selected]
        prefill = next((point.user_text for point in points if point.turn_id == arguments), None)
        view = application.handle(RewindSession(arguments))
        renderer.render_session(view)
        input_controller.replace_history(tuple(point.user_text for point in view.rewind_points))
        return CommandResult(CommandAction.PREFILL, text=prefill) if prefill is not None else CommandResult(CommandAction.HANDLED)

    def unavailable_command(_: str) -> CommandResult:
        return handled(translator.text("command.unavailable"))

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
            return handled(translator.text("command.exit_sub.usage"))
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
            return handled(translator.text("command.approval.invalid"))
        return CommandResult(CommandAction.SET_APPROVAL, approval_mode=mode)

    registry = CommandRegistry(translator=translator)
    registry.register(CommandSpec("/help", translator.text("command.help.description"), help_command))
    registry.register(CommandSpec("/edit", translator.text("command.edit.description"), edit_command))
    registry.register(CommandSpec("/dump", translator.text("command.dump.description"), dump_command))
    registry.register(CommandSpec("/restore", translator.text("command.restore.description"), restore_command))
    registry.register(CommandSpec("/rewind", translator.text("command.rewind.description"), rewind_command))
    registry.register(CommandSpec("/ragreload", translator.text("command.ragreload.unavailable_description"), unavailable_command))
    registry.register(CommandSpec("/build-memory", translator.text("command.build_memory.unavailable_description"), unavailable_command))
    registry.register(CommandSpec("/exit_sub", translator.text("command.exit_sub.description"), exit_subagent_command))
    registry.register(CommandSpec("/approval", translator.text("command.approval.description"), approval_command))
    registry.register(CommandSpec("/exit", translator.text("command.exit.description"), lambda _: CommandResult(CommandAction.EXIT)))
    registry.replace(CommandSpec("/ragreload", translator.text("command.ragreload.description"), reload_command))
    registry.replace(CommandSpec("/build-memory", translator.text("command.build_memory.description"), build_memory_command))
    return registry


def _validate_name(name: str) -> str:
    normalized = name.casefold()
    if not normalized.startswith("/") or len(normalized) == 1 or any(character.isspace() for character in normalized):
        raise ValueError(f"invalid command name: {name!r}")
    return normalized


def _rewind_choices(
    points: Iterable[object],
    *,
    preview_chars: int | None = None,
    translator: Translator,
) -> dict[str, str]:
    """Build human-readable rewind labels while keeping opaque turn ids internal."""
    choices: dict[str, str] = {}
    for index, point in enumerate(points, start=1):
        preview = " ".join(point.user_text.split()) or translator.text("input.blank_preview")
        if preview_chars is not None and len(preview) > preview_chars:
            preview = f"{preview[:preview_chars - 1]}…"
        choices[f"{index}. {preview}"] = point.turn_id
    return choices


def _restore_choices(
    sessions: Iterable[object], *, translator: Translator
) -> dict[str, str]:
    """Build session labels from the public preview without exposing raw history."""
    choices: dict[str, str] = {}
    for index, session in enumerate(sessions, start=1):
        preview = session.preview or translator.text("input.empty_session_preview")
        timestamp = session.updated_at.strftime("%Y-%m-%d %H:%M")
        choices[f"{index}. {preview}  [{timestamp}]"] = session.session_id
    return choices
