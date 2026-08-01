"""Typed, non-terminating configuration for the v2 composition root."""

from dataclasses import dataclass
from enum import StrEnum
import math
import os
from pathlib import Path
from typing import Mapping

from src.get_me_in.ports.llm import ModelProfile


class SettingsValidationError(ValueError):
    """Raised when required v2 configuration is absent or invalid."""


class KnowledgeIndexMode(StrEnum):
    """Storage lifetime for the local embedded Chroma knowledge index."""

    PERSISTENT = "persistent"
    MEMORY = "memory"


@dataclass(frozen=True)
class Settings:
    """Configuration required to assemble the R1 application skeleton."""

    openai_api_key: str
    openai_base_url: str
    llm_pro_model: str
    llm_flash_model: str
    main_model_profile: ModelProfile
    resume_model_profile: ModelProfile
    memory_model_profile: ModelProfile
    web_search_model_profile: ModelProfile
    main_temperature: float
    resume_temperature: float
    memory_temperature: float
    llm_timeout_seconds: float
    llm_thinking_enabled: bool
    hf_endpoint: str | None
    reference_dir: Path
    prompts_dir: Path
    resume_template_dir: Path
    workspace_dir: Path
    sessions_dir: Path
    log_dir: Path
    log_level: str
    max_model_calls_per_run: int
    cancel_grace_seconds: float
    show_thinking: bool
    knowledge_index_mode: KnowledgeIndexMode
    knowledge_manifest_path: Path
    knowledge_chroma_dir: Path
    memories_dir: Path
    embedding_model: str
    reranker_model: str
    embedding_batch_size: int
    rerank_batch_size: int
    retrieval_top_k: int
    shutdown_timeout_seconds: float
    auto_memory_on_exit: bool
    artifacts_dir: Path
    pdf_build_timeout_seconds: float
    artifact_log_max_bytes: int
    model_format_repair_limit: int
    web_search_max_tokens: int
    log_file_name: str
    log_max_bytes: int
    log_backup_count: int
    cli_worker_poll_interval_seconds: float
    subprocess_poll_interval_seconds: float
    hf_hub_disable_progress_bars: bool
    tqdm_disable: bool
    transformers_verbosity: str
    model_library_log_level: str

    @classmethod
    def from_env(cls, env: Mapping[str, str], *, project_root: Path) -> "Settings":
        required = (
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
            "LLM_THINKING_ENABLED",
            "SHOW_THINKING",
            "AGENT_MAX_MODEL_CALLS",
            "CANCEL_GRACE_SECONDS",
            "SHUTDOWN_TIMEOUT_SECONDS",
            "AUTO_MEMORY_ON_EXIT",
            "REFERENCE_DIR",
            "PROMPTS_DIR",
            "RESUME_TEMPLATE_DIR",
            "WORKSPACE_DIR",
            "SESSIONS_DIR",
            "ARTIFACTS_DIR",
            "LOG_DIR",
            "LOG_LEVEL",
            "KNOWLEDGE_INDEX_MODE",
            "KNOWLEDGE_MANIFEST_PATH",
            "KNOWLEDGE_CHROMA_DIR",
            "MEMORIES_DIR",
            "EMBEDDING_MODEL",
            "RERANKER_MODEL",
            "EMBEDDING_BATCH_SIZE",
            "RERANK_BATCH_SIZE",
            "RETRIEVAL_TOP_K",
            "HF_ENDPOINT",
            "PDF_BUILD_TIMEOUT_SECONDS",
            "ARTIFACT_LOG_MAX_BYTES",
            "MODEL_FORMAT_REPAIR_LIMIT",
            "WEB_SEARCH_MAX_TOKENS",
            "LOG_FILE_NAME",
            "LOG_MAX_BYTES",
            "LOG_BACKUP_COUNT",
            "CLI_WORKER_POLL_INTERVAL_SECONDS",
            "SUBPROCESS_POLL_INTERVAL_SECONDS",
            "HF_HUB_DISABLE_PROGRESS_BARS",
            "TQDM_DISABLE",
            "TRANSFORMERS_VERBOSITY",
            "MODEL_LIBRARY_LOG_LEVEL",
        )
        missing = [
            name
            for name in required
            if name not in env
            or (name != "HF_ENDPOINT" and not env[name].strip())
        ]
        if missing:
            raise SettingsValidationError(
                f"Missing required settings: {', '.join(missing)}"
            )

        def model_profile(name: str) -> ModelProfile:
            try:
                return ModelProfile(env[name].strip().lower())
            except ValueError as error:
                raise SettingsValidationError(
                    f"{name} must be pro or flash"
                ) from error

        def temperature(name: str) -> float:
            try:
                value = float(env[name])
            except ValueError as error:
                raise SettingsValidationError(f"{name} must be a number") from error
            if not math.isfinite(value) or not 0 <= value <= 2:
                raise SettingsValidationError(f"{name} must be between 0 and 2")
            return value

        main_model_profile = model_profile("MAIN_MODEL_PROFILE")
        resume_model_profile = model_profile("RESUME_MODEL_PROFILE")
        memory_model_profile = model_profile("MEMORY_MODEL_PROFILE")
        web_search_model_profile = model_profile("WEB_SEARCH_MODEL_PROFILE")
        main_temperature = temperature("MAIN_TEMPERATURE")
        resume_temperature = temperature("RESUME_TEMPERATURE")
        memory_temperature = temperature("MEMORY_TEMPERATURE")

        timeout_raw = env["LLM_TIMEOUT"]
        try:
            timeout = float(timeout_raw)
        except ValueError as error:
            raise SettingsValidationError("LLM_TIMEOUT must be a number") from error
        if timeout <= 0:
            raise SettingsValidationError("LLM_TIMEOUT must be greater than zero")

        max_calls_raw = env["AGENT_MAX_MODEL_CALLS"]
        try:
            max_calls = int(max_calls_raw)
        except ValueError as error:
            raise SettingsValidationError("AGENT_MAX_MODEL_CALLS must be an integer") from error
        if max_calls < 1:
            raise SettingsValidationError("AGENT_MAX_MODEL_CALLS must be at least one")

        cancel_grace_raw = env["CANCEL_GRACE_SECONDS"]
        try:
            cancel_grace = float(cancel_grace_raw)
        except ValueError as error:
            raise SettingsValidationError("CANCEL_GRACE_SECONDS must be a number") from error
        if cancel_grace < 0:
            raise SettingsValidationError("CANCEL_GRACE_SECONDS must not be negative")

        log_level = env["LOG_LEVEL"].strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise SettingsValidationError(
                "LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
            )
        path_values = {
            name: _resolve_config_path(name, env[name], project_root)
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
            )
        }

        thinking_raw = env["LLM_THINKING_ENABLED"].strip().lower()
        boolean_values = {"true": True, "1": True, "false": False, "0": False}

        def boolean(name: str) -> bool:
            raw = env[name].strip().lower()
            if raw not in boolean_values:
                raise SettingsValidationError(
                    f"{name} must be true, false, 1, or 0"
                )
            return boolean_values[raw]

        if thinking_raw not in boolean_values:
            raise SettingsValidationError(
                "LLM_THINKING_ENABLED must be true, false, 1, or 0"
            )
        show_thinking_raw = env["SHOW_THINKING"].strip().lower()
        if show_thinking_raw not in boolean_values:
            raise SettingsValidationError(
                "SHOW_THINKING must be true, false, 1, or 0"
            )
        knowledge_index_mode_raw = env["KNOWLEDGE_INDEX_MODE"].strip().lower()
        try:
            knowledge_index_mode = KnowledgeIndexMode(knowledge_index_mode_raw)
        except ValueError as error:
            raise SettingsValidationError(
                "KNOWLEDGE_INDEX_MODE must be persistent or memory"
            ) from error

        def positive_int(name: str) -> int:
            raw = env[name]
            try:
                value = int(raw)
            except ValueError as error:
                raise SettingsValidationError(f"{name} must be an integer") from error
            if value < 1:
                raise SettingsValidationError(f"{name} must be at least one")
            return value

        def non_negative_int(name: str) -> int:
            raw = env[name]
            try:
                value = int(raw)
            except ValueError as error:
                raise SettingsValidationError(f"{name} must be an integer") from error
            if value < 0:
                raise SettingsValidationError(f"{name} must not be negative")
            return value

        def positive_float(name: str) -> float:
            raw = env[name]
            try:
                value = float(raw)
            except ValueError as error:
                raise SettingsValidationError(f"{name} must be a number") from error
            if value <= 0:
                raise SettingsValidationError(f"{name} must be greater than zero")
            return value

        shutdown_raw = env["SHUTDOWN_TIMEOUT_SECONDS"]
        try:
            shutdown_timeout = float(shutdown_raw)
        except ValueError as error:
            raise SettingsValidationError("SHUTDOWN_TIMEOUT_SECONDS must be a number") from error
        if shutdown_timeout <= 0:
            raise SettingsValidationError("SHUTDOWN_TIMEOUT_SECONDS must be greater than zero")

        auto_memory_raw = env["AUTO_MEMORY_ON_EXIT"].strip().lower()
        if auto_memory_raw not in boolean_values:
            raise SettingsValidationError(
                "AUTO_MEMORY_ON_EXIT must be true, false, 1, or 0"
            )

        transformers_verbosity = env["TRANSFORMERS_VERBOSITY"].strip().lower()
        if transformers_verbosity not in {
            "debug",
            "info",
            "warning",
            "error",
            "critical",
        }:
            raise SettingsValidationError(
                "TRANSFORMERS_VERBOSITY must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
            )
        model_library_log_level = env["MODEL_LIBRARY_LOG_LEVEL"].strip().upper()
        if model_library_log_level not in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            raise SettingsValidationError(
                "MODEL_LIBRARY_LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
            )
        log_file_name = env["LOG_FILE_NAME"].strip()
        log_file_path = Path(log_file_name)
        if (
            not log_file_name
            or log_file_name in {".", ".."}
            or log_file_path.is_absolute()
            or log_file_path.name != log_file_name
        ):
            raise SettingsValidationError(
                "LOG_FILE_NAME must be a single ordinary file name"
            )

        return cls(
            openai_api_key=env["OPENAI_API_KEY"],
            openai_base_url=env["OPENAI_BASE_URL"],
            llm_pro_model=env["LLM_PRO_MODEL"],
            llm_flash_model=env["LLM_FLASH_MODEL"],
            main_model_profile=main_model_profile,
            resume_model_profile=resume_model_profile,
            memory_model_profile=memory_model_profile,
            web_search_model_profile=web_search_model_profile,
            main_temperature=main_temperature,
            resume_temperature=resume_temperature,
            memory_temperature=memory_temperature,
            llm_timeout_seconds=timeout,
            llm_thinking_enabled=boolean_values[thinking_raw],
            hf_endpoint=env.get("HF_ENDPOINT") or None,
            reference_dir=path_values["REFERENCE_DIR"],
            prompts_dir=path_values["PROMPTS_DIR"],
            resume_template_dir=path_values["RESUME_TEMPLATE_DIR"],
            workspace_dir=path_values["WORKSPACE_DIR"],
            sessions_dir=path_values["SESSIONS_DIR"],
            log_dir=path_values["LOG_DIR"],
            log_level=log_level,
            max_model_calls_per_run=max_calls,
            cancel_grace_seconds=cancel_grace,
            show_thinking=boolean_values[show_thinking_raw],
            knowledge_index_mode=knowledge_index_mode,
            knowledge_manifest_path=path_values["KNOWLEDGE_MANIFEST_PATH"],
            knowledge_chroma_dir=path_values["KNOWLEDGE_CHROMA_DIR"],
            memories_dir=path_values["MEMORIES_DIR"],
            embedding_model=env["EMBEDDING_MODEL"],
            reranker_model=env["RERANKER_MODEL"],
            embedding_batch_size=positive_int("EMBEDDING_BATCH_SIZE"),
            rerank_batch_size=positive_int("RERANK_BATCH_SIZE"),
            retrieval_top_k=positive_int("RETRIEVAL_TOP_K"),
            shutdown_timeout_seconds=shutdown_timeout,
            auto_memory_on_exit=boolean_values[auto_memory_raw],
            artifacts_dir=path_values["ARTIFACTS_DIR"],
            pdf_build_timeout_seconds=positive_float("PDF_BUILD_TIMEOUT_SECONDS"),
            artifact_log_max_bytes=positive_int("ARTIFACT_LOG_MAX_BYTES"),
            model_format_repair_limit=non_negative_int("MODEL_FORMAT_REPAIR_LIMIT"),
            web_search_max_tokens=positive_int("WEB_SEARCH_MAX_TOKENS"),
            log_file_name=log_file_name,
            log_max_bytes=positive_int("LOG_MAX_BYTES"),
            log_backup_count=non_negative_int("LOG_BACKUP_COUNT"),
            cli_worker_poll_interval_seconds=positive_float(
                "CLI_WORKER_POLL_INTERVAL_SECONDS"
            ),
            subprocess_poll_interval_seconds=positive_float(
                "SUBPROCESS_POLL_INTERVAL_SECONDS"
            ),
            hf_hub_disable_progress_bars=boolean("HF_HUB_DISABLE_PROGRESS_BARS"),
            tqdm_disable=boolean("TQDM_DISABLE"),
            transformers_verbosity=transformers_verbosity,
            model_library_log_level=model_library_log_level,
        )


_LEGACY_DATA_PATHS = tuple(
    Path(path)
    for path in ("data/save", "data/memories", "data/chroma", "data/temp")
)


def _resolve_config_path(name: str, raw: str, project_root: Path) -> Path:
    """Resolve a configured path and reject all legacy runtime data roots."""
    value = raw.strip()
    if not value:
        raise SettingsValidationError(f"{name} must not be empty")
    configured = Path(value)
    resolved = configured if configured.is_absolute() else project_root / configured
    canonical = resolved.resolve(strict=False)
    for legacy_path in _LEGACY_DATA_PATHS:
        legacy_root = (project_root / legacy_path).resolve(strict=False)
        if canonical == legacy_root or legacy_root in canonical.parents:
            raise SettingsValidationError(
                f"{name} must not point inside a legacy data directory"
            )
    return Path(os.path.normpath(str(resolved)))
