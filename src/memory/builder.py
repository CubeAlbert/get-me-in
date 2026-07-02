"""MemoryBuilder — 调用 LLM 从对话中提取结构化记忆。

加载 ``data/prompts/memory/builder.md`` 作为系统提示词，
将对话序列化为 JSON 送入 flash tier（强制 JSON 模式），
解析返回的 ``{"facts": "<string>", "preferences": "<string>"}``，
为每个非空字段构造 Memory 对象。

用法:
    from src.llm import LLMClient
    from src.memory.builder import MemoryBuilder

    llm = LLMClient()
    builder = MemoryBuilder(llm)
    memories = builder.build(conversation, agent="main")
    for m in memories:
        print(m.category, m.content)
"""

import json
import dataclasses
import time
from datetime import datetime

from src.logger import get_logger
from src.llm.client import LLMClient
from src.message import Message
from src.memory.schemas import Memory
from src.prompts.loader import PromptLoader

logger = get_logger(__name__)


class MemoryBuilder:
    """从对话中提取结构化记忆。

    每次调用 ``build()`` 最多返回 2 条 Memory
    （facts 和 preferences 各一条，空字符串则跳过）。
    """

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self._system_prompt = PromptLoader().get_raw("memory/builder")
        logger.info("MemoryBuilder: 已加载 builder.md 提示词")

    def build(self, conversation: list[Message], agent: str) -> list[Memory]:
        """从对话中提取记忆。

        Args:
            conversation: Message 列表，按时间顺序排列。
            agent: 所属 Agent 名称。

        Returns:
            提取的 Memory 列表（0~2 条）。LLM 返回非法 JSON 时返回空列表。
        """
        conv_json = json.dumps(
            [dataclasses.asdict(m) for m in conversation],
            default=str,
            ensure_ascii=False,
        )
        logger.debug("MemoryBuilder: 序列化完成, size=%d bytes", len(conv_json.encode("utf-8")))

        t0 = time.time()
        try:
            response = self._llm.chat_flash(
                [
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": conv_json},
                ],
                response_format={"type": "json_object"},
            )
        except Exception:
            logger.exception("MemoryBuilder: LLM 调用失败")
            return []

        logger.debug("MemoryBuilder: LLM 耗时 %.1fs", time.time() - t0)

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            logger.error("MemoryBuilder: LLM 输出非法 JSON: %.200s", response)
            return []

        facts_raw = str(data.get("facts", "")).strip()
        prefs_raw = str(data.get("preferences", "")).strip()
        now = datetime.now()

        memories: list[Memory] = []
        if facts_raw:
            items = [line.strip() for line in facts_raw.split("\n") if line.strip()]
            memories.append(Memory(
                content="\n\n---\n\n".join(items),
                category="fact",
                agent=agent,
                time=now,
            ))
        if prefs_raw:
            items = [line.strip() for line in prefs_raw.split("\n") if line.strip()]
            memories.append(Memory(
                content="\n\n---\n\n".join(items),
                category="preference",
                agent=agent,
                time=now,
            ))
        return memories
