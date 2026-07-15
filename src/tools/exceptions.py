"""工具调用异常 — 统一错误处理，让 LLM 有足够上下文自修复。"""


class ToolCallException(Exception):
    """工具调用预期异常。

    handler 只负责抛业务语义（什么错了 + 怎么修），
    ``_execute_tool()`` 框架层负责从 ``Tool`` 对象填充
    ``arguments_schema`` / ``expected_output`` 等上下文。

    Attributes:
        message: 面向 LLM 的错误描述（必填）。
        suggestion: 修复建议，如 "用 workspace_read 获取准确行号后重试"（可选）。
    """

    def __init__(self, message: str, suggestion: str | None = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)
