"""The sole v2 composition root."""

import os
from collections.abc import Mapping
from contextlib import ExitStack

from src.get_me_in.adapters.system import SystemClock, UuidGenerator
from src.get_me_in.adapters.openai_llm import OpenAILLMAdapter
from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.adapters.os_frontend import OSFrontend
from src.get_me_in.adapters.openai_web_search import OpenAIWebSearchAdapter
from src.get_me_in.adapters.authorized_file_reader import AuthorizedFileReader
from src.get_me_in.adapters.chroma_knowledge_index import (
    ChromaKnowledgeIndex,
    CrossEncoderReranker,
    SentenceTransformerEmbedder,
)
from src.get_me_in.adapters.json_manifest_repository import JsonManifestRepository
from src.get_me_in.adapters.json_memory_repository import JsonMemoryRepository
from src.get_me_in.adapters.local_knowledge_sources import LocalKnowledgeSourceRepository
from src.get_me_in.adapters.markdown_chunker import MarkdownChunker
from src.get_me_in.adapters.local_resume_artifacts import LocalResumeArtifacts
from src.get_me_in.adapters.json_artifact_repository import JsonArtifactRepository
from src.get_me_in.adapters.subprocess_runner import SubprocessRunner
from src.get_me_in.adapters.json_session_repository import JsonSessionRepository
from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.application import Application
from src.get_me_in.application.background_worker import BackgroundWorker
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.model_message import ModelMessageCodec
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.session_codec import SessionSnapshotCodec
from src.get_me_in.application.session_service import SessionService
from src.get_me_in.application.orchestration import Orchestrator
from src.get_me_in.application.knowledge_service import KnowledgeService
from src.get_me_in.application.memory_extractor import MemoryExtractor
from src.get_me_in.application.memory_service import MemoryService
from src.get_me_in.application.artifact_service import ArtifactService
from src.get_me_in.application.settings import Settings
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.application.resources import ResourceStack
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
from src.get_me_in.agents.resume import build_resume_spec
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
    runtime_llms: Mapping[AgentKey, LLMPort] | None = None,
) -> Application:
    """Build one isolated application and clean up every partial composition."""
    with ExitStack() as construction:
        application = _build_application(settings, runtime_llms, construction)
        construction.pop_all()
        return application


def _build_application(
    settings: Settings,
    runtime_llms: Mapping[AgentKey, LLMPort] | None,
    construction: ExitStack,
) -> Application:
    if settings.hf_endpoint:
        os.environ["HF_ENDPOINT"] = settings.hf_endpoint

    main_spec = AgentSpec(
        key=AgentKey.MAIN,
        display_name="程序员求职助手路由Agent",
        description=(
            "负责作为程序员求职助手系统的统一入口。"
            "只识别用户需求、收集路由所需的必要上下文，"
            "并将属于当前<SubAgents>清单职责的请求转交给对应专业子Agent。"
            "当前业务能力完全由该清单提供，自身不执行任何领域任务。"
        ),
        responsibilities=(
            "- 判断用户请求是否属于程序员求职相关领域。",
            "- 对属于求职领域的请求进行意图分类。",
            "- 仅从当前<SubAgents>穷尽清单中选择与用户需求匹配的子Agent。",
            "- 在切换Agent前收集必要上下文信息。",
            "- 仅在用户明确要求查询历史个人信息，或完成路由必须获得的个人信息经询问仍未获得时，才使用query_memory作一次针对性兜底。",
            "- 使用switch_to_subagent工具完成会话入口切换。",
            "- 在无法确定用户需求时，通过提问澄清。",
            "- 问候或用户询问能力时，只按当前<SubAgents>的真实职责介绍可用服务。",
            "- 当前<SubAgents>没有匹配项时，只说明暂不支持该请求。",
        ),
        primary_goal="确保用户请求只在当前实际可用的SubAgent能力范围内被识别和路由，不推测或执行未装配能力。",
        success_criteria=(
            "- 非程序员求职相关请求被拒绝处理。",
            "- 程序员求职请求被正确分类。",
            "- 用户需求不明确时，通过交互获得必要信息。",
            "- 切换Agent前提供完整且准确的上下文。",
            "- 只宣传和路由当前<SubAgents>明确提供的业务能力。",
            "- 无匹配SubAgent时明确说明暂不支持，且不提供替代建议。",
            "- 不直接执行任何领域任务。",
        ),
        hard_constraints=(
            "- 只能处理程序员求职相关场景。",
            "- 不回答与求职无关的问题。",
            "- 当前<SubAgents>是业务能力的唯一、权威且穷尽来源，不是示例或未来规划。",
            "- 不得根据产品名称、工具列表、历史消息、模型知识、用户请求或未来扩展推测业务能力。",
            "- 不得宣传、暗示、承诺或执行当前<SubAgents>列表外能力。",
            "- 工具仅用于意图识别、上下文收集、路由计划和切换入口，不构成业务能力。",
            "- 不提供任何领域专业答案。",
            "- 不模拟子Agent行为。",
            "- 不生成简历内容。",
            "- 如果用户请求属于当前某个SubAgent能力范围，必须切换Agent。",
            "- 如果没有匹配SubAgent，只能说明当前暂不支持，不得提供平台、资料、步骤或其他替代建议。",
            "- 如果无法判断用户需求，必须向用户提问，而不是猜测。",
        ),
        soft_constraints=(
            "- 优先保持连续对话体验。",
            "- 提问时尽量减少用户负担。",
            "- 优先使用当前对话信息；不得为主动个性化、补充用户画像或减少普通提问而查询memory。",
            "- 使用简洁明确的语言沟通。",
        ),
        style=AgentStyle(
            tone="专业、简洁、友好、引导式。",
            verbosity="简短。",
            explanation_style="以任务识别和下一步行动说明为主。避免提供领域知识解释。",
            rules=(
                "- 优先确认用户目标。",
                "- 需要澄清时使用简短问题。",
                "- 切换Agent时明确告知用户。",
                "- 问候或介绍能力时，只用用户语言概括当前SubAgent真实职责。",
                "- 保持自然对话，不暴露内部Agent架构细节。",
            ),
            avoids=(
                "- 避免直接回答领域问题或提供专业建议。",
                "- 避免宣传或暗示当前未提供的能力。",
                "- 避免为不支持的请求提供替代建议。",
                "- 避免解释自己无法完成任务的内部原因。",
                "- 避免讨论Agent、工具、路由机制。",
            ),
        ),
        model_profile="pro",
        temperature=0.1,
        capabilities=frozenset(
            {
                Capability.CURRENT_DATETIME,
                Capability.PLAN,
                Capability.INTERACTION,
                Capability.EXTERNAL_FILE_READ,
                Capability.ROUTE,
                Capability.MEMORY_QUERY,
            }
        ),
        priorities=(
            "1. 只依据当前<SubAgents>清单判断和介绍业务能力。",
            "2. 保持纯路由职责，不执行领域任务。",
            "3. 准确识别用户意图并选择匹配的当前SubAgent。",
            "4. 无匹配项时明确说明暂不支持且不提供替代建议。",
            "5. 减少不必要的问题询问并保持自然交互。",
        ),
    )
    resume_spec = build_resume_spec()
    catalog = AgentCatalog((main_spec, resume_spec))
    if runtime_llms is not None:
        if set(runtime_llms) != {AgentKey.MAIN, AgentKey.RESUME}:
            raise ValueError("runtime_llms must provide exactly Main and Resume instances")
        if runtime_llms[AgentKey.MAIN] is runtime_llms[AgentKey.RESUME]:
            raise ValueError("Main and Resume runtime LLM instances must be distinct")
    prompt_renderer = PromptRenderer(settings.prompts_dir)
    clock = SystemClock()
    id_generator = UuidGenerator()
    main_cancellation = CancellationToken()
    resume_cancellation = CancellationToken()
    workspace = LocalWorkspace(settings.workspace_dir)
    frontend = OSFrontend()
    web_search = OpenAIWebSearchAdapter(api_key=settings.openai_api_key, base_url=settings.openai_base_url, model=settings.llm_pro_model)
    construction.callback(web_search.close)
    external_files = AuthorizedFileReader()
    worker = BackgroundWorker("knowledge-memory", settings.shutdown_timeout_seconds)
    construction.callback(worker.close)
    from chromadb import PersistentClient
    knowledge_construction = ExitStack()
    construction.callback(knowledge_construction.close)
    knowledge_index = ChromaKnowledgeIndex(
        PersistentClient(path=str(settings.knowledge_chroma_dir)),
        SentenceTransformerEmbedder(settings.embedding_model, settings.embedding_batch_size),
        CrossEncoderReranker(settings.reranker_model, settings.rerank_batch_size, settings.retrieval_top_k),
    )
    knowledge_construction.callback(knowledge_index.close)
    knowledge = KnowledgeService(
        (LocalKnowledgeSourceRepository(settings.reference_dir), JsonMemoryRepository(settings.memories_dir, clock)),
        MarkdownChunker(),
        knowledge_index,
        JsonManifestRepository(settings.knowledge_manifest_path),
        worker,
    )
    knowledge_construction.pop_all()
    construction.callback(knowledge.close)
    resume_artifacts = LocalResumeArtifacts(
        settings.resume_template_dir,
        SubprocessRunner(cancel_grace_seconds=settings.cancel_grace_seconds),
        settings.pdf_build_timeout_seconds,
    )
    artifacts = ArtifactService(
        resume_artifacts,
        JsonArtifactRepository(settings.artifacts_dir),
        clock,
        id_generator,
        settings.artifact_log_max_bytes,
    )
    construction.callback(artifacts.close)
    workspace_access = WorkspaceAccessState()
    main_plan = PlanService(id_generator)
    resume_plan = PlanService(id_generator)
    session_id = id_generator.new_id()
    tool_catalog = ToolCatalog(
        (*build_system_tools(clock), *build_plan_tools(), *build_workspace_tools(), *build_web_tools(), *build_switch_tools(), *build_customer_file_tools(), *build_retrieval_tools(), *build_resume_tools())
    )
    tool_executor = ToolExecutor(tool_catalog)
    runtime_construction = ExitStack()
    construction.callback(runtime_construction.close)
    if runtime_llms is None:
        runtime_llms = {
            key: OpenAILLMAdapter(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model_names={ModelProfile.PRO: settings.llm_pro_model, ModelProfile.FLASH: settings.llm_flash_model},
                thinking_enabled=settings.llm_thinking_enabled,
            )
            for key in (AgentKey.MAIN, AgentKey.RESUME)
        }
    runtime_construction.callback(runtime_llms[AgentKey.MAIN].close)
    runtime_construction.callback(runtime_llms[AgentKey.RESUME].close)
    memory_construction = ExitStack()
    construction.callback(memory_construction.close)
    memory_llm = OpenAILLMAdapter(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model_names={ModelProfile.PRO: settings.llm_pro_model, ModelProfile.FLASH: settings.llm_flash_model},
        thinking_enabled=False,
    )
    memory_construction.callback(memory_llm.close)
    memory = MemoryService(
        JsonMemoryRepository(settings.memories_dir, clock),
        MemoryExtractor(
            memory_llm,
            (settings.prompts_dir / "memory" / "builder.md").read_text(encoding="utf-8"),
            clock,
            id_generator,
            settings.llm_timeout_seconds,
        ),
        knowledge,
        worker,
    )
    memory_construction.pop_all()
    construction.callback(memory.close)
    main_runtime = AgentRuntime(
        spec=main_spec,
        prompt_renderer=prompt_renderer,
        llm=runtime_llms[AgentKey.MAIN],
        clock=clock,
        id_generator=id_generator,
        cancellation=main_cancellation,
        agent_catalog=catalog,
        tool_catalog=tool_catalog,
        conversation_codec=ModelMessageCodec(),
        max_model_calls=settings.max_model_calls_per_run,
        model_timeout_seconds=settings.llm_timeout_seconds,
        tool_executor=tool_executor,
        tool_context=ToolContext(
            session_id=session_id,
            agent_key=AgentKey.MAIN,
            cancellation=main_cancellation,
            plan=main_plan,
            workspace=workspace,
            frontend=frontend,
            web_search=web_search,
            external_files=external_files,
            retrieval=knowledge,
            resume_artifacts=artifacts,
            workspace_access=workspace_access,
        ),
    )
    resume_runtime = AgentRuntime(
        spec=resume_spec, prompt_renderer=prompt_renderer, llm=runtime_llms[AgentKey.RESUME],
        clock=clock, id_generator=id_generator, cancellation=resume_cancellation,
        agent_catalog=catalog, tool_catalog=tool_catalog, conversation_codec=ModelMessageCodec(),
        max_model_calls=settings.max_model_calls_per_run, model_timeout_seconds=settings.llm_timeout_seconds,
        tool_executor=tool_executor,
        tool_context=ToolContext(
            session_id=session_id, agent_key=AgentKey.RESUME, cancellation=resume_cancellation,
            plan=resume_plan, workspace=workspace, frontend=frontend, web_search=web_search,
            external_files=external_files, retrieval=knowledge, resume_artifacts=artifacts,
            workspace_access=workspace_access,
        ),
    )
    session = SessionState(
        session_id=session_id,
        active_agent=AgentKey.MAIN,
        agents={AgentKey.MAIN: AgentSessionState(), AgentKey.RESUME: AgentSessionState()},
        handoff_stack=(),
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    sessions = SessionService(
        session,
        orchestrator=Orchestrator({AgentKey.MAIN: main_runtime, AgentKey.RESUME: resume_runtime}),
        plans={AgentKey.MAIN: main_plan, AgentKey.RESUME: resume_plan},
        repository=JsonSessionRepository(settings.sessions_dir, codec=SessionSnapshotCodec()),
        clock=clock,
        id_generator=id_generator,
        workspace_access=workspace_access,
    )
    runtime_construction.pop_all()
    construction.callback(sessions.close)
    resources = ResourceStack()
    resources.register("web_search", web_search.close)
    resources.register("sessions", sessions.close)
    resources.register("knowledge", knowledge.close)
    resources.register("memory", memory.close)
    resources.register("artifacts", artifacts.close)
    resources.register("background_worker", worker.close)
    application = Application(
        settings=settings,
        catalog=catalog,
        clock=clock,
        id_generator=id_generator,
        sessions=sessions,
        tool_catalog=tool_catalog,
        web_search=web_search,
        resources=resources,
        knowledge=knowledge,
        memory=memory,
    )
    knowledge.start()
    return application
