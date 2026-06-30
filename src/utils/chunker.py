"""通用文本切分工具 — 按分隔符切分文本为逻辑块。

用法:
    from src.utils.chunker import Chunker, Chunk

    c = Chunker()
    chunks = c.chunk(text, metadata={"category": "knowledge_base"})
"""

import uuid
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """一个逻辑块，向量检索的最小单元。

    Attributes:
        id: uuid4 字符串，Chroma 主键。
        content: 条目原始文本（不含分隔符）。
        metadata: 附带元数据，结构由写入方保证。

    Metadata 字段约定（写入方自行组合，Chunk 不校验）：

    ┌──────────────────┬──────────┬──────────────────────────────────────┐
    │ 字段             │ 写入方   │ 说明                                 │
    ├──────────────────┼──────────┼──────────────────────────────────────┤
    │ source_file      │ Loader   │ 来源文件路径，增删查均依赖此字段     │
    │ category         │ Loader   │ 仅 references，子目录名自动注入      │
    │ agent            │ Loader   │ 仅 memories，Agent 目录名自动注入    │
    │ date             │ Loader   │ 仅 memories，写入日期                │
    │ rerank_score     │ Reranker │ cross-encoder 重排分数（float）      │
    └──────────────────┴──────────┴──────────────────────────────────────┘
    """

    content: str
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


class Chunker:
    """通用文本切分器，按分隔符机械切分，不关心内容语义。

    统一分隔符为 Markdown 水平线 ``---``，记忆和参考数据共用同一套切分规则。
    """

    DEFAULT_SEPARATOR = "\n---\n"

    def chunk(
        self,
        text: str,
        separator: str | None = None,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        """按分隔符切分文本，每个有效片段生成一个 Chunk。

        切分后自动过滤仅含空白字符的片段。

        Args:
            text: 待切分的原始文本。
            separator: 分隔符，默认 ``\\n---\\n``。
            metadata: 附加到每个 Chunk 的元数据字典。

        Returns:
            Chunk 列表。
        """
        sep = separator if separator is not None else self.DEFAULT_SEPARATOR
        meta = metadata if metadata is not None else {}

        chunks: list[Chunk] = []
        for piece in text.split(sep):
            content = piece.strip()
            if not content:
                continue
            chunks.append(Chunk(content=content, metadata=dict(meta)))

        return chunks
