"""Conversation codec tests for prompt-compatible tool-call correlation."""

from datetime import datetime, timezone
import json
import unittest

from src.get_me_in.application.conversation_codec import ConversationCodec
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord, ToolResultRecord


class ConversationCodecTests(unittest.TestCase):
    def test_tool_call_and_result_share_call_id_without_provider_tool_role(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = ConversationCodec().encode(
            "system",
            (
                MessageRecord("user", Role.USER, "question", now),
                ToolCallRecord("event-call", "call-1", "search", {"query": "python"}, now),
                ToolResultRecord("event-result", "call-1", "search", {"items": 1}, now),
            ),
        )

        call = json.loads(messages[2].content)
        result = json.loads(messages[3].content)
        self.assertEqual("call-1", call["id"])
        self.assertEqual("call-1", result["tool_call_id"])
        self.assertEqual(Role.ASSISTANT, messages[2].role)
        self.assertEqual(Role.USER, messages[3].role)

    def test_thinking_is_not_part_of_any_conversation_record(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = ConversationCodec().encode(
            "system", (MessageRecord("assistant", Role.ASSISTANT, "answer", now, thinking="summary"),)
        )

        self.assertNotIn("thinking", messages[1].content)

    def test_tool_call_thinking_is_not_replayed(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = ConversationCodec().encode(
            "system",
            (ToolCallRecord("event", "call", "search", {}, now, thinking="summary"),),
        )

        self.assertNotIn("thinking", messages[1].content)
