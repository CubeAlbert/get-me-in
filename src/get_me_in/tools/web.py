"""Explicit web-search tool definition."""

from collections.abc import Mapping
from typing import Protocol

from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.web_search import WebSearchPort


class WebToolContext(ToolHandlerContext, Protocol):
    web_search: WebSearchPort | None
    cancellation: object


def build_web_tools() -> tuple[ToolDefinition, ...]:
    return (ToolDefinition("web_search", "搜索网络中的最新信息并返回整理结果。", ToolSchema({"query": str}, frozenset({"query"})), ToolPolicy(confirmation=ConfirmationMode.ALWAYS), _search),)


def _search(arguments: Mapping[str, object], context: WebToolContext) -> ToolSuccess | ToolFailure:
    if context.web_search is None:
        return ToolFailure("web_search_unavailable", "This application has no web-search adapter")
    try:
        return ToolSuccess(context.web_search.search(arguments["query"], context.cancellation))
    except InterruptedError:
        return ToolFailure("web_search_cancelled", "Web search was cancelled")
    except Exception as error:
        return ToolFailure("web_search_failed", str(error))
