"""RAG Loader — 数据加载入口，读取磁盘文件入库。

用法:
    from src.rag.loader import RagLoader, LoaderState
    from src.rag.store import ChromaStore
    from src.rag.reranker import Reranker

    loader = RagLoader(store=store, reranker=reranker)
    loader.auto_load()
    if loader.state == LoaderState.READY:
        ...
"""

import threading
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from src.config import config
from src.rag.chunker import Chunker
from src.rag.reranker import Reranker
from src.rag.store import ChromaStore


class LoaderState(Enum):
    """加载器状态。"""

    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class RagLoader:
    """RAG 数据唯一入口，负责扫描磁盘文件 → Chunker → ChromaStore。

    Store / Reranker 通过构造函数注入（单例由 src/rag/__init__.py 管理），
    Chunker 无状态内部创建。同步 + threading.Lock 保证串行，
    LOADING 状态下拒绝新请求。异常写入 state/error 不抛出。
    """

    REFERENCE_DIR = Path("data/reference")
    MEMORIES_DIR = Path("data/memories")
    LAST_UPDATE_FILE = Path("data/chroma/.last_update")

    def __init__(self, store: ChromaStore, reranker: Reranker) -> None:
        self._store = store
        self._reranker = reranker
        self._chunker = Chunker()
        self._state = LoaderState.IDLE
        self._error_msg: str | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    @property
    def state(self) -> LoaderState:
        return self._state

    @property
    def error(self) -> str | None:
        return self._error_msg

    def auto_load(self) -> None:
        """启动时同步加载。内存模式全量；持久化模式通过 .last_update 做增量。"""
        if not self._lock.acquire(blocking=False):
            return
        try:
            self._state = LoaderState.LOADING
            self._error_msg = None

            is_persistent = bool(getattr(config, "CHROMA_PERSIST_DIR", None))
            last_update = self._read_timestamp() if is_persistent else 0.0

            if last_update == 0.0:
                self._load_all()
            else:
                self._load_incremental(last_update)

            if is_persistent:
                self._write_timestamp()

            self._state = LoaderState.READY
        except Exception as e:
            self._state = LoaderState.ERROR
            self._error_msg = str(e)
        finally:
            self._lock.release()

    def reload(self, target: str | None = None) -> str:
        """手动重载。target=None 全量重载（走状态机）；target 非空匹配路径重载。

        Returns:
            target=None 时返回 ""；target 非空时返回结果描述。
        """
        if target is None:
            return self._reload_full()

        if not self._lock.acquire(blocking=False):
            return "加载中，请稍后重试"
        try:
            return self._reload_matched(target)
        finally:
            self._lock.release()

    def load_file(self, path: Path) -> None:
        """增量加载单个文件。Memory 模块运行时调用。"""
        with self._lock:
            try:
                self._state = LoaderState.LOADING
                self._error_msg = None

                collection, extra_meta = self._infer_meta(path)
                self._load_one(path, collection, extra_meta)

                self._state = LoaderState.READY
            except Exception as e:
                self._state = LoaderState.ERROR
                self._error_msg = str(e)

    # ------------------------------------------------------------------
    # reload 子逻辑
    # ------------------------------------------------------------------

    def _reload_full(self) -> str:
        """全量重载，走状态机。"""
        if not self._lock.acquire(blocking=False):
            return "加载中，请稍后重试"
        try:
            self._state = LoaderState.LOADING
            self._error_msg = None

            self._load_all()
            if getattr(config, "CHROMA_PERSIST_DIR", None):
                self._write_timestamp()

            self._state = LoaderState.READY
        except Exception as e:
            self._state = LoaderState.ERROR
            self._error_msg = str(e)
        finally:
            self._lock.release()
        return ""

    def _reload_matched(self, target: str) -> str:
        """匹配路径重载，不动状态机。已在锁内。"""
        matched: list[Path] = []
        for root in (self.REFERENCE_DIR, self.MEMORIES_DIR):
            if not root.exists():
                continue
            for md in root.rglob("*.md"):
                if target in str(md):
                    matched.append(md)

        if not matched:
            return f"未匹配到包含 '{target}' 的文件"

        for md in matched:
            collection, extra_meta = self._infer_meta(md)
            self._load_one(md, collection, extra_meta)

        return f"已重载 {len(matched)} 个文件"

    # ------------------------------------------------------------------
    # 内部 — 遍历 & 加载
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """全量加载 references + memories 下所有 .md，已在锁内。"""
        self._load_dir(self.REFERENCE_DIR, collection="references")
        self._load_dir(self.MEMORIES_DIR, collection="memories")

    def _load_incremental(self, last_update: float) -> None:
        """增量加载 mtime > last_update 的文件，已在锁内。"""
        for root, collection in (
            (self.REFERENCE_DIR, "references"),
            (self.MEMORIES_DIR, "memories"),
        ):
            if not root.exists():
                continue
            for md in sorted(root.rglob("*.md")):
                if md.stat().st_mtime > last_update:
                    _, extra_meta = self._infer_meta(md, root)
                    self._load_one(md, collection, extra_meta)

    def _load_dir(self, root: Path, collection: str) -> None:
        """遍历目录下所有 .md 入库，已在锁内。"""
        if not root.exists():
            return
        for md in sorted(root.rglob("*.md")):
            _, extra_meta = self._infer_meta(md, root)
            self._load_one(md, collection, extra_meta)

    def _load_one(self, path: Path, collection: str, extra_meta: dict) -> None:
        """读取文件 → chunk → remove 旧数据 → add，已在锁内。"""
        text = path.read_text(encoding="utf-8")
        meta = {"source_file": str(path), **extra_meta}
        chunks = self._chunker.chunk(text, metadata=meta)
        self._store.remove(str(path), collection=collection)
        self._store.add(chunks, collection=collection)

    # ------------------------------------------------------------------
    # 路径推断
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_meta(path: Path, _root: Path | None = None) -> tuple[str, dict]:
        """从文件路径推断 collection 名和附加 metadata。

        data/reference/<category>/file.md  → ("references", {"category": "<category>"})
        data/memories/<agent>/file.md      → ("memories",  {"agent": "<agent>", "date": "<stem>"})
        """
        parent = str(path.parent)
        if "reference" in parent:
            return ("references", {"category": path.parent.name})
        if "memories" in parent:
            return ("memories", {"agent": path.parent.name, "date": path.stem})
        return ("references", {})

    # ------------------------------------------------------------------
    # 时间戳
    # ------------------------------------------------------------------

    def _read_timestamp(self) -> float:
        try:
            return float(self.LAST_UPDATE_FILE.read_text(encoding="utf-8").strip())
        except (FileNotFoundError, ValueError):
            return 0.0

    def _write_timestamp(self) -> None:
        self.LAST_UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        ts = str(datetime.now(timezone.utc).timestamp())
        self.LAST_UPDATE_FILE.write_text(ts, encoding="utf-8")
