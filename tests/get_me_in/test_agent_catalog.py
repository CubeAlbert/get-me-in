import unittest

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability


def _spec(key: AgentKey) -> AgentSpec:
    return AgentSpec(
        key=key,
        display_name="测试 Agent",
        description="描述",
        responsibilities=("职责",),
        primary_goal="目标",
        success_criteria=("标准",),
        hard_constraints=("约束",),
        soft_constraints=(),
        style=AgentStyle("专业", "简洁", "直接"),
        model_profile="pro",
        capabilities=frozenset({Capability.ROUTE}),
    )


class AgentCatalogTests(unittest.TestCase):
    def test_get_and_public_descriptors_are_based_on_specs(self) -> None:
        catalog = AgentCatalog((_spec(AgentKey.MAIN),))

        self.assertEqual(AgentKey.MAIN, catalog.get(AgentKey.MAIN).key)
        self.assertEqual("测试 Agent", catalog.list_descriptors()[0].display_name)
