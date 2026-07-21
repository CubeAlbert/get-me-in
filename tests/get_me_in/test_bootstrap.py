import unittest
from pathlib import Path

from src.get_me_in.bootstrap import build_application
from src.get_me_in.application.application import TemporaryConversationUnavailableError
from src.get_me_in.application.settings import Settings
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.ports.llm import CancellationSignal


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
        first = build_application(_settings())
        second = build_application(_settings())

        first.cancellation.cancel()

        self.assertTrue(first.cancellation.is_cancelled)
        self.assertFalse(second.cancellation.is_cancelled)
        self.assertIsNot(first.catalog, second.catalog)
        self.assertIsNot(first.prompt_renderer, second.prompt_renderer)
        self.assertIsNot(first.clock, second.clock)
        self.assertIsNot(first.id_generator, second.id_generator)
        self.assertEqual(AgentKey.MAIN, second.catalog.get(AgentKey.MAIN).key)

    def test_complete_text_runs_one_temporary_no_tool_conversation(self) -> None:
        llm = _FakeLlm("completed")
        application = build_application(_settings(), llm=llm)

        result = application.complete_text("Help me prepare for an interview")

        self.assertEqual("completed", result)
        self.assertIn("Help me prepare for an interview", llm.prompt)
        self.assertFalse(llm.cancellation.is_cancelled)

    def test_complete_text_requires_explicit_llm_injection(self) -> None:
        application = build_application(_settings())

        with self.assertRaises(TemporaryConversationUnavailableError):
            application.complete_text("hello")


class _FakeLlm:
    def __init__(self, response: str) -> None:
        self._response = response
        self.prompt = ""
        self.cancellation: CancellationSignal | None = None

    def complete(self, prompt: str, cancellation: CancellationSignal) -> str:
        self.prompt = prompt
        self.cancellation = cancellation
        return self._response
