import unittest
from pathlib import Path

from src.get_me_in.bootstrap import build_application
from src.get_me_in.application.commands import UserMessage
from src.get_me_in.application.events import Completed, ToolFinished
from src.get_me_in.application.settings import Settings
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.ports.llm import CancellationSignal, LLMRequest, LLMResult


def _settings() -> Settings:
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
    )


class BootstrapTests(unittest.TestCase):
    def test_applications_do_not_share_mutable_runtime_dependencies(self) -> None:
        first = build_application(_settings(), llm=_FakeLlm("first"))
        second = build_application(_settings(), llm=_FakeLlm("second"))

        first.cancellation.cancel()

        self.assertTrue(first.cancellation.is_cancelled)
        self.assertFalse(second.cancellation.is_cancelled)
        self.assertIsNot(first.catalog, second.catalog)
        self.assertIsNot(first.clock, second.clock)
        self.assertIsNot(first.id_generator, second.id_generator)
        self.assertEqual(AgentKey.MAIN, second.catalog.get(AgentKey.MAIN).key)

    def test_application_handles_one_no_tool_conversation(self) -> None:
        llm = _FakeLlm("completed")
        application = build_application(_settings(), llm=llm)

        events = application.handle(UserMessage("Help me prepare for an interview"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("completed", events[-1].message.content)
        self.assertIn("Help me prepare for an interview", llm.request.messages[-1].content)
        self.assertFalse(llm.cancellation.is_cancelled)

    def test_application_executes_its_explicit_system_tool_catalog(self) -> None:
        application = build_application(
            _settings(),
            llm=_FakeLlm(
                [
                    '{"content": "", "tool_call": {"name": "get_current_datetime"}}',
                    '{"content": "done"}',
                ]
            ),
        )

        events = application.handle(UserMessage("What time is it?"))

        self.assertTrue(any(isinstance(event, ToolFinished) for event in events))
        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("done", events[-1].message.content)

    def test_application_exposes_the_complete_explicit_tool_catalog(self) -> None:
        application = build_application(_settings(), llm=_FakeLlm("unused"))

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

    def test_application_close_releases_its_llm_adapter(self) -> None:
        llm = _FakeLlm("unused")
        application = build_application(_settings(), llm=llm)

        application.close()

        self.assertTrue(llm.closed)
        with self.assertRaises(RuntimeError):
            application.handle(UserMessage("hello"))


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
        return LLMResult(content=f'{{"content": "{response}"}}')

    def close(self) -> None:
        self.closed = True
