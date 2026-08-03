import unittest
from dataclasses import replace
import json
from pathlib import Path
import tempfile
from threading import Event, Thread, enumerate as enumerate_threads
from unittest.mock import patch

from src.get_me_in.bootstrap import build_application
from src.get_me_in.application.commands import Approve, Continue, Reject, UserMessage
from src.get_me_in.application.app_commands import DumpSession, ReloadKnowledge, RestoreSession, RewindSession
from src.get_me_in.application.events import ApprovalRequested, Cancelled, Completed, HandoffRequested, Paused, Progress, ProgressKind, ToolFinished, ToolStarted
from src.get_me_in.application.localization import Locale
from src.get_me_in.application.settings import KnowledgeIndexMode, Settings
from src.get_me_in.application.memory_service import MemoryService
from src.get_me_in.domain.agents import AgentKey, AgentStyle
from src.get_me_in.domain.knowledge import ReloadReport
from src.get_me_in.domain.sessions import RuntimePhase
from src.get_me_in.ports.llm import CancellationSignal, LLMRequest, LLMResult, ModelProfile
from src.get_me_in.tools.retrieval import build_retrieval_tools


def _settings(*, sessions_dir: Path = Path("data/runtime/sessions")) -> Settings:
    return Settings(
        openai_api_key="key",
        openai_base_url="https://example.test",
        llm_pro_model="pro",
        llm_flash_model="flash",
        main_model_profile=ModelProfile.PRO,
        resume_model_profile=ModelProfile.PRO,
        memory_model_profile=ModelProfile.FLASH,
        web_search_model_profile=ModelProfile.PRO,
        main_temperature=0.1,
        resume_temperature=0.2,
        memory_temperature=0.0,
        llm_timeout_seconds=60,
        llm_thinking_enabled=True,
        hf_endpoint=None,
        reference_dir=Path("data/reference"),
        prompts_dir=Path("data/prompts"),
        resume_template_dir=Path("data/resume/template"),
        workspace_dir=Path("data/workspace"),
        sessions_dir=sessions_dir,
        log_dir=Path("data/logs"),
        log_level="INFO",
        max_model_calls_per_run=100,
        cancel_grace_seconds=2.0,
        show_thinking=False,
        ui_locale=Locale.ZH_CN,
        response_locale=Locale.ZH_CN,
        locales_dir=Path("data/locales"),
        knowledge_index_mode=KnowledgeIndexMode.PERSISTENT,
        knowledge_manifest_path=Path("data/runtime/knowledge/manifest.json"),
        knowledge_chroma_dir=Path("data/runtime/knowledge/chroma"),
        memories_dir=Path("data/runtime/memories"),
        embedding_model="BAAI/bge-base-zh-v1.5",
        reranker_model="BAAI/bge-reranker-v2-m3",
        embedding_batch_size=32,
        rerank_batch_size=32,
        retrieval_top_k=8,
        shutdown_timeout_seconds=60.0,
        auto_memory_on_exit=False,
        artifacts_dir=Path("data/runtime/artifacts"),
        pdf_build_timeout_seconds=60.0,
        artifact_log_max_bytes=65536,
        model_format_repair_limit=3,
        web_search_max_tokens=4096,
        log_file_name="app.log",
        log_max_bytes=10485760,
        log_backup_count=5,
        cli_worker_poll_interval_seconds=0.1,
        subprocess_poll_interval_seconds=0.05,
        cli_result_preview_chars=500,
        cli_argument_preview_chars=160,
        session_preview_chars=80,
        workspace_read_default_limit=100,
        workspace_search_max_matches=50,
        workspace_file_search_max_results=50,
        customer_file_read_default_limit=100,
        retrieval_default_top_k=5,
        hf_hub_disable_progress_bars=True,
        tqdm_disable=True,
        transformers_verbosity="error",
        model_library_log_level="ERROR",
    )


class BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self._knowledge_start_patcher = patch(
            "src.get_me_in.bootstrap.KnowledgeService.start"
        )
        self.knowledge_start = self._knowledge_start_patcher.start()
        self.addCleanup(self._knowledge_start_patcher.stop)

    def _build_application(self, settings: Settings, *, llm: object):
        application = build_application(
            settings,
            runtime_llms={AgentKey.MAIN: llm, AgentKey.RESUME: _FakeLlm("resume")},
        )
        self.addCleanup(application.close)
        return application

    def test_applications_do_not_share_mutable_runtime_dependencies(self) -> None:
        first = self._build_application(_settings(), llm=_FakeLlm("first"))
        second = self._build_application(_settings(), llm=_FakeLlm("second"))

        first.request_cancel()

        self.assertFalse(first._sessions._orchestrator._runtimes[AgentKey.MAIN]._cancellation.is_cancelled)
        self.assertFalse(second._sessions._orchestrator._runtimes[AgentKey.MAIN]._cancellation.is_cancelled)
        self.assertIsNot(first.catalog, second.catalog)
        self.assertIsNot(first.clock, second.clock)
        self.assertIsNot(first.id_generator, second.id_generator)
        self.assertEqual({AgentKey.MAIN, AgentKey.RESUME}, {item.key for item in second.catalog.list_descriptors()})

    def test_bootstrap_injects_the_configured_log_file_name(self) -> None:
        settings = replace(
            _settings(),
            log_file_name="custom-runtime.log",
            session_preview_chars=7,
            workspace_read_default_limit=11,
            workspace_search_max_matches=13,
            workspace_file_search_max_results=17,
            customer_file_read_default_limit=19,
            retrieval_default_top_k=23,
        )
        with (
            patch(
                "src.get_me_in.bootstrap.build_retrieval_tools",
                wraps=build_retrieval_tools,
            ) as retrieval_builder,
            patch(
                "src.get_me_in.bootstrap.MemoryService",
                wraps=MemoryService,
            ) as memory_type,
        ):
            application = self._build_application(settings, llm=_FakeLlm("done"))

        retrieval_builder.assert_called_once_with("custom-runtime.log", 23)
        self.assertEqual("custom-runtime.log", memory_type.call_args.args[-1])
        self.assertEqual(
            11, application.tool_catalog.get("workspace_read").schema.properties["limit"].default
        )
        self.assertEqual(
            13, application.tool_catalog.get("workspace_grep").schema.properties["max_matches"].default
        )
        self.assertEqual(
            17, application.tool_catalog.get("workspace_search_file").schema.properties["max_results"].default
        )
        self.assertEqual(
            19, application.tool_catalog.get("read_customer_file").schema.properties["limit"].default
        )
        self.assertEqual(
            23, application.tool_catalog.get("query_memory").schema.properties["top_k"].default
        )

    def test_application_handles_one_no_tool_conversation(self) -> None:
        llm = _FakeLlm("completed")
        application = self._build_application(_settings(), llm=llm)

        events = _pump(application, UserMessage("Help me prepare for an interview"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("completed", events[-1].message.content)
        self.assertIn("Help me prepare for an interview", llm.request.messages[-1].content)
        self.assertIn("get_current_datetime", llm.request.messages[0].content)
        self.assertIn(
            "<UseWhen>需要知道当前时间时</UseWhen>",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "<ExpectedOutput>YYYY-MM-DD HH:mm:ss ±HHMM 格式的带时区日期时间字符串</ExpectedOutput>",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "工具用于辅助履行既有职责，不会自行增加、暗示或证明任何业务能力。",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "<HandoffContextContract>",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "handoff 接收回合不得调用任何工具",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "以上列表是当前会话全部业务能力的唯一、权威且穷尽来源",
            llm.request.messages[0].content,
        )
        self.assertIn(
            '<SubAgent name="resume">',
            llm.request.messages[0].content,
        )
        self.assertIn(
            "<Name>简历定制Agent</Name>",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "<Tone>\n专业、简洁、友好、引导式。\n</Tone>",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "以任务识别和下一步行动说明为主。避免提供领域知识解释。",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "- 保持自然对话，不暴露内部Agent架构细节。",
            llm.request.messages[0].content,
        )
        self.assertIn(
            "- 避免讨论Agent、工具、路由机制。",
            llm.request.messages[0].content,
        )
        self.assertNotIn("get_working_dir", llm.request.messages[0].content)
        self.assertNotIn("web_search", llm.request.messages[0].content)
        self.assertNotIn("query_reference_data", llm.request.messages[0].content)
        self.assertNotIn("面试", llm.request.messages[0].content)
        self.assertNotIn("学习", llm.request.messages[0].content)
        self.assertNotIn("workspace_write", llm.request.messages[0].content)
        self.assertNotIn("copy_template", llm.request.messages[0].content)
        self.assertFalse(llm.cancellation.is_cancelled)

    def test_application_executes_its_explicit_system_tool_catalog(self) -> None:
        application = self._build_application(
            _settings(),
            llm=_FakeLlm(
                [
                    _tool_call("get_current_datetime"),
                    _finish("done", "done"),
                ]
            ),
        )

        events = _pump(application, UserMessage("What time is it?"))

        self.assertTrue(any(isinstance(event, ToolFinished) for event in events))
        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("done", events[-1].message.content)

    def test_application_exposes_the_complete_explicit_tool_catalog(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        names = tuple(item["name"] for item in application.tool_catalog.export_descriptors())

        self.assertEqual(26, len(names))
        self.assertEqual(
            {
                "get_current_datetime", "get_working_dir", "web_search",
                "switch_to_subagent", "switch_to_mainagent", "provide_choices",
                "create_plan", "update_plan_status", "cancel_all_plans", "replan",
                "workspace_read", "workspace_list", "workspace_grep", "workspace_search_file",
                "workspace_replace", "workspace_write", "workspace_delete", "workspace_move",
                "workspace_edit", "workspace_open", "read_customer_file", "query_memory",
                "query_reference_data", "copy_template", "build_pdf", "merge_pdfs",
            },
            set(names),
        )

    def test_main_agent_sees_only_the_confirmed_routing_tool_allowlist(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))
        main = application.catalog.get(AgentKey.MAIN)

        names = {
            tool.name
            for tool in application.tool_catalog.list_for_capabilities(main.capabilities)
        }

        self.assertEqual(
            {
                "create_plan",
                "update_plan_status",
                "cancel_all_plans",
                "replan",
                "get_current_datetime",
                "provide_choices",
                "read_customer_file",
                "query_memory",
                "switch_to_subagent",
            },
            names,
        )

    def test_every_production_tool_declares_capabilities(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        missing = [
            item["name"]
            for item in application.tool_catalog.export_descriptors()
            if not item["required_capabilities"]
        ]

        self.assertEqual([], missing)

    def test_composition_restores_complete_legacy_communication_styles(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        self.assertEqual(
            AgentStyle(
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
            application.catalog.get(AgentKey.MAIN).style,
        )
        self.assertEqual(
            AgentStyle(
                tone="专业、细致、注重格式准确性。",
                verbosity="适中，操作类信息简洁，内容建议可以详细。",
                explanation_style='按"当前状态 → 修改计划 → 执行 → 结果"的流程呈现。',
                rules=(
                    "- 收到kind=\"delegate\"的HandoffContext时先向用户确认或纠正交接内容；非handoff回合再按需要确认是新建简历还是修改已有简历。",
                    "- 新建时先与用户确认语言和文件名前缀。",
                    "- 每次编辑前先读取文件，确认行号和内容后再编辑。",
                    "- 大段内容修改用全局替换，精确行级修改用逐行编辑。",
                    "- 完成任务后询问是否需要编译 PDF 和预览。",
                    "- 当前任务全部完成或用户明确表示结束时，调用 finish，不闲聊。",
                ),
                avoids=(
                    "- 避免凭记忆编辑文件，必须先读取文件确认内容。",
                    "- 避免校验用的旧内容与实际文件内容不一致。",
                    "- 避免讨论 Agent 路由或实现细节。",
                    "- 避免替用户编造经历、技能等信息。",
                ),
            ),
            application.catalog.get(AgentKey.RESUME).style,
        )

    def test_composition_restores_complete_legacy_agent_metadata(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))
        main = application.catalog.get(AgentKey.MAIN)
        resume = application.catalog.get(AgentKey.RESUME)

        self.assertEqual(
            (
                "程序员求职助手路由Agent",
                "负责作为程序员求职助手系统的统一入口。只识别用户需求、收集路由所需的必要上下文，"
                "并将属于当前<SubAgents>清单职责的请求转交给对应专业子Agent。"
                "当前业务能力完全由该清单提供，自身不执行任何领域任务。",
                (
                    "- 判断用户请求是否属于程序员求职相关领域。",
                    "- 对属于求职领域的请求进行意图分类。",
                    "- 仅从当前<SubAgents>穷尽清单中选择与用户需求匹配的子Agent。",
                    "- 在切换Agent前收集必要上下文信息。",
                    "- 仅在用户明确要求查询历史个人信息，或完成路由必须获得的个人信息经询问仍未获得时，才使用query_memory作一次针对性兜底。",
                    "- 使用switch_to_subagent工具完成会话入口切换，并在context中提供kind=\"delegate\"的中性HandoffContext，区分已确认信息与推断信息。",
                    "- 收到kind=\"return\"的HandoffContext时，只向用户汇报完成／阻塞／待决定事项并询问下一步。",
                    "- 在无法确定用户需求时，通过提问澄清。",
                    "- 问候或用户询问能力时，只按当前<SubAgents>的真实职责介绍可用服务。",
                    "- 当前<SubAgents>没有匹配项时，只说明暂不支持该请求。",
                ),
                "确保用户请求只在当前实际可用的SubAgent能力范围内被识别和路由，不推测或执行未装配能力。",
                (
                    "- 非程序员求职相关请求被拒绝处理。",
                    "- 程序员求职请求被正确分类。",
                    "- 用户需求不明确时，通过交互获得必要信息。",
                    "- 切换Agent前提供完整且准确的上下文。",
                    "- 只宣传和路由当前<SubAgents>明确提供的业务能力。",
                    "- 无匹配SubAgent时明确说明暂不支持，且不提供替代建议。",
                    "- 不直接执行任何领域任务。",
                ),
                (
                    "1. 只依据当前<SubAgents>清单判断和介绍业务能力。",
                    "2. 保持纯路由职责，不执行领域任务。",
                    "3. 准确识别用户意图并选择匹配的当前SubAgent。",
                    "4. 无匹配项时明确说明暂不支持且不提供替代建议。",
                    "5. 减少不必要的问题询问并保持自然交互。",
                ),
                (
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
                    "- 最新输入包含HandoffContext时即为handoff接收回合；该回合不得调用任何工具或再次路由，必须finish并等待下一条真实用户消息。",
                ),
                (
                    "- 优先保持连续对话体验。",
                    "- 提问时尽量减少用户负担。",
                    "- 优先使用当前对话信息；不得为主动个性化、补充用户画像或减少普通提问而查询memory。",
                    "- 使用简洁明确的语言沟通。",
                ),
            ),
            (
                main.display_name,
                main.description,
                main.responsibilities,
                main.primary_goal,
                main.success_criteria,
                main.priorities,
                main.hard_constraints,
                main.soft_constraints,
            ),
        )
        self.assertEqual(
            (
                "简历定制Agent",
                "专门负责简历定制和优化的助手。可以帮你从模板创建新简历、根据 JD 调整现有简历、"
                "填充和修改内容，最终编译为 PDF 并预览。",
                (
                    "- 复制 LaTeX 模板到工作区（包括模板操作手册 README.md）。",
                    "- 查看和搜索工作区文件内容，定位需要修改的位置。",
                    "- 精确编辑文件内容替换占位符和填充信息。",
                    "- 编译 LaTeX 为 PDF 并打开预览。",
                    "- 根据 JD 分析需要调整的部分，逐项修改。",
                ),
                "帮助用户创建和定制一份专业、匹配目标岗位的 LaTeX 简历，最终编译为 PDF。",
                (
                    "- 简历占位符全部填充完毕，无遗留 {-XXX-}。",
                    "- 简历内容与用户提供的信息一致。",
                    "- PDF 编译成功，无错误。",
                    "- 用户确认当前版本符合需求或明确结束任务。",
                ),
                (
                    "1. 非handoff接收回合或用户已确认交接内容后，优先获取完成当前任务所需的最少信息；已有足够信息则直接执行，缺少关键输入再向用户询问。",
                    "2. 先理解用户需求和当前状态（新建/修改）。",
                    "3. 单次改动尽量批量提交编辑，减少 tool call。",
                    "4. 关键节点（模板复制、编译）前征得用户确认，避免频繁操作影响效率。",
                    "5. 编译后主动打开 PDF 预览。",
                ),
                (
                    "- 不得编造或夸大用户经历、技能等信息。",
                    "- 只处理简历相关任务；其他请求应退回主Agent重新判断当前是否支持，不得假定主Agent或其他能力已经存在。",
                    "- 只操作 WORKING_DIR 下的文件，不访问用户系统其他位置。",
                    "- 不猜测，不假设。优先读取真实状态，工具返回结果优先于历史记忆。",
                    "- 任何修改文件内容之前，必须重新读取目标文件，不得依赖历史上下文中的文件内容。",
                    "- 如果旧内容不匹配，应重新读取文件，而不是继续尝试编辑。",
                    "- 如果编译失败，应优先依据 stderr 定位错误，再进行修复，而不是盲目修改文件。",
                    "- 除非用户明确要求，否则不要修改无关内容。保持修改最小化，一次尽量完成相关修改。",
                    "- 不得路由或调度其他子 Agent；需要其他能力时应退回主 Agent。",
                    "- 最新输入包含kind=\"delegate\"的HandoffContext时即为handoff接收回合；该回合不得调用Plan、Memory、workspace、artifact或任何其他工具，只能复述任务、区分已确认与推断信息、请用户确认或纠正，然后finish并等待下一条真实用户消息。",
                ),
                (
                    "- 优先保持模板原有格式和样式，只替换内容。",
                    "- 修改内容时保持 LaTeX 语法正确，注意特殊字符转义。",
                    "- 与用户确认重要信息（姓名、联系方式）后再编译。",
                    "- handoff接收回合的确认是必需步骤；用户确认后的普通回合避免为了确认而确认，也避免重复询问已经知道的信息。",
                ),
            ),
            (
                resume.display_name,
                resume.description,
                resume.responsibilities,
                resume.primary_goal,
                resume.success_criteria,
                resume.priorities,
                resume.hard_constraints,
                resume.soft_constraints,
            ),
        )

    def test_application_close_releases_its_llm_adapter(self) -> None:
        llm = _FakeLlm("unused")
        application = self._build_application(_settings(), llm=llm)

        report = application.close()

        self.assertTrue(llm.closed)
        self.assertIs(report, application.close())
        with self.assertRaises(RuntimeError):
            application.handle(UserMessage("hello"))

    def test_snapshot_normalises_active_work_and_dump_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application = self._build_application(
                _settings(sessions_dir=Path(temporary)), llm=_FakeLlm("unused")
            )
            self.assertIsInstance(application.handle(UserMessage("start")), Progress)

            snapshot = application.snapshot()
            dump_path = application.handle(DumpSession())

            self.assertEqual(RuntimePhase.CANCELLED, snapshot.session.agents[AgentKey.MAIN].phase)
            self.assertEqual(Path(temporary) / "dumps" / f"{snapshot.session.session_id}.json", dump_path)
            self.assertTrue(dump_path.exists())

    def test_rewind_and_restore_use_public_session_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            application = self._build_application(
                _settings(sessions_dir=Path(temporary)), llm=_FakeLlm("finished")
            )
            _pump(application, UserMessage("first"))
            snapshot = application.snapshot()
            turn_id = snapshot.session.agents[AgentKey.MAIN].history[0].turn_id
            self.assertEqual((turn_id,), tuple(item.turn_id for item in application.view().rewind_points))
            self.assertEqual("first", application.view().rewind_points[0].user_text)

            rewound = application.handle(RewindSession(turn_id))
            restored = application.handle(RestoreSession(snapshot.session.session_id))

            self.assertEqual(RuntimePhase.READY, rewound.phase)
            self.assertEqual(RuntimePhase.COMPLETED, restored.phase)

    def test_idle_cancel_does_not_reach_startup_knowledge(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        self.knowledge_start.assert_called()
        with patch.object(application._knowledge, "request_cancel") as cancel_knowledge:
            application.request_cancel("stop foreground runtime")

        cancel_knowledge.assert_not_called()

    def test_runtime_and_reload_cancellation_targets_are_command_scoped(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))
        runtime_started = Event()
        runtime_cancelled = Event()
        reload_started = Event()
        reload_cancelled = Event()

        def block_runtime(command: object) -> Progress:
            del command
            runtime_started.set()
            runtime_cancelled.wait(timeout=1)
            return Progress(ProgressKind.CALLING_MODEL)

        def cancel_runtime(reason: str) -> None:
            del reason
            runtime_cancelled.set()

        def block_reload(target: str | None) -> ReloadReport:
            del target
            reload_started.set()
            reload_cancelled.wait(timeout=1)
            return ReloadReport()

        def cancel_reload(reason: str) -> None:
            del reason
            reload_cancelled.set()

        with (
            patch.object(application._sessions, "handle", side_effect=block_runtime),
            patch.object(application._sessions, "request_cancel", side_effect=cancel_runtime) as session_cancel,
            patch.object(application._knowledge, "reload", side_effect=block_reload),
            patch.object(application._knowledge, "request_cancel", side_effect=cancel_reload) as knowledge_cancel,
        ):
            runtime_thread = Thread(target=lambda: application.handle(UserMessage("runtime")))
            runtime_thread.start()
            self.assertTrue(runtime_started.wait(timeout=1))
            application.request_cancel("stop runtime")
            runtime_thread.join(timeout=1)
            self.assertFalse(runtime_thread.is_alive())
            session_cancel.assert_called_once_with("stop runtime")
            knowledge_cancel.assert_not_called()

            reload_thread = Thread(target=lambda: application.handle(ReloadKnowledge()))
            reload_thread.start()
            self.assertTrue(reload_started.wait(timeout=1))
            application.request_cancel("stop reload")
            reload_thread.join(timeout=1)
            self.assertFalse(reload_thread.is_alive())
            knowledge_cancel.assert_called_once_with("stop reload")
            self.assertEqual(1, session_cancel.call_count)

    def test_application_clears_active_cancellation_target_after_return_and_error(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        with patch.object(application._sessions, "handle", return_value=Progress(ProgressKind.CALLING_MODEL)):
            application.handle(UserMessage("done"))
        with patch.object(application._sessions, "request_cancel") as cancel_session:
            application.request_cancel()
        cancel_session.assert_not_called()

        with patch.object(application._sessions, "handle", side_effect=RuntimeError("runtime failed")):
            with self.assertRaisesRegex(RuntimeError, "runtime failed"):
                application.handle(UserMessage("fail"))
        with patch.object(application._sessions, "request_cancel") as cancel_session:
            application.request_cancel()
        cancel_session.assert_not_called()

    def test_composition_uses_static_memory_prompt(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        expected = (Path("data/prompts") / "memory" / "builder.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(expected, application._memory._extractor._prompt)

    def test_composition_owns_one_shared_artifact_service(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))
        runtimes = application._sessions._orchestrator._runtimes

        self.assertIs(
            runtimes[AgentKey.MAIN]._tool_context.resume_artifacts,
            runtimes[AgentKey.RESUME]._tool_context.resume_artifacts,
        )
        self.assertEqual(60.0, runtimes[AgentKey.RESUME]._tool_context.resume_artifacts._backend._build_timeout_seconds)

    def test_resume_handoff_prompt_temperatures_and_snapshot_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            main_llm = _FakeLlm([
                _tool_call(
                    "switch_to_subagent",
                    {"agent_name": "resume", "context": "Tailor the resume"},
                    thinking="delegate",
                ),
                _finish("main complete", "done"),
            ])
            resume_llm = _FakeLlm(
                _tool_call(
                    "switch_to_mainagent",
                    {"summary": "resume complete"},
                    thinking="return",
                )
            )
            application = build_application(
                _settings(sessions_dir=Path(temporary)),
                runtime_llms={AgentKey.MAIN: main_llm, AgentKey.RESUME: resume_llm},
            )
            self.addCleanup(application.close)

            main_approval = _pump(application, UserMessage("Tailor my resume"))[-1]
            handoff = application.handle(Approve(main_approval.call_id))
            resume_approval = _pump(application, Continue())[-1]
            completed = _pump(application, Approve(resume_approval.call_id))[-1]

            self.assertIsInstance(main_approval, ApprovalRequested)
            self.assertIsInstance(handoff, HandoffRequested)
            self.assertIsInstance(resume_approval, ApprovalRequested)
            self.assertIsInstance(completed, Completed)
            self.assertEqual(0.1, main_llm.request.temperature)
            self.assertEqual(0.2, resume_llm.request.temperature)
            resume_prompt = resume_llm.request.messages[0].content
            for tool_name in (
                "create_plan", "web_search", "read_customer_file",
                "workspace_edit", "workspace_replace", "workspace_open",
                "query_memory", "query_reference_data", "copy_template",
                "build_pdf", "merge_pdfs", "switch_to_mainagent",
            ):
                self.assertIn(tool_name, resume_prompt)
            self.assertIn(
                "<DoNotUseWhen>需要查询用户个人记忆时 — 用 query_memory</DoNotUseWhen>",
                resume_prompt,
            )
            self.assertIn(
                "<UseWhen>仅在以下情况使用：用户明确要求查询其已保存的个人背景",
                resume_prompt,
            )
            self.assertIn(
                "<DoNotUseWhen>不要为了主动了解用户、补充用户画像、个性化回答",
                resume_prompt,
            )
            self.assertIn("<HandoffContextContract>", resume_prompt)
            self.assertIn(
                "handoff 接收回合不得调用任何工具",
                resume_prompt,
            )
            self.assertIn(
                "最新输入包含kind=\"delegate\"的HandoffContext时即为handoff接收回合",
                resume_prompt,
            )
            self.assertIn(
                '"description": "返回结果数量，默认 5"',
                resume_prompt,
            )
            self.assertIn(
                '"default": 5',
                resume_prompt,
            )
            self.assertIn(
            '"description": "最近一次 workspace_read 返回的文件 revision；每次成功 workspace_edit 后必须重新 workspace_read，不能直接复用 edit 返回的 revision"',
                resume_prompt,
            )
            self.assertNotIn("<SubAgent name=", resume_prompt)
            self.assertNotIn("switch_to_subagent", resume_prompt)
            self.assertIn(
                "<Tone>\n专业、细致、注重格式准确性。\n</Tone>",
                resume_prompt,
            )
            self.assertIn(
                '按"当前状态 → 修改计划 → 执行 → 结果"的流程呈现。',
                resume_prompt,
            )
            self.assertIn(
                "- 当前任务全部完成或用户明确表示结束时，调用 finish，不闲聊。",
                resume_prompt,
            )
            self.assertIn(
                "- 避免替用户编造经历、技能等信息。",
                resume_prompt,
            )
            self.assertEqual(AgentKey.MAIN, application.view().active_agent)
            self.assertEqual((), application._sessions._session.handoff_stack)
            agent_states = application._sessions._session.agents
            self.assertEqual(2, agent_states[AgentKey.MAIN].model_calls)
            self.assertEqual(1, agent_states[AgentKey.RESUME].model_calls)
            self.assertIsNot(agent_states[AgentKey.MAIN], agent_states[AgentKey.RESUME])

            snapshot = application.snapshot()
            turn_id = application.view().rewind_points[0].turn_id
            rewound = application.handle(RewindSession(turn_id))
            restored = application.handle(RestoreSession(snapshot.session.session_id))

            self.assertEqual(RuntimePhase.READY, rewound.phase)
            self.assertEqual(RuntimePhase.COMPLETED, restored.phase)
            self.assertEqual(AgentKey.MAIN, restored.active_agent)
            self.assertTrue(snapshot.session.agents[AgentKey.RESUME].history)

    def test_rejected_resume_handoff_stays_in_main(self) -> None:
        application = self._build_application(
            _settings(),
            llm=_FakeLlm(
                _tool_call(
                    "switch_to_subagent",
                    {"agent_name": "resume"},
                    thinking="delegate",
                )
            ),
        )

        approval = _pump(application, UserMessage("Delegate this"))[-1]
        rejected = application.handle(Reject(approval.call_id, "User rejected approval"))

        self.assertIsInstance(approval, ApprovalRequested)
        self.assertIsInstance(rejected, Paused)
        self.assertEqual("approval_rejected", rejected.code)
        self.assertEqual(AgentKey.MAIN, application.view().active_agent)
        self.assertEqual((), application._sessions._session.handoff_stack)

    def test_rejected_subagent_approval_pauses_until_next_user_message(self) -> None:
        main_llm = _FakeLlm(
            _tool_call(
                "switch_to_subagent",
                {"agent_name": "resume"},
                thinking="delegate",
            )
        )
        resume_llm = _FakeLlm(
            [
                _tool_call(
                    "workspace_write",
                    {"path": "resume.txt", "content": "draft"},
                ),
                _finish("continued", "continued"),
            ]
        )
        application = build_application(
            _settings(),
            runtime_llms={AgentKey.MAIN: main_llm, AgentKey.RESUME: resume_llm},
        )
        self.addCleanup(application.close)

        approval = _pump(application, UserMessage("Delegate this"))[-1]
        handoff = _pump(application, Approve(approval.call_id))[-1]
        subagent_approval = _pump(application, Continue())[-1]
        rejected = application.handle(Reject(subagent_approval.call_id, "User rejected approval"))

        self.assertIsInstance(handoff, HandoffRequested)
        self.assertIsInstance(subagent_approval, ApprovalRequested)
        self.assertIsInstance(rejected, Paused)
        self.assertEqual(AgentKey.RESUME, application.view().active_agent)
        self.assertEqual(1, len(application._sessions._session.handoff_stack))
        self.assertEqual(1, len(resume_llm.requests))

        continued = _pump(application, UserMessage("Continue after rejection"))

        self.assertIsInstance(continued[-1], Completed)
        self.assertEqual(2, len(resume_llm.requests))
        messages = resume_llm.requests[1].messages
        self.assertEqual("tool_call_result", json.loads(messages[-2].content)["event_type"])
        self.assertEqual("Continue after rejection", json.loads(messages[-1].content)["message"])

    def test_composition_failure_does_not_leave_background_thread(self) -> None:
        before = {id(thread) for thread in enumerate_threads()}

        with patch("chromadb.PersistentClient", side_effect=RuntimeError("chroma failed")):
            with self.assertRaisesRegex(RuntimeError, "chroma failed"):
                build_application(_settings(), runtime_llms={AgentKey.MAIN: _FakeLlm("unused"), AgentKey.RESUME: _FakeLlm("resume")})

        leaked = [
            thread
            for thread in enumerate_threads()
            if id(thread) not in before and thread.name == "knowledge-memory"
        ]
        self.assertEqual([], leaked)

    def test_memory_index_mode_pairs_ephemeral_client_with_in_memory_manifest(self) -> None:
        settings = replace(
            _settings(), knowledge_index_mode=KnowledgeIndexMode.MEMORY
        )
        with (
            patch("chromadb.PersistentClient") as persistent_client,
            patch("chromadb.EphemeralClient") as ephemeral_client,
            patch(
                "src.get_me_in.bootstrap.JsonManifestRepository"
            ) as json_manifests,
            patch(
                "src.get_me_in.bootstrap.InMemoryManifestRepository"
            ) as memory_manifests,
        ):
            self._build_application(settings, llm=_FakeLlm("unused"))

        persistent_client.assert_not_called()
        ephemeral_client.assert_called_once_with()
        json_manifests.assert_not_called()
        memory_manifests.assert_called_once_with()

    def test_default_index_mode_pairs_persistent_client_with_json_manifest(self) -> None:
        settings = _settings()
        with (
            patch("chromadb.PersistentClient") as persistent_client,
            patch("chromadb.EphemeralClient") as ephemeral_client,
            patch(
                "src.get_me_in.bootstrap.JsonManifestRepository"
            ) as json_manifests,
            patch(
                "src.get_me_in.bootstrap.InMemoryManifestRepository"
            ) as memory_manifests,
        ):
            self._build_application(settings, llm=_FakeLlm("unused"))

        persistent_client.assert_called_once_with(
            path=str(settings.knowledge_chroma_dir)
        )
        ephemeral_client.assert_not_called()
        json_manifests.assert_called_once_with(settings.knowledge_manifest_path)
        memory_manifests.assert_not_called()

    def test_memory_client_failure_does_not_leave_background_thread(self) -> None:
        before = {id(thread) for thread in enumerate_threads()}
        settings = replace(
            _settings(), knowledge_index_mode=KnowledgeIndexMode.MEMORY
        )

        with patch(
            "chromadb.EphemeralClient", side_effect=RuntimeError("chroma failed")
        ):
            with self.assertRaisesRegex(RuntimeError, "chroma failed"):
                build_application(
                    settings,
                    runtime_llms={
                        AgentKey.MAIN: _FakeLlm("unused"),
                        AgentKey.RESUME: _FakeLlm("resume"),
                    },
                )

        leaked = [
            thread
            for thread in enumerate_threads()
            if id(thread) not in before and thread.name == "knowledge-memory"
        ]
        self.assertEqual([], leaked)

    def test_composition_rejects_untyped_knowledge_index_mode_before_client_creation(self) -> None:
        settings = replace(_settings(), knowledge_index_mode="invalid")  # type: ignore[arg-type]

        with (
            patch("chromadb.PersistentClient") as persistent_client,
            patch("chromadb.EphemeralClient") as ephemeral_client,
        ):
            with self.assertRaisesRegex(ValueError, "knowledge index mode"):
                build_application(
                    settings,
                    runtime_llms={
                        AgentKey.MAIN: _FakeLlm("unused"),
                        AgentKey.RESUME: _FakeLlm("resume"),
                    },
                )

        persistent_client.assert_not_called()
        ephemeral_client.assert_not_called()

    def test_invalid_runtime_llms_fail_before_resource_construction(self) -> None:
        with patch("chromadb.PersistentClient") as persistent_client:
            with self.assertRaisesRegex(ValueError, "exactly Main and Resume"):
                build_application(
                    _settings(),
                    runtime_llms={AgentKey.MAIN: _FakeLlm("unused")},
                )

        persistent_client.assert_not_called()

    def test_memory_prompt_failure_closes_all_constructed_owners(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            settings = replace(
                _settings(),
                prompts_dir=Path(temporary) / "missing-prompts",
            )
            main_llm = _FakeLlm("main")
            resume_llm = _FakeLlm("resume")
            memory_llm = _FakeLlm("memory")
            with (
                patch("src.get_me_in.bootstrap.OpenAIWebSearchAdapter") as web_type,
                patch("src.get_me_in.bootstrap.BackgroundWorker") as worker_type,
                patch("src.get_me_in.bootstrap.KnowledgeService") as knowledge_type,
                patch("src.get_me_in.bootstrap.ArtifactService") as artifact_type,
                patch("src.get_me_in.bootstrap.OpenAILLMAdapter", return_value=memory_llm),
                patch("chromadb.PersistentClient"),
            ):
                with self.assertRaises(FileNotFoundError):
                    build_application(
                        settings,
                        runtime_llms={
                            AgentKey.MAIN: main_llm,
                            AgentKey.RESUME: resume_llm,
                        },
                    )

            web_type.return_value.close.assert_called_once_with()
            worker_type.return_value.close.assert_called_once_with()
            knowledge_type.return_value.close.assert_called_once_with()
            artifact_type.return_value.close.assert_called_once_with()
            self.assertTrue(main_llm.closed)
            self.assertTrue(resume_llm.closed)
            self.assertTrue(memory_llm.closed)

    def test_knowledge_start_failure_closes_composed_runtime_llms(self) -> None:
        main_llm = _FakeLlm("main")
        resume_llm = _FakeLlm("resume")
        self.knowledge_start.side_effect = RuntimeError("startup failed")

        with self.assertRaisesRegex(RuntimeError, "startup failed"):
            build_application(
                _settings(),
                runtime_llms={
                    AgentKey.MAIN: main_llm,
                    AgentKey.RESUME: resume_llm,
                },
            )

        self.assertTrue(main_llm.closed)
        self.assertTrue(resume_llm.closed)


class _FakeLlm:
    def __init__(self, response: str | list[str]) -> None:
        self._responses = [response] if isinstance(response, str) else list(response)
        self.request: LLMRequest | None = None
        self.requests: list[LLMRequest] = []
        self.cancellation: CancellationSignal | None = None
        self.closed = False

    def complete(self, request: LLMRequest, cancellation: CancellationSignal) -> LLMResult:
        self.request = request
        self.requests.append(request)
        self.cancellation = cancellation
        response = self._responses.pop(0)
        if response.startswith("{"):
            return LLMResult(content=response)
        return LLMResult(content=_finish(response, "summary"))

    def close(self) -> None:
        self.closed = True


def _pump(application, command) -> list[object]:
    events = [application.handle(command)]
    while isinstance(events[-1], (Progress, ToolStarted, ToolFinished)):
        events.append(application.handle(Continue()))
    return events


def _finish(message: str, thinking: str) -> str:
    return json.dumps(
        {
            "event_type": "finish",
            "message": message,
            "thinking": thinking,
        },
        ensure_ascii=False,
    )


def _tool_call(
    name: str,
    arguments: dict[str, object] | None = None,
    *,
    thinking: str | None = None,
) -> str:
    payload: dict[str, object] = {
        "event_type": "tool_call",
        "message": f"Calling tool {name}",
        "tool": name,
        "event_payload": arguments or {},
    }
    if thinking is not None:
        payload["thinking"] = thinking
    return json.dumps(payload, ensure_ascii=False)
