import unittest
from pathlib import Path

from src.get_me_in.bootstrap import build_application
from src.get_me_in.application.commands import UserMessage
from src.get_me_in.application.events import Completed
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
        hf_endpoint=None,
        reference_dir=Path("data/reference"),
        prompts_dir=Path("data/prompts"),
        resume_template_dir=Path("data/resume/template"),
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

    def test_application_close_releases_its_llm_adapter(self) -> None:
        llm = _FakeLlm("unused")
        application = build_application(_settings(), llm=llm)

        application.close()

        self.assertTrue(llm.closed)
        with self.assertRaises(RuntimeError):
            application.handle(UserMessage("hello"))


class _FakeLlm:
    def __init__(self, response: str) -> None:
        self._response = response
        self.request: LLMRequest | None = None
        self.cancellation: CancellationSignal | None = None
        self.closed = False

    def complete(self, request: LLMRequest, cancellation: CancellationSignal) -> LLMResult:
        self.request = request
        self.cancellation = cancellation
        return LLMResult(content=f'{{"content": "{self._response}"}}')

    def close(self) -> None:
        self.closed = True
