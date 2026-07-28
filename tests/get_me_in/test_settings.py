import unittest
from pathlib import Path

from src.get_me_in.application.settings import Settings, SettingsValidationError


class SettingsTests(unittest.TestCase):
    def test_example_configuration_documents_v2_settings_and_legacy_rollback(self) -> None:
        example = (Path(__file__).resolve().parents[2] / ".env.example").read_text(
            encoding="utf-8"
        )

        for name in (
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "LLM_PRO_MODEL",
            "LLM_FLASH_MODEL",
            "LLM_TIMEOUT",
            "AGENT_MAX_MODEL_CALLS",
            "WORKSPACE_DIR",
            "SESSIONS_DIR",
            "ARTIFACTS_DIR",
            "EMBEDDING_MODEL",
            "RERANKER_MODEL",
            "PDF_BUILD_TIMEOUT_SECONDS",
            "ARTIFACT_LOG_MAX_BYTES",
        ):
            self.assertIn(name, example)
        self.assertIn("legacy rollback only", example)
        self.assertIn("AGENT_MAX_MODEL_CALLS=100", example)
        self.assertIn("AGENT_MAX_ROUNDS", example)

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
        self.assertEqual(Path("project/data/logs"), settings.log_dir)
        self.assertEqual("INFO", settings.log_level)
        self.assertEqual("BAAI/bge-base-zh-v1.5", settings.embedding_model)
        self.assertEqual("BAAI/bge-reranker-v2-m3", settings.reranker_model)
        self.assertEqual(Path("project/data/v2/artifacts"), settings.artifacts_dir)
        self.assertEqual(60.0, settings.pdf_build_timeout_seconds)
        self.assertEqual(65536, settings.artifact_log_max_bytes)

    def test_from_env_defaults_model_call_limit_to_100(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
            },
            project_root=Path("project"),
        )

        self.assertEqual(100, settings.max_model_calls_per_run)

    def test_from_env_validates_artifact_settings(self) -> None:
        env = {
            "OPENAI_API_KEY": "key", "OPENAI_BASE_URL": "https://example.test",
            "LLM_PRO_MODEL": "pro", "LLM_FLASH_MODEL": "flash",
            "PDF_BUILD_TIMEOUT_SECONDS": "12.5", "ARTIFACT_LOG_MAX_BYTES": "1024",
        }
        settings = Settings.from_env(env, project_root=Path("project"))
        self.assertEqual(12.5, settings.pdf_build_timeout_seconds)
        self.assertEqual(1024, settings.artifact_log_max_bytes)
        for name, value in (("PDF_BUILD_TIMEOUT_SECONDS", "0"), ("ARTIFACT_LOG_MAX_BYTES", "0")):
            invalid = {**env, name: value}
            with self.assertRaises(SettingsValidationError):
                Settings.from_env(invalid, project_root=Path("project"))

    def test_from_env_accepts_legacy_rag_model_names_through_typed_settings(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "BI_ENCODER_MODEL": "legacy-embedder",
                "CROSS_ENCODER_MODEL": "legacy-reranker",
                "EMBED_BATCH_SIZE": "7",
            },
            project_root=Path("project"),
        )

        self.assertEqual("legacy-embedder", settings.embedding_model)
        self.assertEqual("legacy-reranker", settings.reranker_model)
        self.assertEqual(7, settings.embedding_batch_size)

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

    def test_from_env_never_uses_legacy_runtime_data_paths(self) -> None:
        root = Path("sentinel-project-root")
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "CHROMA_PERSIST_DIR": "data/chroma",
                "MEMORIES_BASE_DIR": "data/memories",
                "WORKING_DIR": "data/temp",
                "SAVE_DIR": "data/save",
            },
            project_root=root,
        )

        self.assertEqual(root / "data" / "workspace", settings.workspace_dir)
        self.assertEqual(root / "data" / "v2" / "sessions", settings.sessions_dir)
        self.assertEqual(root / "data" / "v2" / "knowledge" / "chroma", settings.knowledge_chroma_dir)
        self.assertEqual(root / "data" / "v2" / "memories", settings.memories_dir)
        self.assertEqual(root / "data" / "v2" / "artifacts", settings.artifacts_dir)

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

    def test_from_env_parses_logging_settings(self) -> None:
        settings = Settings.from_env(
            {
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LOG_DIR": "runtime-logs",
                "LOG_LEVEL": "debug",
            },
            project_root=Path("project"),
        )

        self.assertEqual(Path("project/runtime-logs"), settings.log_dir)
        self.assertEqual("DEBUG", settings.log_level)

    def test_from_env_rejects_invalid_log_level(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "LOG_LEVEL"):
            Settings.from_env(
                {
                    "OPENAI_API_KEY": "key",
                    "OPENAI_BASE_URL": "https://example.test",
                    "LLM_PRO_MODEL": "pro",
                    "LLM_FLASH_MODEL": "flash",
                    "LOG_LEVEL": "verbose",
                },
                project_root=Path("project"),
            )

    def test_from_env_reports_missing_required_values(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "OPENAI_API_KEY"):
            Settings.from_env({}, project_root=Path("project"))
