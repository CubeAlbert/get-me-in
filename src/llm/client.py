"""LLM 调用封装 — 双 tier（pro / flash）统一调用。

用法:
    from src.llm import LLMClient

    client = LLMClient()
    reply = client.chat_pro([{"role": "user", "content": "分析这份简历..."}])
    reply = client.chat_flash([{"role": "user", "content": "分类: ..."}])
"""

from openai import OpenAI

from src.config import config


class LLMClient:
    """LLM 调用客户端，封装 OpenAI SDK，提供双 tier 调用能力。

    - chat_pro():  高能力模型（config.LLM_PRO_MODEL），用于深度推理
    - chat_flash(): 快速模型（config.LLM_FLASH_MODEL），用于轻量分类/格式化

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
        response = self._client.chat.completions.create(
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content
