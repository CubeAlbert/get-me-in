import unittest
from pathlib import Path

from src.get_me_in.application.settings import Settings, SettingsValidationError


class SettingsTests(unittest.TestCase):
    def test_from_env_builds_typed_static_asset_paths(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LLM_TIMEOUT": "12.5",
            },
            project_root=Path("project"),
        )

        self.assertEqual(12.5, settings.llm_timeout_seconds)
        self.assertTrue(settings.llm_thinking_enabled)
        self.assertEqual(Path("project/data/prompts"), settings.prompts_dir)

    def test_from_env_parses_thinking_setting(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LLM_THINKING_ENABLED": "false",
            },
            project_root=Path("project"),
        )

        self.assertFalse(settings.llm_thinking_enabled)

    def test_from_env_reports_missing_required_values(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "OPENAI_API_KEY"):
            Settings.from_env({}, project_root=Path("project"))
