"""检索工具保持 v2 端口边界的测试。"""

import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolFailure, ToolSuccess
from src.get_me_in.ports.retrieval import RetrievalResult
from src.get_me_in.tools.retrieval import build_retrieval_tools


class RetrievalToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = _Retrieval()
        self.executor = ToolExecutor(ToolCatalog(build_retrieval_tools()))
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken(), retrieval=self.adapter)

    def test_memory_query_filters_category_and_hides_rerank_score(self) -> None:
        outcome = self.executor.execute("call", "query_memory", {"query": "偏好", "memory_type": "preference"}, self.context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual("memories", self.adapter.collection)
        self.assertEqual("preference", self.adapter.category)
        self.assertEqual({"source": "test"}, outcome.output["results"][0]["metadata"])

    def test_reference_query_rejects_unknown_category(self) -> None:
        outcome = self.executor.execute("call", "query_reference_data", {"query": "职位", "category": "unknown"}, self.context)

        self.assertEqual(ToolFailure("invalid_reference_category", "Unsupported reference category: unknown"), outcome)

    def test_invalid_top_k_is_rejected_before_adapter_call(self) -> None:
        outcome = self.executor.execute("call", "query_memory", {"query": "偏好", "top_k": 0}, self.context)

        self.assertEqual(ToolFailure("invalid_top_k", "top_k must be at least 1"), outcome)

    def test_memory_query_returns_success_with_no_results(self) -> None:
        context = ToolContext(
            "session",
            AgentKey.MAIN,
            CancellationToken(),
            retrieval=_EmptyRetrieval(),
        )

        outcome = self.executor.execute(
            "call",
            "query_memory",
            {"query": "尚未记录的信息"},
            context,
        )

        self.assertEqual(
            ToolSuccess(
                {
                    "query": "尚未记录的信息",
                    "total_results": 0,
                    "results": (),
                }
            ),
            outcome,
        )


class _Retrieval:
    collection: str | None = None
    category: str | None = None

    def search(self, query: str, *, collection: str, category: str | None, top_k: int, cancellation: CancellationToken) -> tuple[RetrievalResult, ...]:
        self.collection = collection
        self.category = category
        return (RetrievalResult("命中", {"source": "test", "rerank_score": 0.9}),)


class _EmptyRetrieval:
    def search(self, query, *, collection, category, top_k, cancellation):
        return ()
