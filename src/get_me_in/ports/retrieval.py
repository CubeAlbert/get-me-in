"""检索能力的显式端口；具体索引实现将在 R6 接入。"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from src.get_me_in.ports.llm import CancellationSignal


@dataclass(frozen=True)
class RetrievalResult:
    """一次检索命中的可序列化结果。"""

    content: str
    metadata: Mapping[str, object]


class RetrievalPort(Protocol):
    """为工具提供检索能力，而不暴露 RAG 实现细节。"""

    def search(
        self,
        query: str,
        *,
        collection: str,
        category: str | None,
        top_k: int,
        cancellation: CancellationSignal,
    ) -> tuple[RetrievalResult, ...]: ...
