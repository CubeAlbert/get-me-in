"""临时 v2 Runtime 终端 smoke runner；R5 CLI 落地后删除。"""

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

import questionary
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from src.get_me_in.application.application import Application
from src.get_me_in.application.commands import (
    Approve,
    Cancel,
    Continue,
    Reject,
    RuntimeCommand,
    SubmitSelection,
    UserMessage,
)
from src.get_me_in.application.events import (
    ApprovalRequested,
    Cancelled,
    Completed,
    Failed,
    HandoffRequested,
    Progress,
    RuntimeEvent,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.settings import Settings, SettingsValidationError
from src.get_me_in.bootstrap import build_application


console = Console()
_CUSTOM_CHOICE = "［自定义输入］"


def load_settings() -> Settings:
    """从项目根目录的 .env 构造 v2 Settings。"""
    return Settings.from_env(os.environ, project_root=PROJECT_ROOT)


def render_event(event: RuntimeEvent) -> None:
    """以最小终端样式显示一个 RuntimeEvent。"""
    if isinstance(event, Progress):
        console.print(f"[dim]… {event.message}[/dim]")
    elif isinstance(event, ToolStarted):
        console.print(f"[cyan]→ 工具调用[/cyan] {event.tool_name} [dim]({event.call_id})[/dim]")
    elif isinstance(event, ToolFinished):
        console.print(f"[cyan]← 工具完成[/cyan] {event.tool_name}")
        console.print(event.output)
    elif isinstance(event, ApprovalRequested):
        console.print(f"[yellow]需要审批：[/yellow] {event.summary}")
    elif isinstance(event, SelectionRequested):
        console.print(f"[yellow]需要选择：[/yellow] {event.prompt}")
    elif isinstance(event, HandoffRequested):
        console.print(
            f"[yellow]收到 HandoffRequested：[/yellow] "
            f"{event.source.value} → {event.target.value} [dim]({event.call_id})[/dim]"
        )
        if event.context:
            console.print(event.context)
        console.print("[dim]R4 Orchestrator 尚未实现，本次 smoke 将取消并闭合该 handoff。[/dim]")
    elif isinstance(event, Completed):
        console.print(Markdown(event.message.content))
    elif isinstance(event, Failed):
        console.print(f"[bold red]运行失败 [{event.code}]：[/bold red] {event.message}")
    elif isinstance(event, Cancelled):
        console.print(f"[yellow]已取消：[/yellow] {event.reason}")


def collect_command(event: RuntimeEvent) -> RuntimeCommand | None:
    """把可继续或需要交互的事件转换为下一条 RuntimeCommand。"""
    if isinstance(event, (Progress, ToolStarted, ToolFinished)):
        return Continue()
    if isinstance(event, ApprovalRequested):
        approved = questionary.confirm(event.summary, default=False).ask()
        return Approve(event.call_id) if approved else Reject(event.call_id, "用户在 smoke runner 中拒绝")
    if isinstance(event, SelectionRequested):
        selected = questionary.select(
            event.prompt,
            choices=(*event.choices, _CUSTOM_CHOICE),
        ).ask()
        if selected is None:
            return Cancel("用户取消选择")
        if selected == _CUSTOM_CHOICE:
            selected = Prompt.ask("请输入自定义内容")
        return SubmitSelection(event.request_id, selected)
    if isinstance(event, HandoffRequested):
        return Cancel("R4 Orchestrator 尚未实现")
    return None


def _invoke(
    application: Application,
    executor: ThreadPoolExecutor,
    command: RuntimeCommand,
) -> RuntimeEvent:
    future: Future[RuntimeEvent] = executor.submit(application.handle, command)
    cancel_requested = False
    while True:
        try:
            return future.result(timeout=0.1)
        except FutureTimeout:
            continue
        except KeyboardInterrupt:
            if not cancel_requested:
                cancel_requested = True
                console.print("\n[yellow]正在请求取消活动调用…[/yellow]")
                application.request_cancel("用户按下 Ctrl+C")
            else:
                console.print("[dim]取消请求已发送，正在等待 adapter 释放资源…[/dim]")


def _drive(
    application: Application,
    executor: ThreadPoolExecutor,
    command: RuntimeCommand,
) -> None:
    while True:
        event = _invoke(application, executor, command)
        render_event(event)
        command = collect_command(event)
        if command is None:
            return


def run_event_loop(application: Application) -> None:
    """运行临时外层输入循环，并自动推进 v2 单步 Runtime。"""
    console.print("[bold]get-me-in v2 Runtime smoke[/bold]")
    console.print("输入 [cyan]/exit[/cyan] 退出；阻塞调用期间按 [cyan]Ctrl+C[/cyan] 请求取消。")
    console.print("[dim]Session、RAG、Resume handoff 与正式 CLI 命令尚不在本 runner 范围内。[/dim]\n")
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="v2-smoke") as executor:
        while True:
            try:
                text = Prompt.ask("[bold green]你[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]退出 smoke runner。[/dim]")
                return
            if not text:
                continue
            if text == "/exit":
                return
            _drive(application, executor, UserMessage(text))


def main() -> None:
    """构造隔离的 v2 Application 并启动临时终端 smoke。"""
    try:
        settings = load_settings()
    except SettingsValidationError as error:
        console.print(f"[bold red]配置错误：[/bold red] {error}")
        console.print("请检查项目根目录的 .env，然后重试。")
        raise SystemExit(2) from error

    application = build_application(settings)
    try:
        run_event_loop(application)
    finally:
        application.close()


if __name__ == "__main__":
    main()
