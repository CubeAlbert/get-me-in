import unittest
from pathlib import Path

from src.get_me_in.bootstrap import build_application
from src.get_me_in.application.settings import Settings
from src.get_me_in.domain.agents import AgentKey


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
    def test_applications_do_not_share_cancellation_or_catalog_state(self) -> None:
        first = build_application(_settings())
        second = build_application(_settings())

        first.cancellation.cancel()

        self.assertTrue(first.cancellation.is_cancelled)
        self.assertFalse(second.cancellation.is_cancelled)
        self.assertIsNot(first.catalog, second.catalog)
        self.assertEqual(AgentKey.MAIN, second.catalog.get(AgentKey.MAIN).key)
