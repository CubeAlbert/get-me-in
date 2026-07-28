"""记忆与参考资料查询工具的 v2 定义。"""

from collections.abc import Mapping
from enum import StrEnum
from typing import Protocol

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolFailure, ToolHandlerContext, ToolParameter, ToolPolicy, ToolSchema, ToolSuccess
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
            name="query_memory",
            purpose="语义检索用户记忆库，返回匹配的记忆条目（事实和偏好）。",
            use_when="需要查询用户之前存储的个人信息时，如技能、经历、偏好、期望等",
            do_not_use_when="需要查询公共参考数据时；本工具只查询用户个人记忆",
            expected_output='{"query": "...", "total_results": N, "results": [{"content": "...", "metadata": {...}}]}',
            schema=ToolSchema(
                {
                    "query": ToolParameter(
                        str,
                        "自然语言查询，如 'Python 开发经验'、'期望薪资'",
                    ),
                    "memory_type": ToolParameter(
                        str,
                        "记忆类型过滤；不填则搜索全部",
                        default=None,
                        allowed_values=tuple(item.value for item in MemoryType),
                        nullable=True,
                    ),
                    "top_k": ToolParameter(
                        int,
                        "返回结果数量，默认 5",
                        default=5,
                    ),
                },
                frozenset({"query"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.MEMORY_QUERY}),
                ConfirmationMode.NEVER,
            ),
            handler=_query_memory,
        ),
        ToolDefinition(
            name="query_reference_data",
            purpose="语义检索参考数据库，返回匹配的公共参考内容（技术知识、面试题、公司信息等）。",
            use_when="需要查询面试题、技术知识点、公司信息、简历示例、推荐资料等",
            do_not_use_when="需要查询用户个人记忆时 — 用 query_memory",
            expected_output='{"query": "...", "total_results": N, "results": [{"content": "...", "metadata": {...}}]}',
            schema=ToolSchema(
                {
                    "query": ToolParameter(
                        str,
                        "自然语言查询，如 '快速排序'、'阿里巴巴 Java 面试题'",
                    ),
                    "category": ToolParameter(
                        str,
                        "参考数据分类过滤；不填则搜索全部",
                        default=None,
                        allowed_values=tuple(
                            item.value for item in ReferenceCategory
                        ),
                        nullable=True,
                    ),
                    "top_k": ToolParameter(
                        int,
                        "返回结果数量，默认 5",
                        default=5,
                    ),
                },
                frozenset({"query"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.KNOWLEDGE_QUERY}),
                ConfirmationMode.NEVER,
            ),
            handler=_query_reference_data,
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
