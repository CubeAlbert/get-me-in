"""Explicit web-search tool definition."""

from collections.abc import Mapping
from typing import Protocol

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolParameter, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.web_search import WebSearchPort


class WebToolContext(ToolHandlerContext, Protocol):
    web_search: WebSearchPort | None
    cancellation: object


def build_web_tools() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition(
            name="web_search",
            purpose="搜索网络获取信息，返回整理后的结果。搜索结果是即时的，不依赖模型训练数据。",
            use_when="需要获取最新信息、实时数据、新闻事件，或模型训练数据中可能不存在的内容时；注意当你需要知道当前日期时，请使用日期时间工具先获取日期时间。",
            do_not_use_when="问题可以通过常识或模型已有知识回答时，优先使用已有知识",
            expected_output="基于搜索结果整理的回答，包含具体信息和参考来源（如有）",
            schema=ToolSchema(
                {"query": ToolParameter(str, "搜索查询，使用自然语言或关键词")},
                frozenset({"query"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.WEB_SEARCH}),
                ConfirmationMode.ALWAYS,
            ),
            handler=_search,
        ),
    )


def _search(arguments: Mapping[str, object], context: WebToolContext) -> ToolSuccess | ToolFailure:
    if context.web_search is None:
        return ToolFailure("web_search_unavailable", "This application has no web-search adapter")
    try:
        return ToolSuccess(context.web_search.search(arguments["query"], context.cancellation))
    except InterruptedError:
        return ToolFailure("web_search_cancelled", "Web search was cancelled")
    except Exception as error:
        return ToolFailure("web_search_failed", str(error))
