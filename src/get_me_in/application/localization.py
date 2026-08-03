"""Process-level locale values shared by configuration and prompt assembly."""

from enum import StrEnum


class Locale(StrEnum):
    """Locales supported by the first multilingual CLI release."""

    ZH_CN = "zh-CN"
    EN_US = "en-US"


def parse_locale(value: str, *, setting_name: str) -> Locale:
    """Parse a locale configuration value without accepting aliases."""
    if not isinstance(value, str):
        raise ValueError(f"{setting_name} must be zh-CN or en-US")
    try:
        return Locale(value.strip())
    except ValueError as error:
        raise ValueError(f"{setting_name} must be zh-CN or en-US") from error


def resolve_response_locale(value: str, ui_locale: Locale) -> Locale:
    """Resolve ``ui`` to the current UI locale or parse an explicit locale."""
    if value.strip() == "ui":
        return ui_locale
    return parse_locale(value, setting_name="MODEL_RESPONSE_LANGUAGE")


def prompt_language_name(locale: Locale) -> str:
    """Return the deterministic language label used by the response prompt."""
    return {
        Locale.ZH_CN: "简体中文（zh-CN）",
        Locale.EN_US: "English (en-US)",
    }[locale]
