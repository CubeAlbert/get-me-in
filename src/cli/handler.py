"""Handler 协议 — CLI 层与业务逻辑层之间的桥接接口。

CLI 不直接调用 LLM 或 Agent，而是调用注入的 Handler。
Handler 负责具体的输入处理逻辑，CLI 只负责 I/O 和渲染。

M4 阶段 Handler 协议升级为 ``Request → Response``。
"""

from abc import ABC, abstractmethod

from src.llm.client import LLMClient
from src.message import EventType, Message, Role
from src.prompts.loader import PromptLoader
from src.request import Request, RequestType
from src.response import Response, ResponseType


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


class LLMHandler(Handler):
    """M4 过渡阶段 Handler — 调 LLM + 工具执行 loop。

    持有 LLMClient 和 PromptLoader，维护对话历史。
    从 ToolRegistry 拉取已注册工具注入 ADDITION_TOOLS。
    M4 主 Agent 就绪后，本类由 Orchestrator 替换。

    占位符值内联在类常量中 —— M1 用通用助手描述，
    后续各 Agent 实现时各自覆盖 _PLACEHOLDER_VALUES。
    """

    _MAX_TOOL_ROUNDS = 5

    # M1 demo 占位符值（M4 各 Agent 实现时各自定义）
    _PLACEHOLDER_VALUES: dict[str, str] = {
        "AGENT_NAME": "get-me-in 助手",
        "AGENT_DESCRIPTION": "AI 求职助手，帮助程序员完成求职全流程（M4 验证阶段，支持工具调用）",
        "RESPONSIBILITIES": "- 回答用户关于求职的各类问题\n- 在能力范围内提供建议和指导\n- 诚实告知能力的边界\n- 可利用工具查询实时信息",
        "PRIMARY_GOAL": "帮助用户解决求职相关问题，提供有用的信息和建议",
        "SUCCESS_CRITERIONS": "- 用户的问题得到了清晰、有用的回答\n- 回答准确、专业、可操作",
        "PRIORITIES": "1. 准确性 — 不确定时坦诚说明\n2. 可操作性 — 给具体的建议而非泛泛而谈\n3. 简洁 — 不废话",
        "HARD_CONSTRAINTS": "- 严禁编造虚假信息\n- 不确定时必须坦诚说明\n- 不得提供违法或违反平台政策的建议",
        "SOFT_CONSTRAINTS": "- 尽量用中文回答\n- 尽量给出具体可操作的建议\n- 尽量简洁",
        "ADDITION_TOOLS": "",  # 由 __init__ 从 ToolRegistry 填充
        "TONE": "专业、友好、务实",
        "VERBOSITY": "简洁，不啰嗦，问什么答什么",
        "EXPLANATION_STYLE": "直接给出结论和建议，必要时简要说明理由",
        "STYLE_RULES": "- 使用中文\n- 适当使用 Markdown 格式增强可读性\n- 代码和技术术语使用英文原文",
        "STYLE_AVOIDS": "- 避免过度的客套话和寒暄\n- 避免在不确定时强行给出建议\n- 避免长篇大论",
    }

    def __init__(self, llm: LLMClient, prompts: PromptLoader) -> None:
        import src.tools.system_tool  # noqa: F401 — 触发 @tool 注册

        from src.tools.registry import ToolRegistry

        tools_xml = "\n".join(
            t.to_xml()
            for t in ToolRegistry.get_for("main").values()
        )
        placeholders = dict(self._PLACEHOLDER_VALUES)
        placeholders["ADDITION_TOOLS"] = tools_xml

        self._llm = llm
        self._tools = ToolRegistry.get_for("main")
        self._messages: list[dict] = [
            {"role": "system", "content": prompts.get(**placeholders)}
        ]

    def process(self, input: Request) -> Response:
        """调 LLM → 工具执行 loop → 返回最终结果。"""
        self._messages.append({"role": "user", "content": input.message})

        for _ in range(self._MAX_TOOL_ROUNDS):
            reply = self._llm.chat_pro(self._messages)
            self._messages.append({"role": "assistant", "content": reply})

            llm_msg = self._parse_llm_reply(reply)

            # 终止 — LLM 表示无需工具调用
            if llm_msg.event_type == EventType.FINISH:
                return Response(
                    type=ResponseType.FINISH,
                    message=llm_msg.message,
                    thinking=llm_msg.thinking,
                )

            # 工具调用
            tool_name = llm_msg.tool
            if tool_name and tool_name in self._tools:
                tool = self._tools[tool_name]
                try:
                    payload = tool.handler(**llm_msg.event_payload)
                except Exception as e:
                    payload = {"error": str(e)}
                result = Message(
                    role=Role.USER,
                    event_type=EventType.TOOL_CALL_RESULT,
                    tool=tool_name,
                    tool_call_id=llm_msg.id,
                    event_payload=payload,
                )
                self._messages.append({"role": "user", "content": result.to_json()})
                continue

            # 未知 tool — 让 LLM 知道
            self._messages.append(
                {"role": "user", "content": f"未知工具：{tool_name}，请使用已定义的工具或调用 finish。"}
            )

        # 达到最大轮数，强制结束
        return Response(
            type=ResponseType.FINISH,
            message="已达到最大工具调用轮数，流程终止。",
        )
