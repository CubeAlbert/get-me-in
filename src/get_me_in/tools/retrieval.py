"""记忆与参考资料查询工具的 v2 定义。"""

from collections.abc import Mapping
from enum import StrEnum
from typing import Protocol

from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.retrieval import RetrievalPort


class MemoryType(StrEnum):
    FACT = "fact"
    PREFERENCE = "preference"


class ReferenceCategory(StrEnum):
    COMPANY_INFO = "company_info"
    INTERVIEW_QUESTIONS = "interview_questions"
    JOB_DESCRIPTIONS = "job_descriptions"
    KNOWLEDGE_BASE = "knowledge_base"
    RECOMMENDED_MATERIALS = "recommended_materials"
    RESUME_EXAMPLES = "resume_examples"


class RetrievalToolContext(ToolHandlerContext, Protocol):
    retrieval: RetrievalPort | None
    cancellation: object


def build_retrieval_tools() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition(
            "query_memory", "查询已保存的用户事实或偏好。",
            ToolSchema({"query": str, "memory_type": str, "top_k": int}, frozenset({"query"})),
            ToolPolicy(confirmation=ConfirmationMode.NEVER), _query_memory,
        ),
        ToolDefinition(
            "query_reference_data", "查询已导入的求职参考资料。",
            ToolSchema({"query": str, "category": str, "top_k": int}, frozenset({"query"})),
            ToolPolicy(confirmation=ConfirmationMode.NEVER), _query_reference_data,
        ),
    )


def _query_memory(arguments: Mapping[str, object], context: RetrievalToolContext) -> ToolSuccess | ToolFailure:
    category = arguments.get("memory_type")
    if category is not None and category not in MemoryType:
        return ToolFailure("invalid_memory_type", f"Unsupported memory type: {category}")
    return _search(arguments, context, collection="memories", category=category)


def _query_reference_data(arguments: Mapping[str, object], context: RetrievalToolContext) -> ToolSuccess | ToolFailure:
    category = arguments.get("category")
    if category is not None and category not in ReferenceCategory:
        return ToolFailure("invalid_reference_category", f"Unsupported reference category: {category}")
    return _search(arguments, context, collection="references", category=category)


def _search(
    arguments: Mapping[str, object], context: RetrievalToolContext, *, collection: str, category: object | None,
) -> ToolSuccess | ToolFailure:
    if context.retrieval is None:
        return ToolFailure("retrieval_unavailable", "This application has no retrieval adapter")
    top_k = arguments.get("top_k", 5)
    if top_k < 1:
        return ToolFailure("invalid_top_k", "top_k must be at least 1")
    try:
        results = context.retrieval.search(
            arguments["query"], collection=collection, category=category, top_k=top_k, cancellation=context.cancellation,
        )
    except InterruptedError:
        return ToolFailure("retrieval_cancelled", "Retrieval was cancelled")
    except Exception as error:
        return ToolFailure("retrieval_unavailable", str(error))
    items = tuple(
        {"content": result.content, "metadata": {key: value for key, value in result.metadata.items() if key != "rerank_score"}}
        for result in results
    )
    return ToolSuccess({"query": arguments["query"], "total_results": len(items), "results": items})
