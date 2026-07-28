"""Tests for the provider-independent structured reply codec."""

import unittest

from src.get_me_in.application.model_reply import (
    ModelReplyParseError,
    ModelReplyParser,
)


class ModelReplyParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ModelReplyParser()

    def test_parses_finish_thinking_for_runtime_output(self) -> None:
        reply = self.parser.parse(
            '{"event_type": "finish", "message": "hello", "thinking": "internal"}'
        )

        self.assertEqual("hello", reply.content)
        self.assertEqual("internal", reply.thinking)

    def test_parses_tool_call(self) -> None:
        reply = self.parser.parse(
            '{"event_type": "tool_call", "message": "Searching", "tool": "search", '
            '"event_payload": {"q": "x"}}'
        )

        self.assertEqual("search", reply.tool_name)
        self.assertEqual({"q": "x"}, reply.tool_arguments)
        self.assertIsNone(reply.thinking)
        self.assertEqual("Searching", reply.content)

    def test_rejects_finish_without_thinking_but_allows_tool_call_without_it(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "thinking"):
            self.parser.parse('{"event_type": "finish", "message": "answer"}')

        reply = self.parser.parse(
            '{"event_type": "tool_call", "message": "", "tool": "search", '
            '"event_payload": {}}'
        )
        self.assertIsNone(reply.thinking)

    def test_rejects_non_string_thinking(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "thinking"):
            self.parser.parse(
                '{"event_type": "finish", "message": "answer", "thinking": 1}'
            )
        with self.assertRaisesRegex(ModelReplyParseError, "thinking"):
            self.parser.parse(
                '{"event_type": "tool_call", "message": "", "thinking": null, '
                '"tool": "search", "event_payload": {}}'
            )

    def test_ignores_internal_and_unknown_fields_from_model_output(self) -> None:
        reply = self.parser.parse(
            '{"id": "untrusted", "role": "user", "timestamp": "wrong", '
            '"tool_call_id": "untrusted-call", "plan_status": {"current": "wrong"}, '
            '"unknown": "ignored", "event_type": "finish", '
            '"message": "answer", "thinking": "summary"}'
        )

        self.assertEqual("answer", reply.content)
        self.assertEqual("summary", reply.thinking)

    def test_rejects_the_removed_content_and_nested_tool_call_shape(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "event_type"):
            self.parser.parse(
                '{"content": "", "tool_call": {"name": "search", "arguments": {}}}'
            )

    def test_repairs_common_json_syntax_errors_locally(self) -> None:
        reply = self.parser.parse(
            '{"event_type": "finish", "message": "line1\nline2", '
            '"thinking": "",}'
        )

        self.assertEqual("line1\nline2", reply.content)
        self.assertEqual("json_repair", reply.repair_kind)

    def test_rejects_plain_text_and_json_strings(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "JSON object"):
            self.parser.parse("plain markdown answer")
        with self.assertRaisesRegex(ModelReplyParseError, "JSON object"):
            self.parser.parse('"quoted answer"')

    def test_rejects_non_object_structures_that_cannot_be_safely_normalized(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "JSON object"):
            self.parser.parse('["tool_call", "search"]')

    def test_rejects_missing_content(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "message"):
            self.parser.parse(
                '{"event_type": "finish", "thinking": "summary"}'
            )

    def test_rejects_finish_tool_data_and_invalid_tool_call_fields(self) -> None:
        with self.assertRaisesRegex(ModelReplyParseError, "message"):
            self.parser.parse(
                '{"event_type": "finish", "message": "", "thinking": "summary"}'
            )
        with self.assertRaisesRegex(ModelReplyParseError, "finish tool"):
            self.parser.parse(
                '{"event_type": "finish", "message": "answer", '
                '"thinking": "summary", "tool": "search"}'
            )
        with self.assertRaisesRegex(ModelReplyParseError, "non-empty tool"):
            self.parser.parse(
                '{"event_type": "tool_call", "message": "", "tool": "", '
                '"event_payload": {}}'
            )
        with self.assertRaisesRegex(ModelReplyParseError, "event_payload"):
            self.parser.parse(
                '{"event_type": "tool_call", "message": "", "tool": "search", '
                '"event_payload": null}'
            )
