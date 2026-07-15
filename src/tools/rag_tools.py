"""RAG 查询工具 — 封装语义检索引擎。

- ``query_memory``: 检索用户记忆（fact / preference）
- ``query_reference_data``: 检索参考数据（按 category 过滤）
"""

from enum import StrEnum

from src.rag import is_ready, search as rag_search
from src.tools.registry import ConfirmMode, tool
from src.tools.exceptions import ToolCallException


# ---------------------------------------------------------------------------
# 枚举定义 — 确保 LLM 传入的 filter 值与 data 层约定一致
# ---------------------------------------------------------------------------


class MemoryType(StrEnum):
    """记忆类型 — query_memory 的 memory_type 参数可选值。

    !!! 修改枚举值前必须同步更新 !!!
    - 系统提示词: ``data/prompts/memory/builder.md``（facts / preferences 输出）
    - 数据约定: ``src/memory/schemas.py`` Memory.category 默认值
    """

    FACT = "fact"
    PREFERENCE = "preference"


class ReferenceCategory(StrEnum):
    """参考数据分类 — query_reference_data 的 category 参数可选值。

    !!! 修改枚举值前必须同步更新 !!!
    - 数据目录: ``data/reference/`` 下的子目录名必须与枚举值一致
    - RAG 索引: ``RagLoader`` 用子目录名自动填充 chunk.metadata["category"]
    """

    COMPANY_INFO = "company_info"
    INTERVIEW_QUESTIONS = "interview_questions"
    JOB_DESCRIPTIONS = "job_descriptions"
    KNOWLEDGE_BASE = "knowledge_base"
    RECOMMENDED_MATERIALS = "recommended_materials"
    RESUME_EXAMPLES = "resume_examples"


# 快速查找集合（用于校验 LLM 传入的值）
_VALID_MEMORY_TYPES = frozenset(t.value for t in MemoryType)
_VALID_CATEGORIES = frozenset(c.value for c in ReferenceCategory)


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------


@tool(
    purpose="语义检索用户记忆库，返回匹配的记忆条目（事实和偏好）。",
    use_when="需要查询用户之前存储的个人信息时，如技能、经历、偏好、期望等",
    do_not_use_when="需要查询技术参考、面试题、公司信息等公共数据时 — 用 query_reference_data",
    expected_output='{"query": "...", "total_results": N, "results": [{"content": "...", "metadata": {...}}]}',
    input_schema={
        "query": {
            "description": "自然语言查询，如 'Python 开发经验'、'期望薪资'",
        },
        "memory_type": {
            "description": (
                f"记忆类型过滤，可选: {', '.join(sorted(_VALID_MEMORY_TYPES))}"
                "。不填则搜索全部"
            ),
            "default": None,
        },
        "top_k": {
            "description": "返回结果数量，默认 5",
            "default": 5,
        },
    },
    confirm_mode=ConfirmMode.NEVER,
)
def query_memory(query: str, memory_type: str | None = None, top_k: int = 5) -> dict:
    _check_ready()

    filter = None
    if memory_type is not None:
        if memory_type not in _VALID_MEMORY_TYPES:
            raise ToolCallException(
                f"无效的 memory_type: {memory_type!r}",
                suggestion=f"可选值: {', '.join(sorted(_VALID_MEMORY_TYPES))}",
            )
        filter = {"category": memory_type}

    chunks = rag_search(query, collection="memories", filter=filter, top_k=top_k)
    return _chunks_to_result(query, chunks)


@tool(
    purpose="语义检索参考数据库，返回匹配的公共参考内容（技术知识、面试题、公司信息等）。",
    use_when="需要查询面试题、技术知识点、公司信息、简历示例、推荐资料等",
    do_not_use_when="需要查询用户个人记忆时 — 用 query_memory",
    expected_output='{"query": "...", "total_results": N, "results": [{"content": "...", "metadata": {...}}]}',
    input_schema={
        "query": {
            "description": "自然语言查询，如 '快速排序'、'阿里巴巴 Java 面试题'",
        },
        "category": {
            "description": (
                f"参考数据分类过滤，可选: {', '.join(sorted(_VALID_CATEGORIES))}"
                "。不填则搜索全部"
            ),
            "default": None,
        },
        "top_k": {
            "description": "返回结果数量，默认 5",
            "default": 5,
        },
    },
    agent=["*"],
    confirm_mode=ConfirmMode.NEVER,
)
def query_reference_data(query: str, category: str | None = None, top_k: int = 5) -> dict:
    _check_ready()

    filter = None
    if category is not None:
        if category not in _VALID_CATEGORIES:
            raise ToolCallException(
                f"无效的 category: {category!r}",
                suggestion=f"可选值: {', '.join(sorted(_VALID_CATEGORIES))}",
            )
        filter = {"category": category}

    chunks = rag_search(query, collection="references", filter=filter, top_k=top_k)
    return _chunks_to_result(query, chunks)


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------


def _check_ready() -> None:
    """确保 RAG 就绪，否则抛 ToolCallException。"""
    if not is_ready():
        raise ToolCallException(
            "RAG 索引尚未就绪，请稍后重试",
            suggestion="RAG 正在后台加载模型和数据，请等几秒后重试",
        )


def _chunks_to_result(query: str, chunks: list) -> dict:
    """将 Chunk 列表转换为 LLM 友好的结果结构。"""
    results = []
    for chunk in chunks:
        meta = dict(chunk.metadata)
        meta.pop("rerank_score", None)  # 内部评分，不暴露给 LLM
        results.append({
            "content": chunk.content,
            "metadata": meta,
        })
    return {
        "query": query,
        "total_results": len(results),
        "results": results,
    }
