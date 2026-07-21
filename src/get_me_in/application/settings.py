"""Typed, non-terminating configuration for the v2 composition root."""

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class SettingsValidationError(ValueError):
    """Raised when required v2 configuration is absent or invalid."""


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

        thinking_raw = env.get("LLM_THINKING_ENABLED", "true").strip().lower()
        boolean_values = {"true": True, "1": True, "false": False, "0": False}
        if thinking_raw not in boolean_values:
            raise SettingsValidationError(
                "LLM_THINKING_ENABLED must be true, false, 1, or 0"
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
        )
