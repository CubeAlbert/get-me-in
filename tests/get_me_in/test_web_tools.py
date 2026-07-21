"""Tests for the provider-neutral web search tool."""

import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolSuccess
from src.get_me_in.tools.web import build_web_tools


class WebToolTests(unittest.TestCase):
    def test_search_uses_injected_adapter_after_approval(self) -> None:
        adapter = _Search()
        executor = ToolExecutor(ToolCatalog(build_web_tools()))
        context = ToolContext("session", AgentKey.MAIN, CancellationToken(), web_search=adapter, approved=True)

        outcome = executor.execute("call", "web_search", {"query": "latest"}, context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual("result: latest", outcome.output)


class _Search:
    def search(self, query: str, cancellation: CancellationToken) -> str:
        return f"result: {query}"

    def close(self) -> None:
        pass
