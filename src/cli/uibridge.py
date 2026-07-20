"""UIBridge — 工具 handler 与 CLI 前端的跨线程通信桥。

工具 handler 运行在后台线程中，通过 UIBridge 与主线程（持有 questionary/Console）
交互。handler 调用 ``select()`` / ``confirm()`` 会阻塞等待用户响应，
主线程在 spinner 循环中轮询 bridge 并渲染 UI。

用法::

    # 在工具 handler 中
    from src.cli.uibridge import get_bridge

    def my_tool(prompt: str) -> dict:
        ui = get_bridge()
        if ui.confirm(f"是否执行: {prompt}?"):
            return {"result": "executed"}
        return {"rejected": True}
"""

from __future__ import annotations

import threading

from src.logger import get_logger

logger = get_logger(__name__)

# ── 模块级 bridge 存取 ──────────────────────────────────────────

_current_bridge: UIBridge | None = None


def _set_bridge(bridge: UIBridge | None) -> None:
    """设置当前线程可用的 UIBridge（由 BaseAgent._execute_tool 调用）。"""
    global _current_bridge
    _current_bridge = bridge


def get_bridge() -> UIBridge:
    """获取当前 UIBridge 实例，只能在工具 handler 中调用。"""
    if _current_bridge is None:
        raise RuntimeError("get_bridge() 只能在工具 handler 中调用")
    return _current_bridge


# ── 模块级 cancel 标志 ──────────────────────────────────────────

_cancel_event: threading.Event = threading.Event()


def _set_cancel() -> None:
    """主线程：设置取消标志，通知后台线程停止处理。"""
    _cancel_event.set()


def _clear_cancel() -> None:
    """主线程：清除取消标志（每次新请求开始时调用）。"""
    _cancel_event.clear()


def is_cancelled() -> bool:
    """任意线程：检查是否已被主线程请求取消。"""
    return _cancel_event.is_set()


# ── UIBridge ────────────────────────────────────────────────────


class UIBridge:
    """工具 handler ↔ CLI 前端跨线程通信桥。

    工具 handler（后台线程）调用交互方法 → 阻塞等待；
    主线程轮询 ``has_request`` → 渲染 questionary → 调用 ``respond()`` 传回结果。
    """

    def __init__(self) -> None:
        self._request_ready = threading.Event()  # handler → main: 请求就绪
        self._response_ready = threading.Event()  # main → handler: 响应就绪
        self._action: str = ""
        self._question: str = ""
        self._choices: list[str] = []
        self._result: str | bool = ""

    # ── Tool Handler 端（后台线程）──────────────────────────

    def select(self, question: str, choices: list[str]) -> str:
        """弹出选项列表让用户选择，阻塞直到用户选中，返回选项文本。

        Args:
            question: 提示问题。
            choices: 选项列表，最后一项自动追加 "🔧 自定义输入..."。

        Returns:
            用户选中的选项文本。
        """
        self._action = "select"
        self._question = question
        self._choices = list(choices)
        self._request_ready.set()
        self._response_ready.wait()
        self._response_ready.clear()
        return str(self._result)

    def confirm(self, message: str) -> bool:
        """弹出确认对话框，阻塞直到用户选择。

        Args:
            message: 确认提示信息。

        Returns:
            True 表示用户确认，False 表示取消。
        """
        self._action = "confirm"
        self._question = message
        self._choices = []
        self._request_ready.set()
        self._response_ready.wait()
        self._response_ready.clear()
        return bool(self._result)

    # ── App 端（主线程）──────────────────────────────────────

    @property
    def has_request(self) -> bool:
        """主线程：是否有待处理的 UI 请求。"""
        return self._request_ready.is_set()

    @property
    def action(self) -> str:
        """主线程：当前请求类型（``"select"`` / ``"confirm"``）。"""
        return self._action

    @property
    def question(self) -> str:
        """主线程：提示文本。"""
        return self._question

    @property
    def choices(self) -> list[str]:
        """主线程：选项列表（仅 ``action="select"`` 时有效）。"""
        return self._choices

    def respond(self, result: str | bool) -> None:
        """主线程：设置用户响应并唤醒 handler 线程。

        Args:
            result: 用户的响应（select → str, confirm → bool）。
        """
        self._result = result
        self._request_ready.clear()
        self._response_ready.set()
