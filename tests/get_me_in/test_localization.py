import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.get_me_in.application.localization import (
    Locale,
    parse_locale,
    prompt_language_name,
    resolve_response_locale,
)
from src.get_me_in.cli.localization import LocaleCatalogError, load_translator
from src.get_me_in.cli.main import _load_bootstrap_translator


class LocalizationTests(unittest.TestCase):
    def test_locale_values_are_exact_and_response_ui_resolves(self) -> None:
        self.assertIs(Locale.ZH_CN, parse_locale("zh-CN", setting_name="UI_LOCALE"))
        self.assertIs(Locale.EN_US, parse_locale("en-US", setting_name="UI_LOCALE"))
        self.assertIs(
            Locale.EN_US,
            resolve_response_locale("ui", Locale.EN_US),
        )
        self.assertIs(
            Locale.ZH_CN,
            resolve_response_locale("zh-CN", Locale.EN_US),
        )
        self.assertEqual("简体中文（zh-CN）", prompt_language_name(Locale.ZH_CN))
        self.assertEqual("English (en-US)", prompt_language_name(Locale.EN_US))

        for value in ("zh", "EN-US", "auto", ""):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "UI_LOCALE"):
                    parse_locale(value, setting_name="UI_LOCALE")

    def test_real_catalogs_load_with_matching_keys_and_placeholders(self) -> None:
        root = Path(__file__).resolve().parents[2]
        zh = load_translator(root / "data/locales", Locale.ZH_CN)
        en = load_translator(root / "data/locales", Locale.EN_US)

        self.assertEqual("配置错误：bad value", zh.text("startup.settings_error", detail="bad value"))
        self.assertEqual("Configuration error: bad value", en.text("startup.settings_error", detail="bad value"))
        with self.assertRaises(TypeError):
            zh.messages["new.key"] = "not allowed"  # type: ignore[index]

    def test_catalog_rejects_key_and_placeholder_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root / "zh-CN.json", {"hello": "你好，{name}"})
            self._write(root / "en-US.json", {"hello": "Hello"})
            with self.assertRaisesRegex(LocaleCatalogError, "placeholders"):
                load_translator(root, Locale.EN_US)

            self._write(root / "en-US.json", {"goodbye": "Goodbye"})
            with self.assertRaisesRegex(LocaleCatalogError, "keys differ"):
                load_translator(root, Locale.EN_US)

    def test_catalog_rejects_non_named_or_invalid_format_fields(self) -> None:
        invalid_catalogs = (
            {"hello": "Hello {}"},
            {"hello": "Hello {user.name}"},
            {"hello": "Hello {name!r}"},
            {"hello": "Hello {name:>10}"},
            {"hello": "Hello {name"},
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for invalid in invalid_catalogs:
                with self.subTest(invalid=invalid):
                    self._write(root / "zh-CN.json", invalid)
                    self._write(root / "en-US.json", invalid)
                    with self.assertRaises(LocaleCatalogError):
                        load_translator(root, Locale.ZH_CN)

    def test_translator_requires_exact_format_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = {"hello": "Hello, {name}"}
            self._write(root / "zh-CN.json", catalog)
            self._write(root / "en-US.json", catalog)
            translator = load_translator(root, Locale.EN_US)
            self.assertEqual("Hello, Codex", translator.text("hello", name="Codex"))
            with self.assertRaisesRegex(LocaleCatalogError, "missing"):
                translator.text("hello")
            with self.assertRaisesRegex(LocaleCatalogError, "unexpected"):
                translator.text("hello", name="Codex", extra="value")
            with self.assertRaisesRegex(LocaleCatalogError, "unknown"):
                translator.text("missing")

    def test_bootstrap_uses_base_catalog_for_invalid_locale_and_fails_if_base_is_broken(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write(root / "zh-CN.json", {"error": "错误"})
            self._write(root / "en-US.json", {"error": "Error"})
            with patch.dict(
                os.environ,
                {"LOCALES_DIR": str(root), "UI_LOCALE": "invalid"},
                clear=False,
            ):
                translator = _load_bootstrap_translator(Path(temporary))
            self.assertIsNotNone(translator)
            self.assertIs(Locale.ZH_CN, translator.locale)  # type: ignore[union-attr]

            (root / "zh-CN.json").write_text("{broken", encoding="utf-8")
            with patch.dict(
                os.environ,
                {"LOCALES_DIR": str(root), "UI_LOCALE": "en-US"},
                clear=False,
            ):
                self.assertIsNone(_load_bootstrap_translator(Path(temporary)))

    @staticmethod
    def _write(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
