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
        self.executor = ToolExecutor(
            ToolCatalog(build_retrieval_tools("custom-runtime.log", 5))
        )
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken(), retrieval=self.adapter)

    def test_memory_query_filters_category_and_hides_rerank_score(self) -> None:
        outcome = self.executor.execute("call", "query_memory", {"query": "偏好", "memory_type": "preference"}, self.context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual("memories", self.adapter.collection)
        self.assertEqual("preference", self.adapter.category)
        self.assertEqual(5, self.adapter.top_k)
        self.assertEqual({"source": "test"}, outcome.output["results"][0]["metadata"])

    def test_reference_query_rejects_unknown_category(self) -> None:
        outcome = self.executor.execute("call", "query_reference_data", {"query": "职位", "category": "unknown"}, self.context)

        self.assertEqual(ToolFailure("invalid_argument_value", "Argument category must be one of: 'company_info', 'interview_questions', 'job_descriptions', 'knowledge_base', 'recommended_materials', 'resume_examples'"), outcome)

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

    def test_retrieval_failure_is_logged_before_being_mapped(self) -> None:
        context = ToolContext(
            "session",
            AgentKey.MAIN,
            CancellationToken(),
            retrieval=_FailingRetrieval(),
        )

        with self.assertLogs("src.get_me_in.tools.retrieval", level="ERROR") as captured:
            outcome = self.executor.execute("call", "query_memory", {"query": "偏好"}, context)

        self.assertEqual(ToolFailure("retrieval_unavailable", "backend unavailable"), outcome)
        self.assertIn("retrieval failed: collection=memories", captured.output[0])
        self.assertIn("details were written to custom-runtime.log", captured.output[-1])


class _Retrieval:
    collection: str | None = None
    category: str | None = None
    top_k: int | None = None

    def search(self, query: str, *, collection: str, category: str | None, top_k: int, cancellation: CancellationToken) -> tuple[RetrievalResult, ...]:
        self.collection = collection
        self.category = category
        self.top_k = top_k
        return (RetrievalResult("命中", {"source": "test", "rerank_score": 0.9}),)


class _EmptyRetrieval:
    def search(self, query, *, collection, category, top_k, cancellation):
        return ()


class _FailingRetrieval:
    def search(self, query, *, collection, category, top_k, cancellation):
        raise RuntimeError("backend unavailable")
