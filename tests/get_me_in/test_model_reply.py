"""Tests for the provider-independent structured reply codec."""

import unittest

from src.get_me_in.application.model_reply import (
    ModelReplyParseError,
    ModelReplyParser,
)


class ModelReplyParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ModelReplyParser()

    def test_parses_content_and_ignores_thinking_for_runtime_output(self) -> None:
        reply = self.parser.parse('{"content": "hello", "thinking": "internal"}')

        self.assertEqual("hello", reply.content)
        self.assertEqual("internal", reply.thinking)

    def test_parses_structured_tool_call(self) -> None:
        reply = self.parser.parse(
            '{"content": "", "tool_call": {"name": "search", "arguments": {"q": "x"}}}'
        )

        self.assertEqual("search", reply.tool_name)
        self.assertEqual({"q": "x"}, reply.tool_arguments)

    def test_rejects_invalid_json(self) -> None:
        with self.assertRaises(ModelReplyParseError):
            self.parser.parse("not json")

    def test_rejects_missing_content(self) -> None:
        with self.assertRaises(ModelReplyParseError):
            self.parser.parse("{}")
