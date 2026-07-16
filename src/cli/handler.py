"""Handler 协议 — CLI 层与业务逻辑层之间的桥接接口。

CLI 不直接调用 LLM 或 Agent，而是调用注入的 Handler。
Handler 负责具体的输入处理逻辑，CLI 只负责 I/O 和渲染。
"""

from abc import ABC, abstractmethod

from src.message import Message
from src.request import Request
from src.response import Response


class Handler(ABC):
    """处理用户输入的抽象协议。

    所有业务逻辑入口（Agent、编排器等）均实现此接口，
    CLI 层只依赖 Handler，不感知具体实现。
    """

    @abstractmethod
    def process(self, input: Request) -> Response:
        """处理输入，返回 CLI 指令。

        Args:
            input: App → Agent 请求（用户输入 / 自动继续 / 审批确认）。

        Returns:
            CLI 指令，告诉 App 如何渲染本轮结果。
        """
        ...

    @staticmethod
    def _parse_llm_reply(reply: str) -> Message:
        """将 LLM 返回的 JSON 反序列化为 ``Message``。

        委托给 ``Message.from_llm_reply``。
        """
        return Message.from_llm_reply(reply)
