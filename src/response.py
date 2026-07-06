"""CLI 指令层数据类 — Agent 通过 Response 向 App 下达渲染指令，不进对话历史。

用法:
    from src.response import Response

    # 正常结束
    Response(type="finish", message="任务完成")

    # 让用户选择
    Response(type="select", message="请选择", choices=["选项A", "选项B"])

    # 请求审批
    Response(type="confirm", message="即将执行删除操作")
"""

from dataclasses import dataclass


@dataclass
class Response:
    """Agent → CLI 指令，告诉 App 如何渲染本轮结果。

    ``Response`` 是 CLI 指令层，**不进对话历史**。
    三种 type 对应不同 App 行为：

    - ``"finish"`` — 渲染 markdown，本轮结束
    - ``"select"`` — 渲染 questionary.select（最后一项固定"自定义输入"），用户选择包装为 Message 继续 agent loop
    - ``"confirm"`` — 渲染 questionary.confirm，y → 执行工具，n → 跳过

    Attributes:
        type: 指令类型：``"finish"`` / ``"select"`` / ``"confirm"``。
        message: 展示文本 (markdown)。
        choices: ``type="select"`` 时的选项列表，最后一项自动追加"🔧 自定义输入..."。
        thinking: LLM 推理过程，由 ``SHOW_THINKING`` 环境变量控制是否渲染。默认 ``None``。
    """

    type: str
    message: str
    choices: list[str] | None = None
    thinking: str | None = None
