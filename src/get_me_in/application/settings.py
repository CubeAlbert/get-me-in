"""Typed, non-terminating configuration for the v2 composition root."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping


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
    llm_timeout_seconds: float
    llm_thinking_enabled: bool
    hf_endpoint: str | None
    reference_dir: Path
    prompts_dir: Path
    resume_template_dir: Path
    workspace_dir: Path
    sessions_dir: Path
    log_dir: Path = Path("data/logs")
    log_level: str = "INFO"
    max_model_calls_per_run: int = 100
    cancel_grace_seconds: float = 2.0
    show_thinking: bool = False
    knowledge_index_mode: KnowledgeIndexMode = KnowledgeIndexMode.PERSISTENT
    knowledge_manifest_path: Path = Path("data/v2/knowledge/manifest.json")
    knowledge_chroma_dir: Path = Path("data/v2/knowledge/chroma")
    memories_dir: Path = Path("data/v2/memories")
    embedding_model: str = "BAAI/bge-base-zh-v1.5"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    embedding_batch_size: int = 32
    rerank_batch_size: int = 32
    retrieval_top_k: int = 8
    shutdown_timeout_seconds: float = 60.0
    auto_memory_on_exit: bool = False
    artifacts_dir: Path = Path("data/v2/artifacts")
    pdf_build_timeout_seconds: float = 60.0
    artifact_log_max_bytes: int = 65536

    @classmethod
    def from_env(cls, env: Mapping[str, str], *, project_root: Path) -> "Settings":
        required = (
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "LLM_PRO_MODEL",
            "LLM_FLASH_MODEL",
        )
        missing = [name for name in required if not env.get(name, "").strip()]
        if missing:
            raise SettingsValidationError(
                f"Missing required settings: {', '.join(missing)}"
            )

        timeout_raw = env.get("LLM_TIMEOUT", "60")
        try:
            timeout = float(timeout_raw)
        except ValueError as error:
            raise SettingsValidationError(
                f"LLM_TIMEOUT must be a number: {timeout_raw!r}"
            ) from error
        if timeout <= 0:
            raise SettingsValidationError("LLM_TIMEOUT must be greater than zero")

        max_calls_raw = env.get("AGENT_MAX_MODEL_CALLS", "100")
        try:
            max_calls = int(max_calls_raw)
        except ValueError as error:
            raise SettingsValidationError(
                f"AGENT_MAX_MODEL_CALLS must be an integer: {max_calls_raw!r}"
            ) from error
        if max_calls < 1:
            raise SettingsValidationError("AGENT_MAX_MODEL_CALLS must be at least one")

        cancel_grace_raw = env.get("CANCEL_GRACE_SECONDS", "2")
        try:
            cancel_grace = float(cancel_grace_raw)
        except ValueError as error:
            raise SettingsValidationError(
                f"CANCEL_GRACE_SECONDS must be a number: {cancel_grace_raw!r}"
            ) from error
        if cancel_grace < 0:
            raise SettingsValidationError("CANCEL_GRACE_SECONDS must not be negative")

        log_level = env.get("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise SettingsValidationError(
                "LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL"
            )
        log_dir = Path(env.get("LOG_DIR", "data/logs"))
        if not log_dir.is_absolute():
            log_dir = project_root / log_dir

        thinking_raw = env.get("LLM_THINKING_ENABLED", "true").strip().lower()
        boolean_values = {"true": True, "1": True, "false": False, "0": False}
        if thinking_raw not in boolean_values:
            raise SettingsValidationError(
                "LLM_THINKING_ENABLED must be true, false, 1, or 0"
            )
        show_thinking_raw = env.get("SHOW_THINKING", "false").strip().lower()
        if show_thinking_raw not in boolean_values:
            raise SettingsValidationError(
                "SHOW_THINKING must be true, false, 1, or 0"
            )
        knowledge_index_mode_raw = env.get(
            "KNOWLEDGE_INDEX_MODE", KnowledgeIndexMode.PERSISTENT.value
        ).strip().lower()
        try:
            knowledge_index_mode = KnowledgeIndexMode(knowledge_index_mode_raw)
        except ValueError as error:
            raise SettingsValidationError(
                "KNOWLEDGE_INDEX_MODE must be persistent or memory"
            ) from error

        def positive_int(name: str, default: int) -> int:
            raw = env.get(name, str(default))
            try:
                value = int(raw)
            except ValueError as error:
                raise SettingsValidationError(f"{name} must be an integer: {raw!r}") from error
            if value < 1:
                raise SettingsValidationError(f"{name} must be at least one")
            return value

        def positive_float(name: str, default: float) -> float:
            raw = env.get(name, str(default))
            try:
                value = float(raw)
            except ValueError as error:
                raise SettingsValidationError(f"{name} must be a number: {raw!r}") from error
            if value <= 0:
                raise SettingsValidationError(f"{name} must be greater than zero")
            return value

        shutdown_raw = env.get("SHUTDOWN_TIMEOUT_SECONDS", "60")
        try:
            shutdown_timeout = float(shutdown_raw)
        except ValueError as error:
            raise SettingsValidationError(
                f"SHUTDOWN_TIMEOUT_SECONDS must be a number: {shutdown_raw!r}"
            ) from error
        if shutdown_timeout <= 0:
            raise SettingsValidationError("SHUTDOWN_TIMEOUT_SECONDS must be greater than zero")

        auto_memory_raw = env.get("AUTO_MEMORY_ON_EXIT", "false").strip().lower()
        if auto_memory_raw not in boolean_values:
            raise SettingsValidationError(
                "AUTO_MEMORY_ON_EXIT must be true, false, 1, or 0"
            )

        return cls(
            openai_api_key=env["OPENAI_API_KEY"],
            openai_base_url=env["OPENAI_BASE_URL"],
            llm_pro_model=env["LLM_PRO_MODEL"],
            llm_flash_model=env["LLM_FLASH_MODEL"],
            llm_timeout_seconds=timeout,
            llm_thinking_enabled=boolean_values[thinking_raw],
            hf_endpoint=env.get("HF_ENDPOINT") or None,
            reference_dir=project_root / "data" / "reference",
            prompts_dir=project_root / "data" / "prompts",
            resume_template_dir=project_root / "data" / "resume" / "template",
            workspace_dir=Path(env.get("WORKSPACE_DIR", project_root / "data" / "workspace")),
            sessions_dir=Path(env.get("SESSIONS_DIR", project_root / "data" / "v2" / "sessions")),
            log_dir=log_dir,
            log_level=log_level,
            max_model_calls_per_run=max_calls,
            cancel_grace_seconds=cancel_grace,
            show_thinking=boolean_values[show_thinking_raw],
            knowledge_index_mode=knowledge_index_mode,
            knowledge_manifest_path=project_root / "data" / "v2" / "knowledge" / "manifest.json",
            knowledge_chroma_dir=project_root / "data" / "v2" / "knowledge" / "chroma",
            memories_dir=project_root / "data" / "v2" / "memories",
            embedding_model=env.get("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5"),
            reranker_model=env.get("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"),
            embedding_batch_size=positive_int("EMBEDDING_BATCH_SIZE", 32),
            rerank_batch_size=positive_int("RERANK_BATCH_SIZE", 32),
            retrieval_top_k=positive_int("RETRIEVAL_TOP_K", 8),
            shutdown_timeout_seconds=shutdown_timeout,
            auto_memory_on_exit=boolean_values[auto_memory_raw],
            artifacts_dir=Path(env.get("ARTIFACTS_DIR", project_root / "data" / "v2" / "artifacts")),
            pdf_build_timeout_seconds=positive_float("PDF_BUILD_TIMEOUT_SECONDS", 60),
            artifact_log_max_bytes=positive_int("ARTIFACT_LOG_MAX_BYTES", 65536),
        )
