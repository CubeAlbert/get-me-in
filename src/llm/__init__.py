"""LLM 模块入口 — 单例管理。

用法:
    from src.llm import get_client

    client = get_client()
    reply = client.chat_pro([{"role": "user", "content": "分析这份简历..."}])
    reply = client.chat_flash([{"role": "user", "content": "分类: ..."}])
    result = client.web_search("如何安装 Java")
"""

import threading

from src.llm.client import LLMClient

_client: LLMClient | None = None
_lock = threading.Lock()


def get_client() -> LLMClient:
    """返回 LLMClient 线程安全单例。"""
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                _client = LLMClient()
    return _client


__all__ = ["LLMClient", "get_client"]
