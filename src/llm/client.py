"""LLM 调用封装 — 双 tier（pro / flash）统一调用 + web_search。

用法:
    from src.llm import LLMClient

    client = LLMClient()
    reply = client.chat_pro([{"role": "user", "content": "分析这份简历..."}])
    reply = client.chat_flash([{"role": "user", "content": "分类: ..."}])
    result = client.web_search("如何安装 Java")
"""

import json

from openai import OpenAI

from src.config import config
from src.logger import get_logger

logger = get_logger(__name__)

_WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                }
            },
            "required": ["query"],
        },
    },
}

_WEB_SEARCH_SYSTEM = (
    "You are a web search tool. Your only job is to perform a single "
    "web search for the given query and return the results. "
    "Do not engage in conversation, ask follow-up questions, "
    "or mention that you are an AI model. "
    "Just return the search results directly."
)


class LLMClient:
    """LLM 调用客户端，封装 OpenAI SDK，提供双 tier 调用能力。

    - chat_pro():  高能力模型（config.LLM_PRO_MODEL），用于深度推理
    - chat_flash(): 快速模型（config.LLM_FLASH_MODEL），用于轻量分类/格式化
    - web_search(): 通过模型内置搜索能力获取网络信息

    配置从 src.config 模块读取，不直接访问 os.environ。
    调用失败直接抛出异常，不做 fallback。
    """

    def __init__(self) -> None:
        self._client = OpenAI(
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY,
        )

    def chat_pro(self, messages: list[dict], **kwargs) -> str:
        """调用 pro tier 模型，返回回复文本。

        Args:
            messages: OpenAI 格式的消息列表
            **kwargs: 透传给 chat.completions.create（如 temperature、max_tokens）

        Returns:
            模型回复文本
        """
        kwargs.setdefault("model", config.LLM_PRO_MODEL)
        logger.debug("LLM pro 调用: model=%s, messages=%d", kwargs["model"], len(messages))
        response = self._client.chat.completions.create(
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content

    def chat_flash(self, messages: list[dict], **kwargs) -> str:
        """调用 flash tier 模型，返回回复文本。

        Args:
            messages: OpenAI 格式的消息列表
            **kwargs: 透传给 chat.completions.create（如 temperature、max_tokens）

        Returns:
            模型回复文本
        """
        kwargs.setdefault("model", config.LLM_FLASH_MODEL)
        logger.debug("LLM flash 调用: model=%s, messages=%d", kwargs["model"], len(messages))
        response = self._client.chat.completions.create(
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content

    def web_search(self, query: str, **kwargs) -> str:
        """通过模型内置搜索能力查询网络信息，返回 LLM 整理后的结果。

        两轮对话：
        1. 调用模型触发 web_search 工具选择
        2. 将工具调用结果喂回模型，获取整理后的答案

        Args:
            query: 搜索查询
            **kwargs: 透传给 chat.completions.create（如 model、max_tokens）
                      ``model`` 默认使用 config.LLM_PRO_MODEL

        Returns:
            LLM 基于搜索结果整理的回答文本
        """
        model = kwargs.pop("model", config.LLM_PRO_MODEL)
        max_tokens = kwargs.pop("max_tokens", 4096)
        logger.debug("web_search: query=%s", query[:80])

        # Round 1: 触发 web_search 工具调用
        response = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": _WEB_SEARCH_SYSTEM},
                {"role": "user", "content": f"Perform a web search for the query: {query}"},
            ],
            tools=[_WEB_SEARCH_TOOL],
            tool_choice={"type": "function", "function": {"name": "web_search"}},
            extra_body={"thinking": {"type": "disabled"}},
            **kwargs,
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        tool_call = msg.tool_calls[0]

        # Round 2: 喂回 tool_call + tool_result，让模型整理答案
        response2 = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            extra_body={"thinking": {"type": "disabled"}},
            messages=[
                {"role": "system", "content": _WEB_SEARCH_SYSTEM},
                {"role": "user", "content": f"Perform a web search for the query: {query}"},
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Provide the result",
                },
            ],
            **kwargs,
        )

        return response2.choices[0].message.content
