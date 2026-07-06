"""CLI 交互入口 — 对话循环 + rich 渲染 + $EDITOR 长文本输入。

用法:
    from src.cli import App
    from src.cli.handler import DemoHandler

    app = App(handler=DemoHandler())
    app.run()
"""

import os
import subprocess
import sys
import tempfile
import threading
import time

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.cli.handler import Handler
from src.config import config
from src.message import Message
from src.rag import load


def _ensure_utf8() -> None:
    """Windows 下强制 stdout 使用 UTF-8，避免 GBK 编码报错。"""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]


def _resolve_editor() -> str:
    """解析编辑器路径。

    优先级: $EDITOR → $VISUAL → 平台 fallback
    - Windows: notepad
    - macOS/Linux: nano
    """
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        return editor
    if sys.platform == "win32":
        return "notepad"
    return "nano"


def _edit_text() -> str:
    """弹出编辑器获取用户输入。

    创建临时文件 → 阻塞等编辑器退出 → 读取内容 → 删除临时文件。
    如果编辑器启动失败，返回空字符串并打印错误。
    """
    editor = _resolve_editor()

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        prefix="getmein_",
        encoding="utf-8",
        delete=False,
    ) as f:
        tmp_path = f.name

    try:
        subprocess.call([editor, tmp_path])
    except FileNotFoundError:
        print(f"编辑器未找到: {editor}。请设置 $EDITOR 环境变量。")
        os.unlink(tmp_path)
        return ""

    with open(tmp_path, encoding="utf-8") as f:
        content = f.read()

    os.unlink(tmp_path)
    return content.strip()


class App:
    """CLI 应用 — 纯 I/O 层。

    依赖注入 Handler 处理输入，自身不调 LLM 或 Agent。
    负责：接收输入 → 委托 Handler → rich 渲染输出。
    """

    def __init__(self, handler: Handler) -> None:
        self._handler = handler
        self._console = Console(force_terminal=True)
        self._editor = _resolve_editor()

    def _process_with_spinner(self, msg: Message) -> Response:
        """后台调 handler.process()，主线程显示等待动效。

        格式: ``. 处理中 0.0s`` → ``.. 处理中 0.5s`` → ``... 处理中 1.0s``，
        每 0.1s 刷新，``\\r`` 单行覆盖。
        """
        result = None
        done = threading.Event()
        start = time.time()

        def _run() -> None:
            nonlocal result
            result = self._handler.process(msg)
            done.set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        while not done.is_set():
            elapsed = time.time() - start
            dots = "." * (int(elapsed * 2) % 3 + 1)
            sys.stderr.write(f"\r{dots:<3} 处理中 {elapsed:.1f}s  ")
            sys.stderr.flush()
            done.wait(0.1)

        sys.stderr.write("\r" + " " * 24 + "\r")
        sys.stderr.flush()
        return result

    def run(self) -> None:
        """启动对话循环。"""
        _ensure_utf8()
        self._print_welcome()

        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                self._console.print("\n[dim]再见！[/]")
                break

            if not user_input:
                continue

            if user_input == "/exit":
                self._console.print("[dim]再见！[/]")
                break

            if user_input == "/ragreload" or user_input.startswith("/ragreload "):
                target = user_input[11:].strip() or None
                self._console.print(f"[dim]正在重载{target or '全量'}...[/]")
                result = load(target)
                self._console.print(f"[dim]{result}[/]")
                self._console.print()
                continue

            if user_input == "/edit":
                self._console.print(f"[dim]启动编辑器: {self._editor} ...[/]")
                content = _edit_text()
                if not content:
                    self._console.print("[yellow]未输入内容，已取消[/]")
                    continue
                msg = Message(message=content, event_type="user_input")
                response = self._process_with_spinner(msg)
            else:
                msg = Message(message=user_input, event_type="user_input")
                response = self._process_with_spinner(msg)

            self._console.print()
            if config.SHOW_THINKING and response.thinking:
                self._console.print(Panel(response.thinking, title="思考", border_style="dim"))
            self._console.print(Markdown(response.message))
            self._console.print()

    def _print_welcome(self) -> None:
        self._console.print()
        self._console.print(
            Panel.fit("[bold green]get-me-in[/] — AI 求职助手")
        )
        self._console.print("[dim]命令: /edit 长文本输入 | /ragreload [关键词] 重载RAG | /exit 退出[/]")
        self._console.print()
