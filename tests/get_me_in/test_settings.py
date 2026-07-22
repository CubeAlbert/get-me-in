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
                "AGENT_MAX_MODEL_CALLS": "9",
                "CANCEL_GRACE_SECONDS": "1.5",
            },
            project_root=Path("project"),
        )

        self.assertEqual(12.5, settings.llm_timeout_seconds)
        self.assertEqual(9, settings.max_model_calls_per_run)
        self.assertEqual(1.5, settings.cancel_grace_seconds)
        self.assertTrue(settings.llm_thinking_enabled)
        self.assertFalse(settings.show_thinking)
        self.assertEqual(Path("project/data/prompts"), settings.prompts_dir)
        self.assertEqual(Path("project/data/workspace"), settings.workspace_dir)

    def test_from_env_accepts_a_workspace_override(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "WORKSPACE_DIR": "custom-workspace",
            },
            project_root=Path("project"),
        )

        self.assertEqual(Path("custom-workspace"), settings.workspace_dir)

    def test_from_env_parses_thinking_setting(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LLM_THINKING_ENABLED": "false",
                "SHOW_THINKING": "true",
            },
            project_root=Path("project"),
        )

        self.assertFalse(settings.llm_thinking_enabled)
        self.assertTrue(settings.show_thinking)

    def test_from_env_rejects_invalid_show_thinking(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "SHOW_THINKING"):
            Settings.from_env(
                {
                    "OPENAI_API_KEY": "key",
                    "OPENAI_BASE_URL": "https://example.test",
                    "LLM_PRO_MODEL": "pro",
                    "LLM_FLASH_MODEL": "flash",
                    "SHOW_THINKING": "sometimes",
                },
                project_root=Path("project"),
            )

    def test_from_env_reports_missing_required_values(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "OPENAI_API_KEY"):
            Settings.from_env({}, project_root=Path("project"))
