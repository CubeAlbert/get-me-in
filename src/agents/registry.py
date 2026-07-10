"""AgentRegistry — 子 Agent 注册表，全局单例。

与 ToolRegistry 对称设计：
- ``register(name, agent)`` 注册并从 agent._get_*() 抽取 SubAgentDescriptor
- ``list_agents_prompt()`` 生成 ``{{SUB_AGENTS_LIST}}`` 占位符内容
- 单例通过 ``get_agent_registry()`` 获取（双检锁线程安全）
"""

import threading
from dataclasses import dataclass

from src.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# 模块级单例
# ---------------------------------------------------------------------------

_registry: "AgentRegistry | None" = None
_lock = threading.Lock()


def get_agent_registry() -> "AgentRegistry":
    """获取 AgentRegistry 全局单例（双检锁，线程安全）。"""
    global _registry
    if _registry is None:
        with _lock:
            if _registry is None:
                _registry = AgentRegistry()
    return _registry


# ---------------------------------------------------------------------------
# SubAgentDescriptor
# ---------------------------------------------------------------------------


@dataclass
class SubAgentDescriptor:
    """子 Agent 元数据，从 BaseAgent._get_*() 抽取。

    字段聚焦路由决策所需信息，不含 tone/verbosity/style。
    """

    name: str              # registry key
    display_name: str      # _get_agent_name()
    description: str       # _get_agent_description()
    responsibilities: str  # _get_responsibilities()
    hard_constraints: str  # _get_hard_constraints()

    def to_xml(self) -> str:
        """渲染为 05_sub_agents.md 格式的 XML 块。"""
        return (
            f'<SubAgent name="{self.name}">\n'
            f"  <Name>{self.display_name}</Name>\n"
            f"  <Description>{self.description}</Description>\n"
            f"  <Responsibilities>{self.responsibilities}</Responsibilities>\n"
            f"  <HardConstraints>{self.hard_constraints}</HardConstraints>\n"
            f"</SubAgent>"
        )


# ---------------------------------------------------------------------------
# AgentRegistry
# ---------------------------------------------------------------------------


class AgentRegistry:
    """子 Agent 注册表。

    全局单例，与 ToolRegistry 对称。MainAgent 通过
    ``list_agents_prompt()`` 将子 Agent 列表注入 system prompt。
    """

    def __init__(self) -> None:
        self._descriptors: dict[str, SubAgentDescriptor] = {}
        self._agents: dict[str, object] = {}  # BaseAgent 实例，object 避免循环 import

    # -- public API ---------------------------------------------------------

    def register(self, name: str, agent: object) -> None:
        """注册子 Agent，同时构建 SubAgentDescriptor。

        Args:
            name: 注册名（也是 switch_to_subagent 的 sub_agent 参数值）。
            agent: BaseAgent 实例。
        """
        if name in self._agents:
            logger.warning("Agent %r 已注册，覆盖旧实例。", name)

        self._agents[name] = agent
        self._descriptors[name] = SubAgentDescriptor(
            name=name,
            display_name=agent._get_agent_name(),
            description=agent._get_agent_description(),
            responsibilities=agent._get_responsibilities(),
            hard_constraints=agent._get_hard_constraints(),
        )
        logger.info("AgentRegistry: 已注册 %r", name)

    def get(self, name: str) -> object:
        """获取子 Agent 实例。

        Raises:
            KeyError: 未找到指定名称的 Agent。
        """
        if name not in self._agents:
            raise KeyError(f"未找到 Agent: {name!r}，可用: {list(self._agents)}")
        return self._agents[name]

    def list(self) -> list[str]:
        """返回所有已注册 Agent 名称。"""
        return list(self._agents.keys())

    def list_agents_prompt(self) -> str:
        """生成子 Agent 列表 XML，用于填充 ``{{SUB_AGENTS_LIST}}``。"""
        if not self._descriptors:
            return ""
        parts = [d.to_xml() for d in self._descriptors.values()]
        return "\n".join(parts)
