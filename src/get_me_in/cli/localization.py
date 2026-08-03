"""Strict, immutable locale catalog loading for the CLI frontend."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import string
from types import MappingProxyType
from typing import Mapping

from src.get_me_in.application.localization import Locale


class LocaleCatalogError(ValueError):
    """Raised when a locale catalog violates the shared catalog contract."""


_FIELD_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass(frozen=True)
class Translator:
    """Immutable access to one fully validated locale catalog."""

    locale: Locale
    messages: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", MappingProxyType(dict(self.messages)))

    def text(self, key: str, **values: object) -> str:
        """Format one known message using exactly its named placeholders."""
        try:
            template = self.messages[key]
        except KeyError as error:
            raise LocaleCatalogError(f"unknown locale key: {key}") from error
        expected = _placeholders(template, key=key)
        provided = set(values)
        if expected != provided:
            missing = ", ".join(sorted(expected - provided))
            extra = ", ".join(sorted(provided - expected))
            details = []
            if missing:
                details.append(f"missing: {missing}")
            if extra:
                details.append(f"unexpected: {extra}")
            raise LocaleCatalogError(
                f"locale key {key!r} received invalid format values ({'; '.join(details)})"
            )
        try:
            return template.format(**values)
        except (IndexError, KeyError, ValueError) as error:
            raise LocaleCatalogError(f"invalid locale format for key: {key}") from error


def load_translator(locales_dir: Path, locale: Locale) -> Translator:
    """Load and strictly validate the base and requested locale catalogs."""
    base = _load_catalog(locales_dir / f"{Locale.ZH_CN.value}.json")
    target = base if locale is Locale.ZH_CN else _load_catalog(locales_dir / f"{locale.value}.json")
    base_keys = set(base)
    target_keys = set(target)
    if base_keys != target_keys:
        missing = ", ".join(sorted(base_keys - target_keys))
        extra = ", ".join(sorted(target_keys - base_keys))
        details = []
        if missing:
            details.append(f"missing: {missing}")
        if extra:
            details.append(f"unexpected: {extra}")
        raise LocaleCatalogError(
            f"locale catalog keys differ for {locale.value} ({'; '.join(details)})"
        )
    for key in sorted(base_keys):
        base_placeholders = _placeholders(base[key], key=key)
        target_placeholders = _placeholders(target[key], key=key)
        if base_placeholders != target_placeholders:
            raise LocaleCatalogError(
                f"locale key {key!r} has different named placeholders between catalogs"
            )
    return Translator(locale, target)


def _load_catalog(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LocaleCatalogError(f"unable to load locale catalog: {path}") from error
    if not isinstance(raw, dict) or any(not isinstance(value, str) for value in raw.values()):
        raise LocaleCatalogError(f"locale catalog must be an object of strings: {path}")
    if any(not key for key in raw):
        raise LocaleCatalogError(f"locale catalog keys must not be empty: {path}")
    for key, template in raw.items():
        _placeholders(template, key=key)
    return raw


def _placeholders(template: str, *, key: str) -> frozenset[str]:
    fields: set[str] = set()
    try:
        parsed = string.Formatter().parse(template)
        for _, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue
            if (
                not _FIELD_NAME.fullmatch(field_name)
                or format_spec
                or conversion is not None
            ):
                raise LocaleCatalogError(
                    f"locale key {key!r} may use only simple named placeholders"
                )
            fields.add(field_name)
    except ValueError as error:
        raise LocaleCatalogError(f"invalid locale format for key: {key}") from error
    return frozenset(fields)
