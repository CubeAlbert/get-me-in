"""Tests for the provider-neutral web search tool."""

import unittest
from types import SimpleNamespace

from src.get_me_in.adapters.openai_web_search import OpenAIWebSearchAdapter
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


class OpenAIWebSearchAdapterTests(unittest.TestCase):
    def test_uses_the_legacy_deepseek_web_search_wire_contract(self) -> None:
        tool_call = SimpleNamespace(
            id="provider-call",
            function=SimpleNamespace(name="web_search", arguments='{"query": "latest"}'),
        )
        client = _OpenAIClient(
            _Response(SimpleNamespace(content="", tool_calls=(tool_call,))),
            _Response(SimpleNamespace(content="source: https://example.test", tool_calls=None)),
        )
        adapter = OpenAIWebSearchAdapter(
            api_key="key", base_url="https://api.deepseek.com", model="deepseek-v4-pro",
            max_tokens=1234, client_factory=lambda: client,
        )

        result = adapter.search("latest", CancellationToken())

        self.assertEqual("source: https://example.test", result)
        self.assertEqual(2, len(client.requests))
        first, second = client.requests
        self.assertEqual(1234, first["max_tokens"])
        self.assertEqual(
            "Perform a web search for the query: latest",
            first["messages"][1]["content"],
        )
        self.assertEqual(first["messages"][:2], second["messages"][:2])
        self.assertEqual(1234, second["max_tokens"])
        self.assertEqual("Provide the result", second["messages"][3]["content"])

    def test_rejects_an_unexecuted_dsml_web_search_call(self) -> None:
        client = _OpenAIClient(
            _Response(SimpleNamespace(content='<｜｜DSML｜｜tool_calls>\n<｜｜DSML｜｜invoke name="web_search">', tool_calls=None)),
        )
        adapter = OpenAIWebSearchAdapter(
            api_key="key", base_url="https://api.deepseek.com", model="deepseek-v4-pro",
            max_tokens=4096, client_factory=lambda: client,
        )

        with self.assertRaisesRegex(RuntimeError, "unexecuted web_search"):
            adapter.search("latest", CancellationToken())


class _Response:
    def __init__(self, message: object) -> None:
        self.choices = (SimpleNamespace(message=message),)


class _OpenAIClient:
    def __init__(self, *responses: _Response) -> None:
        self.chat = SimpleNamespace(completions=self)
        self._responses = list(responses)
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> _Response:
        self.requests.append(kwargs)
        return self._responses.pop(0)

    def close(self) -> None:
        pass


class _Search:
    def search(self, query: str, cancellation: CancellationToken) -> str:
        return f"result: {query}"

    def close(self) -> None:
        pass
