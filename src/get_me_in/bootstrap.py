"""The sole v2 composition root."""

import os

from src.get_me_in.adapters.system import SystemClock, UuidGenerator
from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.application import Application
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.settings import Settings
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
from src.get_me_in.ports.llm import LLMPort


def build_application(
    settings: Settings,
    *,
    llm: LLMPort | None = None,
) -> Application:
    """Build one isolated R1 application without import-time side effects."""
    if settings.hf_endpoint:
        os.environ["HF_ENDPOINT"] = settings.hf_endpoint

    main_spec = AgentSpec(
        key=AgentKey.MAIN,
        display_name="主 Agent",
        description="负责识别用户意图并编排已声明的能力。",
        responsibilities=("识别意图", "编排能力"),
        primary_goal="将用户请求路由到正确的处理能力。",
        success_criteria=("路由决策明确",),
        hard_constraints=("不直接执行冻结的领域功能",),
        soft_constraints=("必要时说明下一步",),
        style=AgentStyle(
            tone="清晰、专业",
            verbosity="适中",
            explanation_style="先给结论，再给必要说明",
        ),
        model_profile="pro",
        capabilities=frozenset({Capability.ROUTE}),
        priorities=("先明确用户当前目标，再选择下一步。",),
    )
    return Application(
        settings=settings,
        catalog=AgentCatalog((main_spec,)),
        prompt_renderer=PromptRenderer(settings.prompts_dir),
        clock=SystemClock(),
        id_generator=UuidGenerator(),
        cancellation=CancellationToken(),
        llm=llm,
    )
