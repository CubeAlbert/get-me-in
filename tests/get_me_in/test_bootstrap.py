import unittest
from dataclasses import replace
from pathlib import Path
import tempfile
from threading import enumerate as enumerate_threads
from unittest.mock import patch

from src.get_me_in.bootstrap import build_application
from src.get_me_in.application.commands import Approve, Continue, Reject, UserMessage
from src.get_me_in.application.app_commands import DumpSession, RestoreSession, RewindSession
from src.get_me_in.application.events import ApprovalRequested, Cancelled, Completed, HandoffRequested, Progress, ToolFinished, ToolStarted
from src.get_me_in.application.settings import Settings
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.sessions import RuntimePhase
from src.get_me_in.ports.llm import CancellationSignal, LLMRequest, LLMResult


def _settings(*, sessions_dir: Path = Path("data/v2/sessions")) -> Settings:
    return Settings(
        openai_api_key="key",
        openai_base_url="https://example.test",
        llm_pro_model="pro",
        llm_flash_model="flash",
        llm_timeout_seconds=60,
        llm_thinking_enabled=True,
        hf_endpoint=None,
        reference_dir=Path("data/reference"),
        prompts_dir=Path("data/prompts"),
        resume_template_dir=Path("data/resume/template"),
        workspace_dir=Path("data/workspace"),
        sessions_dir=sessions_dir,
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

        self.assertTrue(first._sessions._orchestrator._runtimes[AgentKey.MAIN]._cancellation.is_cancelled)
        self.assertFalse(second._sessions._orchestrator._runtimes[AgentKey.MAIN]._cancellation.is_cancelled)
        self.assertIsNot(first.catalog, second.catalog)
        self.assertIsNot(first.clock, second.clock)
        self.assertIsNot(first.id_generator, second.id_generator)
        self.assertEqual({AgentKey.MAIN, AgentKey.RESUME}, {item.key for item in second.catalog.list_descriptors()})

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
            '"description": "搜索查询，使用自然语言或关键词"',
            llm.request.messages[0].content,
        )
        self.assertIn(
            '<SubAgent name="resume">',
            llm.request.messages[0].content,
        )
        self.assertIn(
            "<Name>简历定制 Agent</Name>",
            llm.request.messages[0].content,
        )
        self.assertNotIn("workspace_write", llm.request.messages[0].content)
        self.assertNotIn("copy_template", llm.request.messages[0].content)
        self.assertFalse(llm.cancellation.is_cancelled)

    def test_application_executes_its_explicit_system_tool_catalog(self) -> None:
        application = self._build_application(
            _settings(),
            llm=_FakeLlm(
                [
                    '{"content": "", "tool_call": {"name": "get_current_datetime"}}',
                    '{"content": "done", "thinking": "done"}',
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

        self.assertEqual(25, len(names))
        self.assertEqual(
            {
                "get_current_datetime", "get_working_dir", "web_search",
                "switch_to_subagent", "switch_to_mainagent", "provide_choices",
                "create_plan", "update_plan_status", "cancel_all_plans", "replan",
                "workspace_read", "workspace_list", "workspace_grep", "workspace_search_file",
                "workspace_replace", "workspace_write", "workspace_delete", "workspace_move",
                "workspace_edit", "workspace_open", "read_customer_file", "query_memory",
                "query_reference_data", "copy_template", "build_pdf",
            },
            set(names),
        )

    def test_main_agent_cannot_see_workspace_or_resume_tools(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))
        main = application.catalog.get(AgentKey.MAIN)

        names = {
            tool.name
            for tool in application.tool_catalog.list_for_capabilities(main.capabilities)
        }

        self.assertIn("switch_to_subagent", names)
        self.assertNotIn("workspace_read", names)
        self.assertNotIn("copy_template", names)
        self.assertNotIn("switch_to_mainagent", names)

    def test_every_production_tool_declares_capabilities(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        missing = [
            item["name"]
            for item in application.tool_catalog.export_descriptors()
            if not item["required_capabilities"]
        ]

        self.assertEqual([], missing)

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

    def test_composition_starts_knowledge_and_cancel_reaches_it(self) -> None:
        application = self._build_application(_settings(), llm=_FakeLlm("unused"))

        self.knowledge_start.assert_called()
        with patch.object(application._knowledge, "request_cancel") as cancel_knowledge:
            application.request_cancel("stop reload")

        cancel_knowledge.assert_called_once_with("stop reload")

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
                '{"content":"","thinking":"delegate","tool_call":{"name":"switch_to_subagent","arguments":{"agent_name":"resume","context":"Tailor the resume"}}}',
                '{"content":"main complete","thinking":"done"}',
            ])
            resume_llm = _FakeLlm(
                '{"content":"","thinking":"return","tool_call":{"name":"switch_to_mainagent","arguments":{"summary":"resume complete"}}}'
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
                "build_pdf", "switch_to_mainagent",
            ):
                self.assertIn(tool_name, resume_prompt)
            self.assertIn(
                "<DoNotUseWhen>需要查询用户个人记忆时 — 用 query_memory</DoNotUseWhen>",
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
                '"description": "最近一次 workspace_read 返回的文件 revision；文件变化后旧 revision 会被拒绝"',
                resume_prompt,
            )
            self.assertNotIn("<SubAgent name=", resume_prompt)
            self.assertNotIn("switch_to_subagent", resume_prompt)
            self.assertEqual(AgentKey.MAIN, application.view().active_agent)
            self.assertEqual((), application._sessions._session.handoff_stack)

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
                '{"content":"","thinking":"delegate","tool_call":{"name":"switch_to_subagent","arguments":{"agent_name":"resume"}}}'
            ),
        )

        approval = _pump(application, UserMessage("Delegate this"))[-1]
        rejected = application.handle(Reject(approval.call_id, "User rejected approval"))

        self.assertIsInstance(approval, ApprovalRequested)
        self.assertIsInstance(rejected, Cancelled)
        self.assertEqual(AgentKey.MAIN, application.view().active_agent)
        self.assertEqual((), application._sessions._session.handoff_stack)

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
        self.cancellation: CancellationSignal | None = None
        self.closed = False

    def complete(self, request: LLMRequest, cancellation: CancellationSignal) -> LLMResult:
        self.request = request
        self.cancellation = cancellation
        response = self._responses.pop(0)
        if response.startswith("{"):
            return LLMResult(content=response)
        return LLMResult(content=f'{{"content": "{response}", "thinking": "summary"}}')

    def close(self) -> None:
        self.closed = True


def _pump(application, command) -> list[object]:
    events = [application.handle(command)]
    while isinstance(events[-1], (Progress, ToolStarted, ToolFinished)):
        events.append(application.handle(Continue()))
    return events
