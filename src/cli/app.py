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

import questionary
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.agents.registry import get_agent_registry
from src.cli.handler import Handler
from src.config import config
from src.message import EventType, Message
from src.rag import load
from src.request import Request, RequestType
from src.response import ConfirmChoice, Response, ResponseType


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

    _COMMANDS = ["/exit", "/edit", "/ragreload", "/exit_sub"]

    def __init__(self, handler: Handler) -> None:
        self._handler = handler
        self._main_agent = handler  # 切回目标，子 Agent 退出时回到这里
        self._switch_tool_call_id: str | None = None  # main→sub 时的 TOOL_CALL id
        self._console = Console(force_terminal=True)
        self._editor = _resolve_editor()

    @staticmethod
    def _complete_commands() -> list[str]:
        """返回所有可用命令列表，由 questionary 按输入做前缀匹配。"""
        return App._COMMANDS

    def _get_handler(self, name: str) -> Handler | None:
        """按名获取 handler 实例。

        ``"main"`` 返回主 Agent，其他从 AgentRegistry 查找。
        """
        if name == "main":
            return self._main_agent
        try:
            return get_agent_registry().get(name)
        except KeyError:
            return None

    def _process_with_spinner(self, request: Request) -> Response:
        """后台调 handler.process()，主线程显示等待动效。

        格式: ``. 处理中 0.0s`` → ``.. 处理中 0.5s`` → ``... 处理中 1.0s``，
        每 0.1s 刷新，``\\r`` 单行覆盖。
        """
        result = None
        done = threading.Event()
        start = time.time()

        def _run() -> None:
            nonlocal result
            result = self._handler.process(request)
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
        """启动对话循环。

        外层循环：等用户输入。
        内层循环：agent loop，阻塞用户输入，按 ResponseType 分支：
          - FINISH   → 渲染，回外层
          - PROGRESS → 渲染，自动 CONTINUE
          - CONFIRM  → questionary.select，通过则 CONFIRM_APPROVED，拒绝则回外层
        """
        _ensure_utf8()
        self._print_welcome()

        while True:
            try:
                user_input = questionary.autocomplete(
                    "",
                    choices=self._complete_commands,
                    qmark=">",
                ).ask()
                if user_input is None:  # Ctrl+C
                    self._console.print("\n[dim]再见！[/]")
                    break
                user_input = user_input.strip()
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

            if user_input == "/exit_sub":
                if self._handler is self._main_agent:
                    self._console.print("[red]当前已是主Agent，/exit_sub 仅在子Agent会话中可用[/]")
                    continue
                # 通知子 Agent 整理上下文并退出
                self._handler._history.append(
                    Message(
                        role="user",
                        event_type=EventType.SYSTEM_MESSAGE,
                        message="用户请求主动退出当前会话。请整理本次会话的关键信息和结论，然后调用 switch_to_mainagent 退出。",
                    )
                )
                request = Request(type=RequestType.CONTINUE)
                # 掉入内层循环，由子 Agent LLM 处理

            elif user_input == "/edit":
                self._console.print(f"[dim]启动编辑器: {self._editor} ...[/]")
                content = _edit_text()
                if not content:
                    self._console.print("[yellow]未输入内容，已取消[/]")
                    continue
                request = Request(type=RequestType.USER_INPUT, message=content)
            else:
                request = Request(type=RequestType.USER_INPUT, message=user_input)

            # ── 内层 agent loop ──
            while True:
                response = self._process_with_spinner(request)

                if response.type == ResponseType.FINISH:
                    # switch 检测：Agent 切换
                    if response.switch_agent:
                        if response.switch_agent != "main":
                            # main → sub: 保存 tool_call_id 供切回时匹配
                            if response.switch_tool_call_id:
                                self._switch_tool_call_id = response.switch_tool_call_id
                        else:
                            # sub → main: 注入 TOOL_CALL_RESULT 完成异步调用闭环
                            if self._switch_tool_call_id:
                                self._main_agent._history.append(
                                    Message(
                                        role="user",
                                        event_type=EventType.TOOL_CALL_RESULT,
                                        tool="switch_to_subagent",
                                        tool_call_id=self._switch_tool_call_id,
                                        event_payload={"summary": response.switch_context or ""},
                                    )
                                )
                                self._switch_tool_call_id = None

                        new_handler = self._get_handler(response.switch_agent)
                        if new_handler is None:
                            self._console.print(f"[red]未知 Agent: {response.switch_agent}[/]")
                            break
                        self._handler = new_handler
                        context = response.switch_context or "请开始处理。"
                        request = Request(
                            type=RequestType.USER_INPUT,
                            message=context,
                        )
                        continue  # 留在内层循环，新 handler 开始工作

                    # 正常 FINISH：渲染并回外层
                    self._console.print()
                    if config.SHOW_THINKING and response.thinking:
                        self._console.print(Panel(response.thinking, title="思考", border_style="dim"))
                    self._console.print(Markdown(response.message))
                    self._console.print()
                    break

                if response.type == ResponseType.PROGRESS:
                    self._console.print()
                    if response.message:
                        self._console.print(f"[dim]🔄 {response.message}[/]")
                    request = Request(type=RequestType.CONTINUE)
                    continue

                if response.type == ResponseType.CONFIRM:
                    self._console.print()
                    choice = questionary.select(
                        f"⚠️  {response.message}",
                        choices=[ConfirmChoice.APPROVE, ConfirmChoice.REJECT],
                        qmark="",
                    ).ask()
                    if choice == ConfirmChoice.APPROVE:
                        request = Request(type=RequestType.CONFIRM_APPROVED)
                        continue
                    else:
                        self._console.print("[dim]已取消[/]")
                        break

    def _print_welcome(self) -> None:
        self._console.print()
        self._console.print(
            Panel.fit("[bold green]get-me-in[/] — AI 求职助手")
        )
        self._console.print("[dim]命令: /edit 长文本输入 | /ragreload [关键词] 重载RAG | /exit 退出[/]")
        self._console.print()
