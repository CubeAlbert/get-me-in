"""Handler 协议 — CLI 层与业务逻辑层之间的桥接接口。

CLI 不直接调用 LLM 或 Agent，而是调用注入的 Handler。
Handler 负责具体的输入处理逻辑，CLI 只负责 I/O 和渲染。

M1 阶段用 LLMHandler 验证端到端管线（config → LLM → prompts → CLI）；
M4 阶段 Handler 协议升级为 ``Message → Response``，LLMHandler 临时适配新协议。
"""

import json

from abc import ABC, abstractmethod

from src.llm.client import LLMClient
from src.message import Message
from src.prompts.loader import PromptLoader
from src.response import Response


class Handler(ABC):
    """处理用户输入的抽象协议。

    所有业务逻辑入口（Agent、编排器等）均实现此接口，
    CLI 层只依赖 Handler，不感知具体实现。
    """

    @abstractmethod
    def process(self, input: Message) -> Response:
        """处理输入消息，返回 CLI 指令。

        Args:
            input: 输入消息（含用户文本、事件类型等）。

        Returns:
            CLI 指令，告诉 App 如何渲染本轮结果。
        """
        ...

    @staticmethod
    def _parse_llm_reply(reply: str) -> Message:
        """将 LLM 返回的 JSON 反序列化为 ``Message``。

        按 ``06_output_format.md`` schema 解析：
        ``thinking`` → ``Message.thinking``\\，
        ``action.tool`` → ``Message.event_type``\\，
        ``action.message`` → ``Message.message``\\，
        ``action.args`` → ``Message.event_payload``\\，
        ``action.id`` → ``Message.id``。

        Args:
            reply: LLM 返回的原始 JSON 字符串。

        Returns:
            解析后的 Message，``role`` 固定为 ``"assistant"``。
        """
        parsed = json.loads(reply)
        return Message(
            role="assistant",
            id=parsed["action"]["id"],
            message=parsed["action"]["message"],
            event_type=parsed["action"]["tool"],
            event_payload=parsed["action"].get("args", {}),
            thinking=parsed.get("thinking"),
        )


class LLMHandler(Handler):
    """M1 阶段 Handler — 直接调 LLM，无 Agent 逻辑。

    持有 LLMClient 和 PromptLoader，维护对话历史。
    M4 主 Agent 就绪后，本类由 Orchestrator 替换。

    占位符值内联在类常量中 —— M1 用通用助手描述，
    后续各 Agent 实现时各自覆盖 _PLACEHOLDER_VALUES。
    """

    # M1 demo 占位符值（M4 各 Agent 实现时各自定义）
    _PLACEHOLDER_VALUES: dict[str, str] = {
        "AGENT_NAME": "get-me-in 助手",
        "AGENT_DESCRIPTION": "AI 求职助手，帮助程序员完成求职全流程（M1 验证阶段，暂不调度子 Agent，直接回答用户问题）",
        "RESPONSIBILITIES": "- 回答用户关于求职的各类问题\n- 在能力范围内提供建议和指导\n- 诚实告知能力的边界",
        "PRIMARY_GOAL": "帮助用户解决求职相关问题，提供有用的信息和建议",
        "SUCCESS_CRITERIONS": "- 用户的问题得到了清晰、有用的回答\n- 回答准确、专业、可操作",
        "PRIORITIES": "1. 准确性 — 不确定时坦诚说明\n2. 可操作性 — 给具体的建议而非泛泛而谈\n3. 简洁 — 不废话",
        "HARD_CONSTRAINTS": "- 严禁编造虚假信息\n- 不确定时必须坦诚说明\n- 不得提供违法或违反平台政策的建议",
        "SOFT_CONSTRAINTS": "- 尽量用中文回答\n- 尽量给出具体可操作的建议\n- 尽量简洁",
        "ADDITION_TOOLS": "<!-- M1 阶段无额外工具，M4 主 Agent 注入 dispatch_* 工具 -->",
        "TONE": "专业、友好、务实",
        "VERBOSITY": "简洁，不啰嗦，问什么答什么",
        "EXPLANATION_STYLE": "直接给出结论和建议，必要时简要说明理由",
        "STYLE_RULES": "- 使用中文\n- 适当使用 Markdown 格式增强可读性\n- 代码和技术术语使用英文原文",
        "STYLE_AVOIDS": "- 避免过度的客套话和寒暄\n- 避免在不确定时强行给出建议\n- 避免长篇大论",
    }

    def __init__(self, llm: LLMClient, prompts: PromptLoader) -> None:
        self._llm = llm
        self._prompts = prompts

        system_prompt = prompts.get(**self._PLACEHOLDER_VALUES)
        self._messages: list[dict] = [
            {"role": "system", "content": system_prompt}
        ]

    def process(self, input: Message) -> Response:
        """调 LLM 获取回复，维护对话历史。"""
        self._messages.append({"role": "user", "content": input.message})
        reply = self._llm.chat_pro(self._messages)
        self._messages.append({"role": "assistant", "content": reply})

        llm_msg = self._parse_llm_reply(reply)
        return Response(
            type="finish",
            message=llm_msg.message,
            thinking=llm_msg.thinking,
        )
