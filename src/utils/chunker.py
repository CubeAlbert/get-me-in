"""通用文本切分工具 — 按分隔符切分文本为逻辑块。

所有文件必须有 front-matter 块（``---`` 包裹的 KV 对），否则视为格式不合法，
返回空列表。front-matter 中的 KV 会被提取并注入到所有切分出的 Chunk。
后续 ``---`` 仍按正常分隔符切分。

用法:
    from src.utils.chunker import Chunker, Chunk

    c = Chunker()
    chunks = c.chunk(text, metadata={"category": "knowledge_base"})
"""

import re
import uuid
from dataclasses import dataclass, field

from src.logger import get_logger

logger = get_logger(__name__)


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
    所有输入文本必须以 front-matter 块开头，无 front-matter 的文件返回空列表。
    """

    DEFAULT_SEPARATOR = "\n---\n"

    # 匹配文本开头的 front-matter 块：可选前导空白 + --- + KV 行 + ---
    _FM_RE = re.compile(
        r"^[ \t\n\r]*---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.DOTALL
    )

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def chunk(
        self,
        text: str,
        separator: str | None = None,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        """解析 front-matter → 切分正文，无 front-matter 则跳过。

        Args:
            text: 待切分的原始文本，必须以 front-matter 块开头。
            separator: 分隔符，默认 ``\\n---\\n``。
            metadata: 附加到每个 Chunk 的元数据字典（覆盖 front-matter 同名字段）。

        Returns:
            Chunk 列表。无 front-matter 时返回空列表。
        """
        fm_meta, body = self._parse_front_matter(text)
        if fm_meta is None:
            logger.warning("Chunker: front-matter 缺失，返回空列表")
            # TODO: 未来增加无 front-matter 文件的处理逻辑
            #   - 纯文本自动注入默认 metadata
            #   - 或根据文件扩展名/目录推断 category
            return []

        sep = separator if separator is not None else self.DEFAULT_SEPARATOR
        caller_meta = metadata if metadata is not None else {}
        merged = {**fm_meta, **caller_meta}  # caller 覆盖 front-matter

        chunks: list[Chunk] = []
        for piece in body.split(sep):
            content = piece.strip()
            if not content:
                continue
            chunks.append(Chunk(content=content, metadata=dict(merged)))

        logger.info("Chunker: 切分完成，产出 %d 条 chunks", len(chunks))
        return chunks

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _parse_front_matter(self, text: str) -> tuple[dict | None, str]:
        """尝试从文本开头提取 front-matter。

        Args:
            text: 原始文本。

        Returns:
            ``(fm_metadata, remaining_text)`` —— 成功时 fm_metadata 为 dict；
            未匹配到 front-matter 时返回 ``(None, text)``。
        """
        m = self._FM_RE.match(text)
        if not m:
            return None, text

        fm_block = m.group(1)
        body = text[m.end():]

        meta: dict[str, str] = {}
        for line in fm_block.split("\n"):
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if key:
                    meta[key] = value

        return meta, body
