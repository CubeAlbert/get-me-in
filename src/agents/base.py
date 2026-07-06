"""BaseAgent — Agent 基类，所有 Agent 的公共能力。

子类必须实现 14 个 ``_get_*`` 抽象方法（13 个占位符 + 1 个 agent_name），
遗漏任何一个 Python 会在 import 时报 ``TypeError``，防止漏填提示词。
"""

import dataclasses
import json

from abc import abstractmethod

from src.cli.handler import Handler
from src.config import config
from src.llm.client import LLMClient
from src.logger import get_logger
from src.message import Message
from src.prompts.loader import PromptLoader
from src.response import Response, ResponseType
from src.tools.registry import ConfirmMode, Tool, ToolRegistry

logger = get_logger(__name__)

# 硬编码在 04_tools.md 中，不走 ToolRegistry 但 agent loop 需要识别
_TERMINAL_TOOLS = frozenset({"finish", "ask_user", "return"})


class BaseAgent(Handler):
    """Agent 基类 — 提供 agent loop、工具调度、对话管理、记忆写入。

    子类按需覆盖 ``_pro_params`` / ``_flash_params``（LLM 参数默认值）。
    """

    _pro_params: dict = {}
    _flash_params: dict = {}

    # ── 14 个抽象方法：子类必须全部实现 ──────────────────────

    @abstractmethod
    def _get_agent_name(self) -> str:
        """Agent 标识名，用于工具过滤、记忆归属。"""
        ...

    @abstractmethod
    def _get_agent_description(self) -> str:
        """→ AGENT_DESCRIPTION"""
        ...

    @abstractmethod
    def _get_responsibilities(self) -> str:
        """→ RESPONSIBILITIES"""
        ...

    @abstractmethod
    def _get_primary_goal(self) -> str:
        """→ PRIMARY_GOAL"""
        ...

    @abstractmethod
    def _get_success_criterions(self) -> str:
        """→ SUCCESS_CRITERIONS"""
        ...

    @abstractmethod
    def _get_priorities(self) -> str:
        """→ PRIORITIES"""
        ...

    @abstractmethod
    def _get_hard_constraints(self) -> str:
        """→ HARD_CONSTRAINTS"""
        ...

    @abstractmethod
    def _get_soft_constraints(self) -> str:
        """→ SOFT_CONSTRAINTS"""
        ...

    @abstractmethod
    def _get_tone(self) -> str:
        """→ TONE"""
        ...

    @abstractmethod
    def _get_verbosity(self) -> str:
        """→ VERBOSITY"""
        ...

    @abstractmethod
    def _get_explanation_style(self) -> str:
        """→ EXPLANATION_STYLE"""
        ...

    @abstractmethod
    def _get_style_rules(self) -> str:
        """→ STYLE_RULES"""
        ...

    @abstractmethod
    def _get_style_avoids(self) -> str:
        """→ STYLE_AVOIDS"""
        ...

    # ── init ──────────────────────────────────────────────

    def __init__(
        self,
        llm: LLMClient,
        prompts: PromptLoader,
        extra_tools: list[Tool] | None = None,
    ) -> None:
        name = self._get_agent_name()

        # 从 ToolRegistry 按 agent 过滤拉取工具
        self._tools = ToolRegistry.get_for(name)
        if extra_tools:
            for t in extra_tools:
                self._tools[t.name] = t

        # 组装所有占位符值
        tools_xml = "\n".join(t.to_xml() for t in self._tools.values())
        placeholders = {
            "AGENT_NAME": name,
            "AGENT_DESCRIPTION": self._get_agent_description(),
            "RESPONSIBILITIES": self._get_responsibilities(),
            "PRIMARY_GOAL": self._get_primary_goal(),
            "SUCCESS_CRITERIONS": self._get_success_criterions(),
            "PRIORITIES": self._get_priorities(),
            "HARD_CONSTRAINTS": self._get_hard_constraints(),
            "SOFT_CONSTRAINTS": self._get_soft_constraints(),
            "ADDITION_TOOLS": tools_xml,
            "TONE": self._get_tone(),
            "VERBOSITY": self._get_verbosity(),
            "EXPLANATION_STYLE": self._get_explanation_style(),
            "STYLE_RULES": self._get_style_rules(),
            "STYLE_AVOIDS": self._get_style_avoids(),
        }
        system_prompt = prompts.get(**placeholders)

        self._llm = llm
        self._output_format = prompts.get_raw("general_agent/06_output_format")
        self._history: list[Message] = [
            Message(role="system", message=system_prompt, event_type="system_prompt")
        ]
        self._max_rounds = int(config.AGENT_MAX_ROUNDS)

        logger.debug(
            "%s 初始化 — %d 个工具, max_rounds=%d",
            name,
            len(self._tools),
            self._max_rounds,
        )

    # ── process — agent loop ──────────────────────────────

    def _to_openai(self) -> list[dict]:
        """将 ``_history`` 转换为 OpenAI API 格式。

        每个 Message 完整序列化为 JSON，结构不变 → LLM 缓存命中。
        """
        return [
            {"role": m.role, "content": json.dumps(dataclasses.asdict(m))}
            for m in self._history
        ]

    def _execute_tool(self, tool_name: str, payload: dict) -> Message:
        """执行工具并返回结果 Message。

        异常时记 error 日志刷到 stderr，同时包装为 tool_call_result 喂回 LLM。
        """
        tool = self._tools[tool_name]
        try:
            return tool.handler(**payload)
        except Exception as e:
            logger.error("工具 %s 执行失败: %s", tool_name, e)
            return Message(
                role="user",
                event_type="tool_call_result",
                message=f"[Error] {tool_name} 执行失败：{e}",
            )

    def _should_confirm(self, tool: Tool) -> bool:
        """判断工具是否需要审批。不暴露给 LLM。"""
        if tool.confirm_mode == ConfirmMode.NEVER:
            return False
        if tool.confirm_mode == ConfirmMode.ALWAYS:
            return True
        return bool(config.TOOL_CONFIRM_ENABLED)

    def process(self, input: Message) -> Response:
        """Agent 主循环。

        用户输入 → LLM 推理 → 解析 JSON → 调工具/返回结果 → 循环，
        正常退出由 LLM 调 ``finish`` / ``ask_user`` / ``return`` 触发。
        达到 ``_max_rounds`` 仍未返回终止工具时安全阀强制结束。
        """
        self._history.append(
            Message(
                role="user",
                message=input.message,
                event_type=input.event_type or "user_input",
            )
        )

        for round_idx in range(self._max_rounds):
            reply = self._llm.chat_pro(self._to_openai(), **self._pro_params)

            # JSON 解析，失败时注入 output_format 让 LLM 自修复
            try:
                llm_msg = self._parse_llm_reply(reply)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("JSON 解析失败 (round %d): %s", round_idx + 1, e)
                self._history.append(
                    Message(
                        role="user",
                        event_type="json_format_reminder",
                        message=self._output_format,
                    )
                )
                continue

            self._history.append(llm_msg)

            # ── 工具调度 (7a–7d) ──
            # 7a. tool_name ∈ {finish, ask_user, return} → return Response(type=ResponseType.FINISH)
            # 7b. tool_name 已注册 + 需审批 → return Response(type=ResponseType.CONFIRM)
            # 7c. tool_name 已注册 + 无需审批 → 执行 → _history <tool_call_result> → continue
            # 7d. tool_name 未知 → _history <system_error> → LLM 下轮自修正
            _ = llm_msg  # 临时占位

        # 安全阀 — 循环跑完未正常退出
        logger.warning("%s 达到最大轮数 %d，强制终止", self._get_agent_name(), self._max_rounds)
        return Response(
            type=ResponseType.FINISH,
            message="已达到最大工具调用轮数，流程终止。",
        )
