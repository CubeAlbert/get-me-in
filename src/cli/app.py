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
from rich.text import Text

from src.agents.registry import MAIN_AGENT_KEY, get_agent_registry
from src.cli.handler import Handler
from src.cli.uibridge import UIBridge, _set_bridge
from src.config import config
from src.logger import get_logger
from src.message import EventType, Message, Role
from src.rag import load
from src.request import Request, RequestType
from src.response import ConfirmChoice, Response, ResponseType

logger = get_logger(__name__)


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

    _COMMAND_HELP: dict[str, str] = {
        "/auto-approve-switch": "切换工具审批开关 [on|off]",
        "/dump": "导出当前 Agent 对话历史",
        "/edit": "调 $EDITOR 输入长文本",
        "/exit": "退出程序",
        "/exit_sub": "从子 Agent 退回主 Agent",
        "/help": "显示所有命令说明",
        "/ragreload": "重载 RAG 索引（可选关键词）",
        "/restore": "恢复存档会话（无参数列出选择 | /restore <id> 直接恢复）",
    }

    _COMMANDS = list(_COMMAND_HELP.keys())

    def __init__(self, handler: Handler) -> None:
        from pathlib import Path
        from src.utils.saver import SaveManager

        self._handler = handler
        self._main_agent = handler  # 切回目标，子 Agent 退出时回到这里
        self._switch_tool_call_id: str | None = None  # main→sub 时的 TOOL_CALL id
        self._console = Console(force_terminal=True)
        self._editor = _resolve_editor()
        self._save_mgr = SaveManager(Path(config.SAVE_DIR))

    @staticmethod
    def _complete_commands() -> list[str]:
        """返回所有可用命令列表，由 questionary 按输入做前缀匹配。"""
        return App._COMMANDS

    def _get_handler(self, name: str) -> Handler | None:
        """按名获取 handler 实例。

        ``"main"`` 返回主 Agent，其他从 AgentRegistry 查找。
        """
        if name == MAIN_AGENT_KEY:
            return self._main_agent
        try:
            return get_agent_registry().get(name)
        except KeyError:
            return None

    # ── auto-save / restore ──

    def _auto_save(self) -> None:
        """自动保存当前 handler 的对话历史和 plan 状态。"""
        self._save_mgr.save(
            self._handler._get_agent_key(),
            self._handler._history,
            plan=self._handler._plan,
        )

    def _restore_interactive(self) -> None:
        """用 questionary.select 列出存档让用户选择恢复。"""
        sessions = self._save_mgr.list_sessions()
        if not sessions:
            self._console.print("[dim]没有找到存档会话[/]")
            self._console.print()
            return

        choices = []
        for s in sessions:
            detail_parts = []
            if s.get("saved_at"):
                try:
                    ts = s["saved_at"]
                    detail_parts.append(ts[11:19] if "T" in ts else ts)
                except Exception:
                    pass
            if s.get("sub_agent"):
                detail_parts.append(f"sub:{s['sub_agent']}")
            title = s["id"]
            if detail_parts:
                title += f"  [{', '.join(detail_parts)}]"
            choices.append(questionary.Choice(title=title, value=s["id"]))

        selected = questionary.select(
            "选择要恢复的存档:",
            choices=choices,
            qmark="",
        ).ask()

        if selected:
            self._do_restore(selected)

    def _do_restore(self, session_id: str) -> None:
        """从存档目录恢复会话状态（含 plan）。"""
        messages = self._save_mgr.load_main(session_id)
        if messages is None:
            self._console.print("[red]读取存档失败，详见日志[/]")
            self._console.print()
            return

        self._save_mgr.session_id = session_id
        self._main_agent._history = messages
        self._switch_tool_call_id = None

        # 恢复 plan 状态
        plans = self._save_mgr.load_plans(session_id)
        if "main" in plans:
            self._main_agent._plan = plans["main"]

        sub_agent = self._save_mgr.find_sub_agent(session_id)
        if sub_agent:
            sub_messages = self._save_mgr.load_sub(session_id, sub_agent)
            if sub_messages is not None:
                handler = self._get_handler(sub_agent)
                if handler is None:
                    self._console.print(f"[red]未知 Agent: {sub_agent}[/]")
                    self._handler = self._main_agent
                else:
                    handler._history = sub_messages
                    if sub_agent in plans:
                        handler._plan = plans[sub_agent]
                    self._handler = handler
                    self._console.print(
                        f"[dim]已恢复到 {session_id}，当前在 {sub_agent} 子Agent[/]")
            else:
                self._handler = self._main_agent
                self._console.print(
                    f"[yellow]子Agent存档读取失败 ({sub_agent})，仅恢复主Agent[/]")
        else:
            self._handler = self._main_agent
            self._console.print(f"[dim]已恢复到 {session_id}[/]")

        self._console.print()

    # ── agent loop ──

    def _process_with_spinner(self, request: Request, bridge: UIBridge) -> Response:
        """后台调 handler.process()，主线程显示等待动效并处理 UI 请求。

        格式: ``. 处理中 0.0s`` → ``.. 处理中 0.5s`` → ``... 处理中 1.0s``，
        每 0.1s 刷新，``\\r`` 单行覆盖。
        当工具 handler 通过 UIBridge 发起 UI 请求时，暂停 spinner 并渲染
        questionary 交互，完成后再恢复 spinner。
        """
        result = None
        done = threading.Event()
        start = time.time()

        def _run() -> None:
            nonlocal result
            _set_bridge(bridge)
            try:
                result = self._handler.process(request)
            finally:
                _set_bridge(None)
            done.set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()

        while not done.is_set():
            if bridge.has_request:
                sys.stderr.write("\r" + " " * 24 + "\r")
                sys.stderr.flush()
                self._handle_bridge_request(bridge)
            else:
                elapsed = time.time() - start
                dots = "." * (int(elapsed * 2) % 3 + 1)
                sys.stderr.write(f"\r{dots:<3} 处理中 {elapsed:.1f}s  ")
                sys.stderr.flush()
            done.wait(0.1)

        sys.stderr.write("\r" + " " * 24 + "\r")
        sys.stderr.flush()
        return result

    def _handle_bridge_request(self, bridge: UIBridge) -> None:
        """处理 UIBridge 的 UI 请求（主线程中执行）。"""
        self._console.print()
        if bridge.action == "confirm":
            choice = questionary.select(
                f"⚠️  {bridge.question}",
                choices=[ConfirmChoice.APPROVE, ConfirmChoice.REJECT],
                qmark="",
            ).ask()
            bridge.respond(choice == ConfirmChoice.APPROVE)
        elif bridge.action == "select":
            choices = list(bridge.choices) + ["🔧 自定义输入..."]
            choice = questionary.select(
                bridge.question,
                choices=choices,
                qmark="",
            ).ask()
            if choice == "🔧 自定义输入...":
                custom = questionary.text(
                    "请输入:",
                    qmark="",
                ).ask()
                bridge.respond(custom or "")
            else:
                bridge.respond(choice or "")
        else:
            logger.warning("UIBridge 未知 action: %s", bridge.action)
            bridge.respond("")

    def run(self) -> None:
        """启动对话循环。

        外层循环：等用户输入。
        内层循环：agent loop，阻塞用户输入，按 ResponseType 分支：
          - FINISH   → 渲染，回外层
          - PROGRESS → 渲染，自动 CONTINUE
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

            if user_input == "/help":
                self._console.print()
                for cmd, desc in self._COMMAND_HELP.items():
                    self._console.print(f"  [bold]{cmd}[/] — [dim]{desc}[/]")
                self._console.print()
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

            if user_input == "/dump":
                result = self._handler.dump_history()
                if result:
                    self._console.print(f"[dim]history dumped: {result}[/]")
                else:
                    self._console.print("[red]dump failed, see log for details[/]")
                continue

            if user_input == "/restore" or user_input.startswith("/restore "):
                arg = user_input[9:].strip()
                if arg:
                    self._do_restore(arg)
                else:
                    self._restore_interactive()
                continue

            if user_input == "/auto-approve-switch" or user_input.startswith("/auto-approve-switch "):
                arg = user_input[22:].strip()
                if arg == "on":
                    config.TOOL_CONFIRM_ENABLED = True
                elif arg == "off":
                    config.TOOL_CONFIRM_ENABLED = False
                else:
                    config.TOOL_CONFIRM_ENABLED = not config.TOOL_CONFIRM_ENABLED
                state = "ON" if config.TOOL_CONFIRM_ENABLED else "OFF"
                self._console.print(f"[dim]工具审批: {state} (TOOL_CONFIRM_ENABLED={config.TOOL_CONFIRM_ENABLED})[/]")
                self._console.print()
                continue

            if user_input == "/exit_sub":
                if self._handler is self._main_agent:
                    self._console.print("[red]当前已是主Agent，/exit_sub 仅在子Agent会话中可用[/]")
                    continue
                self._handler._history.append(
                    Message(
                        role=Role.USER,
                        event_type=EventType.SYSTEM_MESSAGE,
                        message="用户请求主动退出当前会话。请整理本次会话的关键信息和结论，然后调用 switch_to_mainagent 退出。",
                    )
                )
                request = Request(type=RequestType.CONTINUE)

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
            bridge = UIBridge()
            while True:
                response = self._process_with_spinner(request, bridge)

                logger.debug(
                    "App response — type=%s switch=%s msg_len=%d plan_items=%d",
                    response.type,
                    response.switch_agent or "-",
                    len(response.message or ""),
                    len(response.plan) if response.plan else 0,
                )

                if response.type == ResponseType.FINISH:
                    # ═══ auto-save: 保存当前 handler 的对话历史 ═══
                    self._auto_save()

                    if response.switch_agent:
                        old_agent_key = self._handler._get_agent_key()

                        if response.switch_agent != MAIN_AGENT_KEY:
                            # main → sub: 保存 tool_call_id 用于后续闭环
                            if response.switch_tool_call_id:
                                self._switch_tool_call_id = response.switch_tool_call_id
                        else:
                            # sub → main: 向 main 注入 tool_call_result
                            if self._switch_tool_call_id:
                                self._main_agent._history.append(
                                    Message(
                                        role=Role.USER,
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

                        # sub → main: 保存 main 注入后的状态，延迟删除 sub 存档
                        if response.switch_agent == MAIN_AGENT_KEY and old_agent_key != MAIN_AGENT_KEY:
                            self._auto_save()
                            self._save_mgr.schedule_sub_cleanup(old_agent_key)

                        context = response.switch_context or "请开始处理。"
                        request = Request(
                            type=RequestType.USER_INPUT,
                            message=context,
                        )
                        continue

                    # 正常 FINISH：渲染并回外层
                    self._console.print()
                    self._render_plan(response.plan)
                    if config.SHOW_THINKING and response.thinking:
                        self._console.print(Panel(response.thinking, title="思考", border_style="dim"))
                    msg = response.message or ""
                    if msg:
                        self._console.print(Markdown(msg))
                    self._console.print()
                    break

                if response.type == ResponseType.PROGRESS:
                    self._console.print()
                    self._render_plan(response.plan)
                    if response.message:
                        self._console.print(f"[dim]🔄 {response.message}[/]")
                    request = Request(type=RequestType.CONTINUE)
                    continue

    def _plan_panel(self, plan_items: list) -> Panel | None:
        """构建计划进度 Panel，plan 为空或全部完成时返回 None。"""
        if not plan_items:
            return None
        # 无进行中或待执行项 → plan 已结束，不显示
        has_active = any(
            item.status.value in ("pending", "in_progress")
            for item in plan_items
        )
        if not has_active:
            return None

        STATUS_ICONS: dict[str, str] = {
            "pending": "[ ]",
            "in_progress": "[>]",
            "completed": "[x]",
            "cancelled": "[~]",
        }

        lines: list[str] = []
        for item in sorted(plan_items, key=lambda x: x.order):
            icon = STATUS_ICONS.get(item.status.value, "?")
            lines.append(f"{icon} {item.description}")

        body = Text("\n".join(lines))
        return Panel(body, title="[ Execution Plan ]", border_style="dim")

    def _render_plan(self, plan_items: list) -> None:
        """打印计划进度面板到终端。"""
        panel = self._plan_panel(plan_items)
        if panel:
            self._console.print(panel)

    def _print_welcome(self) -> None:
        self._console.print()
        self._console.print(
            Panel.fit("[bold green]get-me-in[/] — AI 求职助手")
        )
        self._console.print("[dim]输入 /help 查看所有命令[/]")
        self._console.print()
