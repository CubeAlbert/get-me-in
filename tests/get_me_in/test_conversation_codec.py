"""Conversation codec tests for prompt-compatible tool-call correlation."""

from datetime import datetime, timezone
import json
import unittest

from src.get_me_in.application.conversation_codec import ConversationCodec
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord, ToolResultRecord
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus


class ConversationCodecTests(unittest.TestCase):
    def test_tool_call_and_result_share_call_id_without_provider_tool_role(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = ConversationCodec().encode(
            "system",
            (
                MessageRecord("user", Role.USER, "question", now),
                ToolCallRecord(
                    "event-call",
                    "call-1",
                    "search",
                    {"query": "python"},
                    now,
                    content="Searching",
                ),
                ToolResultRecord("event-result", "call-1", "search", {"items": 1}, now),
            ),
        )

        call = json.loads(messages[2].content)
        result = json.loads(messages[3].content)
        self.assertEqual("event-call", call["id"])
        self.assertEqual("call-1", call["tool_call_id"])
        self.assertEqual("Searching", call["message"])
        self.assertEqual("call-1", result["tool_call_id"])
        self.assertEqual(Role.ASSISTANT, messages[2].role)
        self.assertEqual(Role.USER, messages[3].role)

    def test_thinking_is_not_part_of_any_conversation_record(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = ConversationCodec().encode(
            "system", (MessageRecord("assistant", Role.ASSISTANT, "answer", now, thinking="summary"),)
        )

        self.assertNotIn("thinking", messages[1].content)

    def test_runtime_plan_snapshot_is_projected_into_history_messages(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        plan = Plan(
            "plan",
            (
                PlanItem("done", "已完成", PlanStatus.COMPLETED),
                PlanItem("current", "处理中", PlanStatus.IN_PROGRESS),
                PlanItem("next", "待处理", PlanStatus.PENDING),
                PlanItem("cancelled", "已取消", PlanStatus.CANCELLED),
            ),
        )

        messages = ConversationCodec().encode(
            "system",
            (
                MessageRecord("event", Role.ASSISTANT, "answer", now, plan=plan),
                ToolResultRecord("result", "call", "search", "ok", now, plan=plan),
            ),
        )

        expected = {
            "current": "1|处理中",
            "completed": ["0|已完成"],
            "remaining": ["2|待处理"],
        }
        self.assertEqual(expected, json.loads(messages[1].content)["plan_status"])
        self.assertEqual(expected, json.loads(messages[2].content)["plan_status"])

    def test_tool_call_thinking_is_not_replayed(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        messages = ConversationCodec().encode(
            "system",
            (ToolCallRecord("event", "call", "search", {}, now, thinking="summary"),),
        )

        self.assertNotIn("thinking", messages[1].content)
