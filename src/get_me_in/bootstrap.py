"""The sole v2 composition root."""

import os

from src.get_me_in.adapters.system import SystemClock, UuidGenerator
from src.get_me_in.adapters.openai_llm import OpenAILLMAdapter
from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.adapters.os_frontend import OSFrontend
from src.get_me_in.adapters.openai_web_search import OpenAIWebSearchAdapter
from src.get_me_in.adapters.authorized_file_reader import AuthorizedFileReader
from src.get_me_in.adapters.deferred_retrieval import DeferredRetrievalAdapter
from src.get_me_in.adapters.local_resume_artifacts import LocalResumeArtifacts
from src.get_me_in.adapters.subprocess_runner import SubprocessRunner
from src.get_me_in.adapters.json_session_repository import JsonSessionRepository
from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.application import Application
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.conversation_codec import ConversationCodec
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.session_codec import SessionSnapshotCodec
from src.get_me_in.application.session_service import SessionService
from src.get_me_in.application.settings import Settings
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
from src.get_me_in.domain.sessions import AgentSessionState, SessionState
from src.get_me_in.ports.llm import LLMPort, ModelProfile
from src.get_me_in.tools.system import build_system_tools
from src.get_me_in.tools.plan import build_plan_tools
from src.get_me_in.tools.workspace import build_workspace_tools
from src.get_me_in.tools.web import build_web_tools
from src.get_me_in.tools.switch import build_switch_tools
from src.get_me_in.tools.customer_file import build_customer_file_tools
from src.get_me_in.tools.retrieval import build_retrieval_tools
from src.get_me_in.tools.resume import build_resume_tools


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
        capabilities=frozenset(
            {
                Capability.SYSTEM,
                Capability.PLAN,
                Capability.INTERACTION,
                Capability.WEB_SEARCH,
                Capability.EXTERNAL_FILE_READ,
                Capability.ROUTE,
                Capability.KNOWLEDGE_QUERY,
            }
        ),
        priorities=("先明确用户当前目标，再选择下一步。",),
    )
    catalog = AgentCatalog((main_spec,))
    prompt_renderer = PromptRenderer(settings.prompts_dir)
    clock = SystemClock()
    id_generator = UuidGenerator()
    cancellation = CancellationToken()
    workspace = LocalWorkspace(settings.workspace_dir)
    frontend = OSFrontend()
    web_search = OpenAIWebSearchAdapter(api_key=settings.openai_api_key, base_url=settings.openai_base_url, model=settings.llm_pro_model)
    external_files = AuthorizedFileReader()
    retrieval = DeferredRetrievalAdapter()
    resume_artifacts = LocalResumeArtifacts(
        settings.resume_template_dir,
        SubprocessRunner(cancel_grace_seconds=settings.cancel_grace_seconds),
    )
    workspace_access = WorkspaceAccessState()
    plan_service = PlanService(id_generator)
    session_id = id_generator.new_id()
    tool_catalog = ToolCatalog(
        (*build_system_tools(clock), *build_plan_tools(), *build_workspace_tools(), *build_web_tools(), *build_switch_tools(), *build_customer_file_tools(), *build_retrieval_tools(), *build_resume_tools())
    )
    tool_executor = ToolExecutor(tool_catalog)
    runtime_llm = llm or OpenAILLMAdapter(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model_names={
            ModelProfile.PRO: settings.llm_pro_model,
            ModelProfile.FLASH: settings.llm_flash_model,
        },
        thinking_enabled=settings.llm_thinking_enabled,
    )
    runtime = AgentRuntime(
        spec=main_spec,
        prompt_renderer=prompt_renderer,
        llm=runtime_llm,
        clock=clock,
        id_generator=id_generator,
        cancellation=cancellation,
        agent_catalog=catalog,
        tool_catalog=tool_catalog,
        conversation_codec=ConversationCodec(),
        max_model_calls=settings.max_model_calls_per_run,
        model_timeout_seconds=settings.llm_timeout_seconds,
        tool_executor=tool_executor,
        tool_context=ToolContext(
            session_id=session_id,
            agent_key=AgentKey.MAIN,
            cancellation=cancellation,
            plan=plan_service,
            workspace=workspace,
            frontend=frontend,
            web_search=web_search,
            external_files=external_files,
            retrieval=retrieval,
            resume_artifacts=resume_artifacts,
            workspace_access=workspace_access,
        ),
    )
    session = SessionState(
        session_id=session_id,
        active_agent=AgentKey.MAIN,
        agents={AgentKey.MAIN: AgentSessionState()},
        handoff_stack=(),
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    sessions = SessionService(
        session,
        runtime=runtime,
        plans=plan_service,
        repository=JsonSessionRepository(settings.sessions_dir, codec=SessionSnapshotCodec()),
        clock=clock,
        workspace_access=workspace_access,
    )
    return Application(
        settings=settings,
        catalog=catalog,
        clock=clock,
        id_generator=id_generator,
        cancellation=cancellation,
        runtime=runtime,
        sessions=sessions,
        tool_catalog=tool_catalog,
        web_search=web_search,
    )
