import unittest
from pathlib import Path

from src.get_me_in.application.settings import (
    KnowledgeIndexMode,
    Settings,
    SettingsValidationError,
)
from src.get_me_in.application.localization import Locale
from src.get_me_in.ports.llm import ModelProfile


_BASE_ENV = {
    "OPENAI_API_KEY": "key",
    "OPENAI_BASE_URL": "https://example.test",
    "LLM_PRO_MODEL": "pro",
    "LLM_FLASH_MODEL": "flash",
    "MAIN_MODEL_PROFILE": "pro",
    "RESUME_MODEL_PROFILE": "pro",
    "MEMORY_MODEL_PROFILE": "flash",
    "WEB_SEARCH_MODEL_PROFILE": "pro",
    "MAIN_TEMPERATURE": "0.1",
    "RESUME_TEMPERATURE": "0.2",
    "MEMORY_TEMPERATURE": "0.0",
    "LLM_TIMEOUT": "60",
    "LLM_THINKING_ENABLED": "true",
    "SHOW_THINKING": "false",
    "UI_LOCALE": "zh-CN",
    "MODEL_RESPONSE_LANGUAGE": "ui",
    "AGENT_MAX_MODEL_CALLS": "100",
    "CANCEL_GRACE_SECONDS": "2",
    "SHUTDOWN_TIMEOUT_SECONDS": "60",
    "AUTO_MEMORY_ON_EXIT": "false",
    "REFERENCE_DIR": "data/reference",
    "PROMPTS_DIR": "data/prompts",
    "RESUME_TEMPLATE_DIR": "data/resume/template",
    "LOCALES_DIR": "data/locales",
    "WORKSPACE_DIR": "data/workspace",
    "SESSIONS_DIR": "data/runtime/sessions",
    "ARTIFACTS_DIR": "data/runtime/artifacts",
    "LOG_DIR": "data/logs",
    "LOG_LEVEL": "INFO",
    "KNOWLEDGE_INDEX_MODE": "persistent",
    "KNOWLEDGE_MANIFEST_PATH": "data/runtime/knowledge/manifest.json",
    "KNOWLEDGE_CHROMA_DIR": "data/runtime/knowledge/chroma",
    "MEMORIES_DIR": "data/runtime/memories",
    "EMBEDDING_MODEL": "BAAI/bge-base-zh-v1.5",
    "RERANKER_MODEL": "BAAI/bge-reranker-v2-m3",
    "EMBEDDING_BATCH_SIZE": "32",
    "RERANK_BATCH_SIZE": "32",
    "RETRIEVAL_TOP_K": "8",
    "HF_ENDPOINT": "https://hf-mirror.com",
    "PDF_BUILD_TIMEOUT_SECONDS": "60",
    "ARTIFACT_LOG_MAX_BYTES": "65536",
    "MODEL_FORMAT_REPAIR_LIMIT": "3",
    "WEB_SEARCH_MAX_TOKENS": "4096",
    "LOG_FILE_NAME": "app.log",
    "LOG_MAX_BYTES": "10485760",
    "LOG_BACKUP_COUNT": "5",
    "CLI_WORKER_POLL_INTERVAL_SECONDS": "0.1",
    "SUBPROCESS_POLL_INTERVAL_SECONDS": "0.05",
    "CLI_RESULT_PREVIEW_CHARS": "500",
    "CLI_ARGUMENT_PREVIEW_CHARS": "160",
    "SESSION_PREVIEW_CHARS": "80",
    "WORKSPACE_READ_DEFAULT_LIMIT": "100",
    "WORKSPACE_SEARCH_MAX_MATCHES": "50",
    "WORKSPACE_FILE_SEARCH_MAX_RESULTS": "50",
    "CUSTOMER_FILE_READ_DEFAULT_LIMIT": "100",
    "RETRIEVAL_DEFAULT_TOP_K": "5",
    "HF_HUB_DISABLE_PROGRESS_BARS": "1",
    "TQDM_DISABLE": "1",
    "TRANSFORMERS_VERBOSITY": "error",
    "MODEL_LIBRARY_LOG_LEVEL": "ERROR",
}


def _env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    values = dict(_BASE_ENV)
    values.update(overrides or {})
    return values


class SettingsTests(unittest.TestCase):
    def test_example_configuration_documents_current_settings(self) -> None:
        example = (Path(__file__).resolve().parents[2] / ".env.example").read_text(
            encoding="utf-8"
        )

        for name in (
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "LLM_PRO_MODEL",
            "LLM_FLASH_MODEL",
            "MAIN_MODEL_PROFILE",
            "RESUME_MODEL_PROFILE",
            "MEMORY_MODEL_PROFILE",
            "WEB_SEARCH_MODEL_PROFILE",
            "MAIN_TEMPERATURE",
            "RESUME_TEMPERATURE",
            "MEMORY_TEMPERATURE",
            "LLM_TIMEOUT",
            "UI_LOCALE",
            "MODEL_RESPONSE_LANGUAGE",
            "AGENT_MAX_MODEL_CALLS",
            "REFERENCE_DIR",
            "PROMPTS_DIR",
            "RESUME_TEMPLATE_DIR",
            "LOCALES_DIR",
            "WORKSPACE_DIR",
            "SESSIONS_DIR",
            "ARTIFACTS_DIR",
            "LOG_DIR",
            "KNOWLEDGE_INDEX_MODE",
            "KNOWLEDGE_MANIFEST_PATH",
            "KNOWLEDGE_CHROMA_DIR",
            "MEMORIES_DIR",
            "EMBEDDING_MODEL",
            "RERANKER_MODEL",
            "PDF_BUILD_TIMEOUT_SECONDS",
            "ARTIFACT_LOG_MAX_BYTES",
            "SHUTDOWN_TIMEOUT_SECONDS",
            "MODEL_FORMAT_REPAIR_LIMIT",
            "WEB_SEARCH_MAX_TOKENS",
            "LOG_FILE_NAME",
            "LOG_MAX_BYTES",
            "LOG_BACKUP_COUNT",
            "CLI_WORKER_POLL_INTERVAL_SECONDS",
            "SUBPROCESS_POLL_INTERVAL_SECONDS",
            "CLI_RESULT_PREVIEW_CHARS",
            "CLI_ARGUMENT_PREVIEW_CHARS",
            "SESSION_PREVIEW_CHARS",
            "WORKSPACE_READ_DEFAULT_LIMIT",
            "WORKSPACE_SEARCH_MAX_MATCHES",
            "WORKSPACE_FILE_SEARCH_MAX_RESULTS",
            "CUSTOMER_FILE_READ_DEFAULT_LIMIT",
            "RETRIEVAL_DEFAULT_TOP_K",
            "HF_HUB_DISABLE_PROGRESS_BARS",
            "TQDM_DISABLE",
            "TRANSFORMERS_VERBOSITY",
            "MODEL_LIBRARY_LOG_LEVEL",
        ):
            self.assertIn(name, example)
        self.assertNotIn("legacy rollback only", example)
        self.assertIn("AGENT_MAX_MODEL_CALLS=100", example)
        self.assertIn("SHUTDOWN_TIMEOUT_SECONDS=60", example)
        self.assertIn("KNOWLEDGE_INDEX_MODE=persistent", example)
        self.assertNotIn("AGENT_MAX_ROUNDS", example)
        self.assertNotIn("BI_ENCODER_MODEL", example)
        self.assertNotIn("CROSS_ENCODER_MODEL", example)
        self.assertNotIn("EMBED_BATCH_SIZE", example)

    def test_from_env_builds_typed_static_asset_paths(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LLM_TIMEOUT": "12.5",
                "AGENT_MAX_MODEL_CALLS": "9",
                "CANCEL_GRACE_SECONDS": "1.5",
            }),
            project_root=Path("project"),
        )

        self.assertEqual(12.5, settings.llm_timeout_seconds)
        self.assertEqual(9, settings.max_model_calls_per_run)
        self.assertEqual(1.5, settings.cancel_grace_seconds)
        self.assertIs(Locale.ZH_CN, settings.ui_locale)
        self.assertIs(Locale.ZH_CN, settings.response_locale)
        self.assertEqual(Path("project/data/locales"), settings.locales_dir)
        self.assertIs(ModelProfile.PRO, settings.main_model_profile)
        self.assertIs(ModelProfile.PRO, settings.resume_model_profile)
        self.assertIs(ModelProfile.FLASH, settings.memory_model_profile)
        self.assertEqual(0.1, settings.main_temperature)
        self.assertEqual(0.2, settings.resume_temperature)
        self.assertEqual(0.0, settings.memory_temperature)
        self.assertEqual(3, settings.model_format_repair_limit)
        self.assertEqual(4096, settings.web_search_max_tokens)
        self.assertEqual("app.log", settings.log_file_name)
        self.assertEqual(10485760, settings.log_max_bytes)
        self.assertEqual(5, settings.log_backup_count)
        self.assertEqual(0.1, settings.cli_worker_poll_interval_seconds)
        self.assertEqual(0.05, settings.subprocess_poll_interval_seconds)
        self.assertEqual(500, settings.cli_result_preview_chars)
        self.assertEqual(160, settings.cli_argument_preview_chars)
        self.assertEqual(80, settings.session_preview_chars)
        self.assertEqual(100, settings.workspace_read_default_limit)
        self.assertEqual(50, settings.workspace_search_max_matches)
        self.assertEqual(50, settings.workspace_file_search_max_results)
        self.assertEqual(100, settings.customer_file_read_default_limit)
        self.assertEqual(5, settings.retrieval_default_top_k)
        self.assertTrue(settings.llm_thinking_enabled)
        self.assertFalse(settings.show_thinking)
        self.assertEqual(Path("project/data/prompts"), settings.prompts_dir)
        self.assertEqual(Path("project/data/workspace"), settings.workspace_dir)
        self.assertEqual(Path("project/data/logs"), settings.log_dir)
        self.assertEqual("INFO", settings.log_level)
        self.assertEqual("BAAI/bge-base-zh-v1.5", settings.embedding_model)
        self.assertEqual("BAAI/bge-reranker-v2-m3", settings.reranker_model)
        self.assertIs(KnowledgeIndexMode.PERSISTENT, settings.knowledge_index_mode)
        self.assertEqual(Path("project/data/runtime/artifacts"), settings.artifacts_dir)
        self.assertEqual(60.0, settings.pdf_build_timeout_seconds)
        self.assertEqual(65536, settings.artifact_log_max_bytes)

    def test_from_env_requires_canonical_application_settings(self) -> None:
        settings = Settings.from_env(
            _env(),
            project_root=Path("project"),
        )

        self.assertEqual(100, settings.max_model_calls_per_run)
        self.assertEqual(60.0, settings.shutdown_timeout_seconds)
        missing = _env()
        del missing["REFERENCE_DIR"]
        with self.assertRaisesRegex(SettingsValidationError, "REFERENCE_DIR"):
            Settings.from_env(missing, project_root=Path("project"))

    def test_from_env_rejects_invalid_model_and_logging_runtime_values(self) -> None:
        invalid_values = (
            ("MAIN_MODEL_PROFILE", "balanced"),
            ("MAIN_TEMPERATURE", "2.1"),
            ("MODEL_FORMAT_REPAIR_LIMIT", "-1"),
            ("WEB_SEARCH_MAX_TOKENS", "0"),
            ("LOG_FILE_NAME", "nested/app.log"),
            ("LOG_FILE_NAME", "nested\\\\app.log"),
            ("LOG_FILE_NAME", "C:\\\\app.log"),
            ("LOG_FILE_NAME", "/tmp/app.log"),
            ("LOG_BACKUP_COUNT", "-1"),
            ("CLI_WORKER_POLL_INTERVAL_SECONDS", "0"),
            ("CLI_RESULT_PREVIEW_CHARS", "0"),
            ("SESSION_PREVIEW_CHARS", "0"),
            ("RETRIEVAL_DEFAULT_TOP_K", "0"),
            ("TRANSFORMERS_VERBOSITY", "verbose"),
        )
        for name, value in invalid_values:
            with self.subTest(name=name):
                with self.assertRaisesRegex(SettingsValidationError, name):
                    Settings.from_env(_env({name: value}), project_root=Path("project"))

    def test_from_env_rejects_non_finite_duration_and_poll_values(self) -> None:
        names = (
            "LLM_TIMEOUT",
            "CANCEL_GRACE_SECONDS",
            "SHUTDOWN_TIMEOUT_SECONDS",
            "PDF_BUILD_TIMEOUT_SECONDS",
            "CLI_WORKER_POLL_INTERVAL_SECONDS",
            "SUBPROCESS_POLL_INTERVAL_SECONDS",
        )
        for name in names:
            for value in ("nan", "inf", "-inf"):
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(SettingsValidationError, name):
                        Settings.from_env(_env({name: value}), project_root=Path("project"))

    def test_from_env_validates_artifact_settings(self) -> None:
        env = _env({
            "OPENAI_API_KEY": "key", "OPENAI_BASE_URL": "https://example.test",
            "LLM_PRO_MODEL": "pro", "LLM_FLASH_MODEL": "flash",
            "PDF_BUILD_TIMEOUT_SECONDS": "12.5", "ARTIFACT_LOG_MAX_BYTES": "1024",
        })
        settings = Settings.from_env(env, project_root=Path("project"))
        self.assertEqual(12.5, settings.pdf_build_timeout_seconds)
        self.assertEqual(1024, settings.artifact_log_max_bytes)
        for name, value in (("PDF_BUILD_TIMEOUT_SECONDS", "0"), ("ARTIFACT_LOG_MAX_BYTES", "0")):
            invalid = {**env, name: value}
            with self.assertRaises(SettingsValidationError):
                Settings.from_env(invalid, project_root=Path("project"))

    def test_from_env_accepts_current_rag_setting_names(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "EMBEDDING_MODEL": "current-embedder",
                "RERANKER_MODEL": "current-reranker",
                "EMBEDDING_BATCH_SIZE": "11",
            }),
            project_root=Path("project"),
        )

        self.assertEqual("current-embedder", settings.embedding_model)
        self.assertEqual("current-reranker", settings.reranker_model)
        self.assertEqual(11, settings.embedding_batch_size)

    def test_from_env_ignores_removed_legacy_rag_setting_names(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "BI_ENCODER_MODEL": "legacy-embedder",
                "CROSS_ENCODER_MODEL": "legacy-reranker",
                "EMBED_BATCH_SIZE": "7",
            }),
            project_root=Path("project"),
        )

        self.assertEqual("BAAI/bge-base-zh-v1.5", settings.embedding_model)
        self.assertEqual("BAAI/bge-reranker-v2-m3", settings.reranker_model)
        self.assertEqual(32, settings.embedding_batch_size)

    def test_from_env_accepts_a_workspace_override(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "WORKSPACE_DIR": "custom-workspace",
            }),
            project_root=Path("project"),
        )

        self.assertEqual(Path("project/custom-workspace"), settings.workspace_dir)

    def test_from_env_resolves_all_configured_paths_from_project_root(self) -> None:
        settings = Settings.from_env(
            _env(
                {
                    "REFERENCE_DIR": "inputs/reference",
                    "PROMPTS_DIR": "inputs/prompts",
                    "RESUME_TEMPLATE_DIR": "inputs/resume",
                    "WORKSPACE_DIR": "runtime/workspace",
                    "SESSIONS_DIR": "runtime/sessions",
                    "ARTIFACTS_DIR": "runtime/artifacts",
                    "LOG_DIR": "runtime/logs",
                    "KNOWLEDGE_MANIFEST_PATH": "runtime/knowledge/manifest.json",
                    "KNOWLEDGE_CHROMA_DIR": "runtime/knowledge/chroma",
                    "MEMORIES_DIR": "runtime/memories",
                }
            ),
            project_root=Path("project"),
        )

        self.assertEqual(Path("project/inputs/reference"), settings.reference_dir)
        self.assertEqual(Path("project/inputs/prompts"), settings.prompts_dir)
        self.assertEqual(Path("project/inputs/resume"), settings.resume_template_dir)
        self.assertEqual(Path("project/runtime/workspace"), settings.workspace_dir)
        self.assertEqual(Path("project/runtime/sessions"), settings.sessions_dir)
        self.assertEqual(Path("project/runtime/artifacts"), settings.artifacts_dir)
        self.assertEqual(Path("project/runtime/logs"), settings.log_dir)
        self.assertEqual(
            Path("project/runtime/knowledge/manifest.json"),
            settings.knowledge_manifest_path,
        )
        self.assertEqual(
            Path("project/runtime/knowledge/chroma"),
            settings.knowledge_chroma_dir,
        )
        self.assertEqual(Path("project/runtime/memories"), settings.memories_dir)

    def test_from_env_rejects_all_legacy_data_roots(self) -> None:
        for name in (
            "REFERENCE_DIR",
            "PROMPTS_DIR",
            "RESUME_TEMPLATE_DIR",
            "WORKSPACE_DIR",
            "SESSIONS_DIR",
            "ARTIFACTS_DIR",
            "LOG_DIR",
            "KNOWLEDGE_MANIFEST_PATH",
            "KNOWLEDGE_CHROMA_DIR",
            "MEMORIES_DIR",
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(SettingsValidationError, name):
                    Settings.from_env(
                        _env({name: "data/save/nested"}),
                        project_root=Path("project"),
                    )

    def test_from_env_never_uses_legacy_runtime_data_paths(self) -> None:
        root = Path("sentinel-project-root")
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "CHROMA_PERSIST_DIR": "data/chroma",
                "MEMORIES_BASE_DIR": "data/memories",
                "WORKING_DIR": "data/temp",
                "SAVE_DIR": "data/save",
            }),
            project_root=root,
        )

        self.assertEqual(root / "data" / "workspace", settings.workspace_dir)
        self.assertEqual(root / "data" / "runtime" / "sessions", settings.sessions_dir)
        self.assertEqual(root / "data" / "runtime" / "knowledge" / "chroma", settings.knowledge_chroma_dir)
        self.assertIs(KnowledgeIndexMode.PERSISTENT, settings.knowledge_index_mode)
        self.assertEqual(root / "data" / "runtime" / "memories", settings.memories_dir)
        self.assertEqual(root / "data" / "runtime" / "artifacts", settings.artifacts_dir)

    def test_from_env_accepts_explicit_memory_index_mode(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "KNOWLEDGE_INDEX_MODE": "MeMoRy",
            }),
            project_root=Path("project"),
        )

        self.assertIs(KnowledgeIndexMode.MEMORY, settings.knowledge_index_mode)

    def test_from_env_rejects_invalid_knowledge_index_mode(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "KNOWLEDGE_INDEX_MODE"):
            Settings.from_env(
                _env({
                    "OPENAI_API_KEY": "key",
                    "OPENAI_BASE_URL": "https://example.test",
                    "LLM_PRO_MODEL": "pro",
                    "LLM_FLASH_MODEL": "flash",
                    "KNOWLEDGE_INDEX_MODE": "sometimes",
                }),
                project_root=Path("project"),
            )

    def test_from_env_parses_thinking_setting(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LLM_THINKING_ENABLED": "false",
                "SHOW_THINKING": "true",
            }),
            project_root=Path("project"),
        )

        self.assertFalse(settings.llm_thinking_enabled)
        self.assertTrue(settings.show_thinking)

    def test_from_env_resolves_explicit_response_locale(self) -> None:
        settings = Settings.from_env(
            _env({
                "UI_LOCALE": "en-US",
                "MODEL_RESPONSE_LANGUAGE": "zh-CN",
                "LOCALES_DIR": "custom/locales",
            }),
            project_root=Path("project"),
        )

        self.assertIs(Locale.EN_US, settings.ui_locale)
        self.assertIs(Locale.ZH_CN, settings.response_locale)
        self.assertEqual(Path("project/custom/locales"), settings.locales_dir)

    def test_from_env_rejects_invalid_locale_values(self) -> None:
        for name, value in (
            ("UI_LOCALE", "zh"),
            ("MODEL_RESPONSE_LANGUAGE", "auto"),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(SettingsValidationError, name):
                    Settings.from_env(_env({name: value}), project_root=Path("project"))

    def test_from_env_rejects_invalid_show_thinking(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "SHOW_THINKING"):
            Settings.from_env(
                _env({
                    "OPENAI_API_KEY": "key",
                    "OPENAI_BASE_URL": "https://example.test",
                    "LLM_PRO_MODEL": "pro",
                    "LLM_FLASH_MODEL": "flash",
                    "SHOW_THINKING": "sometimes",
                }),
                project_root=Path("project"),
            )

    def test_from_env_parses_logging_settings(self) -> None:
        settings = Settings.from_env(
            _env({
                "OPENAI_API_KEY": "key",
                "OPENAI_BASE_URL": "https://example.test",
                "LLM_PRO_MODEL": "pro",
                "LLM_FLASH_MODEL": "flash",
                "LOG_DIR": "runtime-logs",
                "LOG_LEVEL": "debug",
            }),
            project_root=Path("project"),
        )

        self.assertEqual(Path("project/runtime-logs"), settings.log_dir)
        self.assertEqual("DEBUG", settings.log_level)

    def test_from_env_rejects_invalid_log_level(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "LOG_LEVEL"):
            Settings.from_env(
                _env({
                    "OPENAI_API_KEY": "key",
                    "OPENAI_BASE_URL": "https://example.test",
                    "LLM_PRO_MODEL": "pro",
                    "LLM_FLASH_MODEL": "flash",
                    "LOG_LEVEL": "verbose",
                }),
                project_root=Path("project"),
            )

    def test_from_env_reports_missing_required_values(self) -> None:
        with self.assertRaisesRegex(SettingsValidationError, "OPENAI_API_KEY"):
            Settings.from_env({}, project_root=Path("project"))
