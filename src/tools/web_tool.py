"""Web 搜索工具 — 通过 LLM 内置搜索能力查询网络信息。"""

from src.llm.client import LLMClient
from src.tools.registry import tool

_client: LLMClient | None = None


def _get_client() -> LLMClient:
    """懒加载 LLMClient 单例。"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


@tool(
    purpose="搜索网络获取信息，返回整理后的结果。搜索结果是即时的，不依赖模型训练数据。",
    use_when="需要获取最新信息、实时数据、新闻事件，或模型训练数据中可能不存在的内容时；注意当你需要知道当前日期时，请使用日期时间工具先获取日期时间。",
    do_not_use_when="问题可以通过常识或模型已有知识回答时，优先使用已有知识",
    expected_output="基于搜索结果整理的回答，包含具体信息和参考来源（如有）",
    input_schema={
        "query": {"description": "搜索查询，使用自然语言或关键词"},
    },
)
def web_search(query: str) -> str:
    return _get_client().web_search(query)
