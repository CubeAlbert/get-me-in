"""Tests for the provider-independent structured reply codec."""

import json
import unittest

from src.get_me_in.application.model_reply import ModelReplyParseError, ModelReplyParser


class ModelReplyParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ModelReplyParser()

    def test_parses_finish_envelope(self) -> None:
        reply = self.parser.parse(
            '{"message": "hello", "thinking": "internal", "tool_call": null}'
        )

        self.assertEqual("hello", reply.content)
        self.assertEqual("internal", reply.thinking)
        self.assertIsNone(reply.tool_name)

    def test_parses_tool_call_envelope(self) -> None:
        reply = self.parser.parse(
            '{"message": "Searching", "tool_call": '
            '{"name": "search", "arguments": {"q": "x"}}}'
        )

        self.assertEqual("search", reply.tool_name)
        self.assertEqual({"q": "x"}, reply.tool_arguments)
        self.assertIsNone(reply.thinking)
        self.assertEqual("Searching", reply.content)

    def test_allows_optional_thinking_and_arguments(self) -> None:
        reply = self.parser.parse('{"message": "answer"}')
        self.assertIsNone(reply.thinking)

        reply = self.parser.parse(
            '{"message": "", "tool_call": {"name": "search"}}'
        )
        self.assertEqual({}, reply.tool_arguments)
        self.assertIsNone(reply.thinking)

    def test_accepts_nullable_thinking_for_both_reply_types(self) -> None:
        for payload in (
            {"message": "answer", "thinking": None, "tool_call": None},
            {"message": "", "thinking": None, "tool_call": {"name": "search"}},
        ):
            with self.subTest(payload=payload):
                self.assertIsNone(self.parser.parse(json.dumps(payload)).thinking)

    def test_rejects_non_string_thinking(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "thinking"):
            self.parser.parse('{"message": "answer", "thinking": 1}')

    def test_allows_empty_or_whitespace_finish_thinking(self) -> None:
        for thinking in (None, "", "   ", "\n\t"):
            with self.subTest(thinking=repr(thinking)):
                reply = self.parser.parse(
                    json.dumps({"message": "answer", "thinking": thinking})
                )
                self.assertEqual(thinking, reply.thinking)

    def test_ignores_internal_and_unknown_fields_from_model_output(self) -> None:
        reply = self.parser.parse(
            '{"id": "untrusted", "role": "user", "timestamp": "wrong", '
            '"tool_call_id": "untrusted-call", "plan_status": {"current": "wrong"}, '
            '"unknown": "ignored", "message": "answer", "thinking": "summary", '
            '"tool_call": null}'
        )

        self.assertEqual("answer", reply.content)
        self.assertEqual("summary", reply.thinking)

    def test_rejects_removed_content_and_flat_tool_fields(self) -> None:
        for raw in (
            '{"content": "answer", "tool_call": null}',
            '{"message": "answer", "tool": "search", "event_payload": {}}',
            '{"event_type": "finish", "message": "answer", "tool_call": null}',
        ):
            with self.subTest(raw=raw), self.assertRaisesRegex(
                ModelReplyParseError, "message/thinking/tool_call"
            ):
                self.parser.parse(raw)

    def test_repairs_common_json_syntax_errors_locally(self) -> None:
        reply = self.parser.parse(
            '{"message": "line1\nline2", "thinking": "summary", '
            '"tool_call": null,}'
        )

        self.assertEqual("line1\nline2", reply.content)
        self.assertEqual("json_repair", reply.repair_kind)

    def test_rejects_plain_text_json_strings_and_arrays(self) -> None:
        for raw in ("plain markdown answer", '"quoted answer"', '["tool_call"]'):
            with self.subTest(raw=raw), self.assertRaisesRegex(
                ModelReplyParseError, "JSON object"
            ):
                self.parser.parse(raw)

    def test_rejects_missing_or_empty_finish_message(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "message"):
            self.parser.parse('{"thinking": "summary", "tool_call": null}')
        with self.assertRaisesRegex(ModelReplyParseError, "non-empty"):
            self.parser.parse('{"message": "", "tool_call": null}')

    def test_rejects_invalid_tool_call_fields(self) -> None:
        cases = (
            ('{"message": "", "tool_call": "search"}', "object or null"),
            ('{"message": "", "tool_call": {"name": ""}}', "non-empty name"),
            (
                '{"message": "", "tool_call": {"name": "search", "arguments": []}}',
                "arguments",
            ),
        )
        for raw, error in cases:
            with self.subTest(raw=raw), self.assertRaisesRegex(ModelReplyParseError, error):
                self.parser.parse(raw)
