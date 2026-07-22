"""Terminal input controlled by the CLI without Application state access."""

from collections.abc import Callable, Iterable
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import questionary
from prompt_toolkit.filters import has_completions
from prompt_toolkit.key_binding import KeyBindings


CompletionProvider = Callable[[], tuple[str, ...]]
Editor = Callable[[], str | None]


class InputController:
    """Owns process-local input navigation, editor input, and completion lookup."""

    def __init__(self, editor: Editor | None = None) -> None:
        self._editor = editor or _edit_with_system_editor
        self._completion_provider: CompletionProvider = lambda: ()
        self._history: list[str] = []
        self._history_cursor = -1

    def set_completions(self, provider: CompletionProvider) -> None:
        """Inject a lazy completion provider without depending on a command registry."""
        self._completion_provider = provider

    def read(self, prefill: str | None = None) -> str | None:
        """Read one input line, using current completions and local history navigation."""
        try:
            answer = questionary.autocomplete(
                "",
                choices=self._completion_provider(),
                default=prefill or "",
                qmark=">",
                key_bindings=self._key_bindings(),
            ).ask()
        except (EOFError, KeyboardInterrupt):
            return None
        return answer

    def edit(self) -> str | None:
        """Open the configured editor and return its non-empty trimmed content."""
        text = self._editor()
        return text.strip() if text else None

    def confirm(self, prompt: str) -> bool | None:
        try:
            choice = questionary.select(
                prompt,
                choices=("✅ 执行", "❌ 取消"),
                qmark="",
            ).ask()
            return choice == "✅ 执行"
        except (EOFError, KeyboardInterrupt):
            return None

    def select(self, prompt: str, choices: Iterable[str], allow_custom: bool = False) -> str | None:
        options = list(choices)
        custom_choice = "🔧 自定义输入..."
        if allow_custom:
            options.append(custom_choice)
        try:
            selected = questionary.select(prompt, choices=options, qmark="").ask()
            if selected != custom_choice:
                return selected
            return questionary.text("请输入:", qmark="").ask()
        except (EOFError, KeyboardInterrupt):
            return None

    def remember(self, text: str) -> None:
        """Remember ordinary user text for this process only."""
        normalized = text.strip()
        if normalized and not normalized.startswith("/"):
            self._history.append(normalized)
        self._history_cursor = -1

    def replace_history(self, entries: Iterable[str]) -> None:
        """Replace navigation history after restore or rewind without persistence."""
        self._history = [entry.strip() for entry in entries if entry.strip() and not entry.strip().startswith("/")]
        self._history_cursor = -1

    def _key_bindings(self) -> KeyBindings:
        bindings = KeyBindings()

        @bindings.add("up", filter=~has_completions)  # type: ignore[arg-type]
        def up(event: object) -> None:
            if not self._history or self._history_cursor >= len(self._history) - 1:
                return
            self._history_cursor += 1
            _replace_buffer(event, self._history[-(self._history_cursor + 1)])

        @bindings.add("down", filter=~has_completions)  # type: ignore[arg-type]
        def down(event: object) -> None:
            if self._history_cursor <= 0:
                self._history_cursor = -1
                _replace_buffer(event, "")
                return
            self._history_cursor -= 1
            _replace_buffer(event, self._history[-(self._history_cursor + 1)])

        return bindings


def _replace_buffer(event: object, text: str) -> None:
    buffer = event.current_buffer  # type: ignore[union-attr]
    buffer.text = text
    buffer.cursor_position = len(text)


def _edit_with_system_editor() -> str | None:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or ("notepad" if sys.platform == "win32" else "nano")
    path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", prefix="getmein_", encoding="utf-8", delete=False) as file:
            path = Path(file.name)
        subprocess.call([editor, str(path)])
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
