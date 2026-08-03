"""记忆与参考资料查询工具定义。"""

from collections.abc import Mapping
from enum import StrEnum
import logging
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


logger = logging.getLogger(__name__)
_FILE_ONLY_LOG = {"_get_me_in_file_only": True}


def build_retrieval_tools(
    log_file_name: str, default_top_k: int
) -> tuple[ToolDefinition, ...]:
    def query_memory(
        arguments: Mapping[str, object], context: RetrievalToolContext
    ) -> ToolSuccess | ToolFailure:
        return _query_memory(
            arguments,
            context,
            log_file_name=log_file_name,
            default_top_k=default_top_k,
        )

    def query_reference_data(
        arguments: Mapping[str, object], context: RetrievalToolContext
    ) -> ToolSuccess | ToolFailure:
        return _query_reference_data(
            arguments,
            context,
            log_file_name=log_file_name,
            default_top_k=default_top_k,
        )

    return (
        ToolDefinition(
            name="query_memory",
            purpose="语义检索用户记忆库，返回匹配的记忆条目（事实和偏好）。",
            use_when=(
                "仅在以下情况使用：用户明确要求查询其已保存的个人背景、技术栈、经历、偏好或期望；"
                "或者完成当前任务必须获得某项个人信息，该信息不在当前对话中，已先向用户询问但仍未获得有效答案，"
                "需要将历史记忆作为最后一次补充尝试。查询必须聚焦于当前明确缺失的信息。"
            ),
            do_not_use_when=(
                "不要为了主动了解用户、补充用户画像、个性化回答、减少普通提问或确认已知信息而调用。"
                "当前对话、文件或工具结果已经提供所需信息时不要调用；尚未先向用户询问时不要调用；"
                "缺失信息只是可选信息、不影响任务继续时不要调用；问候、能力介绍、简单路由或闲聊时不要调用；"
                "用户拒绝提供该信息、要求不要访问记忆或查询公共参考数据时不要调用。"
                "查询无结果后不要更换近义词反复尝试，应回到用户询问。"
            ),
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
                        f"返回结果数量，默认 {default_top_k}",
                        default=default_top_k,
                    ),
                },
                frozenset({"query"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.MEMORY_QUERY}),
                ConfirmationMode.NEVER,
            ),
            handler=query_memory,
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
                        f"返回结果数量，默认 {default_top_k}",
                        default=default_top_k,
                    ),
                },
                frozenset({"query"}),
            ),
            policy=ToolPolicy(
                frozenset({Capability.KNOWLEDGE_QUERY}),
                ConfirmationMode.NEVER,
            ),
            handler=query_reference_data,
        ),
    )


def _query_memory(
    arguments: Mapping[str, object],
    context: RetrievalToolContext,
    *,
    log_file_name: str,
    default_top_k: int,
) -> ToolSuccess | ToolFailure:
    category = arguments.get("memory_type")
    if category is not None and category not in MemoryType:
        return ToolFailure("invalid_memory_type", f"Unsupported memory type: {category}")
    return _search(
        arguments,
        context,
        collection="memories",
        category=category,
        log_file_name=log_file_name,
        default_top_k=default_top_k,
    )


def _query_reference_data(
    arguments: Mapping[str, object],
    context: RetrievalToolContext,
    *,
    log_file_name: str,
    default_top_k: int,
) -> ToolSuccess | ToolFailure:
    category = arguments.get("category")
    if category is not None and category not in ReferenceCategory:
        return ToolFailure("invalid_reference_category", f"Unsupported reference category: {category}")
    return _search(
        arguments,
        context,
        collection="references",
        category=category,
        log_file_name=log_file_name,
        default_top_k=default_top_k,
    )


def _search(
    arguments: Mapping[str, object],
    context: RetrievalToolContext,
    *,
    collection: str,
    category: object | None,
    log_file_name: str,
    default_top_k: int,
) -> ToolSuccess | ToolFailure:
    if context.retrieval is None:
        return ToolFailure("retrieval_unavailable", "This application has no retrieval adapter")
    top_k = arguments.get("top_k", default_top_k)
    if top_k < 1:
        return ToolFailure("invalid_top_k", "top_k must be at least 1")
    try:
        results = context.retrieval.search(
            arguments["query"], collection=collection, category=category, top_k=top_k, cancellation=context.cancellation,
        )
    except InterruptedError:
        return ToolFailure("retrieval_cancelled", "Retrieval was cancelled")
    except Exception as error:
        logger.exception(
            "retrieval failed: collection=%s category=%s top_k=%s query_chars=%s",
            collection,
            category,
            top_k,
            len(str(arguments.get("query", ""))),
            extra=_FILE_ONLY_LOG,
        )
        logger.error(
            "Error: retrieval unavailable; collection=%s category=%s; details were written to %s",
            collection,
            category,
            log_file_name,
        )
        return ToolFailure("retrieval_unavailable", str(error))
    items = tuple(
        {"content": result.content, "metadata": {key: value for key, value in result.metadata.items() if key != "rerank_score"}}
        for result in results
    )
    return ToolSuccess({"query": arguments["query"], "total_results": len(items), "results": items})
