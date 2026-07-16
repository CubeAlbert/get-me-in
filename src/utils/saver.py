"""会话存档工具 — 自动保存和恢复 Agent 对话历史。

低层函数：save_messages / load_messages / save_session_meta / list_sessions
高层封装：SaveManager — 管理 session_id、延迟清理、供 App 直接使用

用法:
    from src.utils.saver import SaveManager

    save_mgr = SaveManager(Path("data/save/"))
    save_mgr.save("main", history)          # 保存
    msgs = save_mgr.load_main(session_id)   # 恢复
    sessions = save_mgr.list_sessions()     # 列出
"""

from __future__ import annotations

import dataclasses
import json
import os as _os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from src.logger import get_logger

if TYPE_CHECKING:
    from src.message import Message

logger = get_logger(__name__)


def save_messages(filepath: Path, history: list[Message]) -> bool:
    """将对话历史序列化为 JSON 写入文件。自动创建父目录。

    Args:
        filepath: 目标文件路径。
        history: Message 列表。

    Returns:
        ``True`` 表示成功，``False`` 表示失败。
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [dataclasses.asdict(m) for m in history]
        filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.debug("saved %d messages to %s", len(history), filepath)
        return True
    except Exception:
        logger.exception("failed to save messages to %s", filepath)
        return False


def load_messages(filepath: Path) -> list[Message] | None:
    """从 JSON 文件读取并重建 Message 列表。

    Args:
        filepath: 存档文件路径。

    Returns:
        Message 列表；读取或解析失败返回 ``None``。
    """
    from src.message import Message

    try:
        raw = filepath.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            logger.warning("%s 不是 JSON 数组，无法加载", filepath)
            return None
        messages = [Message.from_dict(d) for d in data]
        logger.debug("loaded %d messages from %s", len(messages), filepath)
        return messages
    except FileNotFoundError:
        logger.warning("save file not found: %s", filepath)
        return None
    except Exception:
        logger.exception("failed to load messages from %s", filepath)
        return None


def save_session_meta(
    session_dir: Path,
    session_id: str,
    current_agent: str,
    plan: list | None = None,
    plan_keys_to_remove: list[str] | None = None,
    preview: str = "",
) -> None:
    """写入 session.json 元数据。

    Args:
        session_dir: 会话存档目录。
        session_id: 会话 ID (yyyyMMddHHmmss)。
        current_agent: 当前 Agent key（如 ``"main"`` / ``"resume"``）。
        plan: 当前 Agent 的 PlanItem 列表（序列化为 dict）。
        plan_keys_to_remove: 需要从 meta 中移除的 plan key 列表。
        preview: 会话预览文本（首条用户消息截断），用于 /restore 列表展示。
    """
    import dataclasses

    try:
        session_dir.mkdir(parents=True, exist_ok=True)

        meta_file = session_dir / "session.json"
        created_at = datetime.now(timezone.utc).isoformat()

        # 读取已有 meta，保留 created_at 和其他 agent 的 plan
        existing: dict = {}
        if meta_file.exists():
            try:
                existing = json.loads(meta_file.read_text(encoding="utf-8"))
                created_at = existing.get("created_at", created_at)
            except Exception:
                pass

        meta = {
            "id": session_id,
            "created_at": created_at,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "current_agent": current_agent,
        }

        # 保留其他 agent 的 plan（不在本次更新范围内）
        for key, value in existing.items():
            if key.endswith("_plan") and key not in (plan_keys_to_remove or []):
                meta[key] = value

        # 写入当前 agent 的 plan
        if plan is not None:
            plan_key = f"{current_agent}_plan"
            meta[plan_key] = [dataclasses.asdict(item) for item in plan]

        # preview：有新的就用新的，否则保留旧的
        if preview:
            meta["preview"] = preview[:60]
        elif existing.get("preview"):
            meta["preview"] = existing["preview"]

        meta_file.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # 将目录 mtime 更新到当前时间，供 list_sessions 排序
        _os.utime(str(session_dir), None)
    except Exception:
        logger.exception("failed to save session meta to %s", session_dir)


def list_sessions(save_dir: Path) -> list[dict]:
    """扫描存档目录，返回按最后修改时间倒序排列的会话列表。

    Args:
        save_dir: 存档根目录（如 ``data/save/``）。

    Returns:
        字典列表，每项: ``{id, saved_at, current_agent, has_sub, sub_agent}``。
    """
    if not save_dir.exists():
        return []

    entries: list[tuple[float, dict]] = []
    for session_dir in save_dir.iterdir():
        if not session_dir.is_dir():
            continue

        session_id = session_dir.name
        meta_file = session_dir / "session.json"

        saved_at = ""
        current_agent = "main"
        preview = ""
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                saved_at = meta.get("saved_at", "")
                current_agent = meta.get("current_agent", "main")
                preview = meta.get("preview", "")
            except Exception:
                pass

        # 检查是否有子 Agent 存档
        sub_files = [
            f for f in session_dir.glob("*.json")
            if f.stem not in ("main", "session")
        ]
        has_sub = len(sub_files) > 0
        sub_agent = sub_files[0].stem if has_sub else None

        # 用目录 mtime 排序（save_session_meta 会更新）
        mtime = session_dir.stat().st_mtime
        entry = {
            "id": session_id,
            "saved_at": saved_at,
            "current_agent": current_agent,
            "has_sub": has_sub,
            "sub_agent": sub_agent,
            "preview": preview,
        }
        entries.append((mtime, entry))

    # 按 mtime 倒序
    entries.sort(key=lambda x: x[0], reverse=True)
    return [e[1] for e in entries]


# ═══════════════════════════════════════════════════════════════════════
# SaveManager — 高层封装，供 App 直接使用
# ═══════════════════════════════════════════════════════════════════════


class SaveManager:
    """会话存档管理器 — 封装 session ID、文件路径、延迟清理逻辑。

    App 通过此对象完成 auto-save 和 restore，无需感知文件路径细节。

    用法::

        save_mgr = SaveManager(Path(config.SAVE_DIR))
        save_mgr.save("main", history)
        msgs = save_mgr.load_main("20260716143025")
    """

    def __init__(self, save_dir: Path) -> None:
        self._save_dir = save_dir
        self._session_id: str = datetime.now().strftime("%Y%m%d%H%M%S")
        self._pending_sub_cleanup: str | None = None

    # ── properties ──

    @property
    def session_id(self) -> str:
        """当前会话 ID（yyyyMMddHHmmss）。"""
        return self._session_id

    @session_id.setter
    def session_id(self, value: str) -> None:
        self._session_id = value
        self._pending_sub_cleanup = None

    # ── save ──

    def save(self, agent_key: str, history: list[Message], plan: list | None = None) -> None:
        """保存指定 Agent 的对话历史和 plan 状态到当前会话目录。

        同时处理延迟的子 Agent 清理：当前为 main 且有 pending cleanup 时，
        说明 main 已至少成功保存一次，可以安全删除旧 sub 存档及其 plan。
        """
        session_dir = self._save_dir / self._session_id

        if agent_key == "main":
            filepath = session_dir / "main.json"
        else:
            filepath = session_dir / f"{agent_key}.json"

        # 延迟清理：删除旧 sub 存档 + 其 plan
        plan_keys_to_remove: list[str] | None = None
        if agent_key == "main" and self._pending_sub_cleanup:
            self._delete_sub_save(self._pending_sub_cleanup)
            plan_keys_to_remove = [f"{self._pending_sub_cleanup}_plan"]
            self._pending_sub_cleanup = None

        # 提取 preview：首条有意义用户消息（截断 60 字符）
        preview = ""
        for m in history:
            if m.event_type.value == "user_input" and m.message.strip():
                preview = m.message.strip()
                break
        if not preview:
            for m in reversed(history):
                if m.event_type.value == "finish" and m.message.strip():
                    preview = m.message.strip()
                    break

        save_messages(filepath, history)
        save_session_meta(
            session_dir, self._session_id, agent_key,
            plan=plan,
            plan_keys_to_remove=plan_keys_to_remove,
            preview=preview,
        )

    def schedule_sub_cleanup(self, agent_key: str) -> None:
        """标记 sub Agent 存档待清理 — 下次 main 保存成功后自动删除。"""
        self._pending_sub_cleanup = agent_key

    # ── restore ──

    def load_main(self, session_id: str) -> list[Message] | None:
        """读取指定会话的 main Agent 历史。"""
        filepath = self._save_dir / session_id / "main.json"
        return load_messages(filepath)

    def load_sub(self, session_id: str, agent_key: str) -> list[Message] | None:
        """读取指定会话的子 Agent 历史。"""
        filepath = self._save_dir / session_id / f"{agent_key}.json"
        return load_messages(filepath)

    def find_sub_agent(self, session_id: str) -> str | None:
        """扫描会话目录，找到子 Agent 存档（若有），返回 agent_key。"""
        session_dir = self._save_dir / session_id
        if not session_dir.exists():
            return None
        sub_files = [
            f for f in session_dir.glob("*.json")
            if f.stem not in ("main", "session")
        ]
        return sub_files[0].stem if sub_files else None

    def list_sessions(self) -> list[dict]:
        """列出所有存档会话，按 mtime 倒序。"""
        return list_sessions(self._save_dir)

    def load_plans(self, session_id: str) -> dict[str, list]:
        """读取 session.json 中所有 agent 的 plan 状态。

        Returns:
            ``{"main": [PlanItem, ...], "resume": [PlanItem, ...]}``
            — key 为 agent_key，value 为 PlanItem 列表。无可反序列化。
        """
        from src.agents.plan import PlanItem, PlanStatus

        meta_file = self._save_dir / session_id / "session.json"
        if not meta_file.exists():
            return {}

        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("failed to read session.json: %s", meta_file)
            return {}

        plans: dict[str, list] = {}
        for key, value in meta.items():
            if not key.endswith("_plan") or not isinstance(value, list):
                continue
            agent_key = key[:-5]  # strip "_plan" suffix
            items = []
            for item_d in value:
                try:
                    items.append(PlanItem(
                        id=item_d["id"],
                        description=item_d["description"],
                        status=PlanStatus(item_d["status"]),
                        order=item_d["order"],
                    ))
                except Exception:
                    logger.exception("failed to parse plan item: %s", item_d)
            plans[agent_key] = items

        return plans

    # ── internal ──

    def _delete_sub_save(self, agent_key: str) -> None:
        """删除子 Agent 存档文件（仅在 main 确认保存成功后调用）。"""
        filepath = self._save_dir / self._session_id / f"{agent_key}.json"
        try:
            filepath.unlink(missing_ok=True)
            logger.info("deleted sub save: %s", filepath)
        except Exception:
            logger.exception("failed to delete sub save: %s", filepath)
