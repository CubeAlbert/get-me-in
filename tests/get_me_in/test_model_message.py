"""Contract tests for the shared model-message entity and codec."""

from datetime import datetime, timezone
import json
import unittest

from src.get_me_in.application.model_message import (
    ModelMessageCodec,
    ModelMessageEventType,
    ModelMessageParseError,
)
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord, ToolResultRecord
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus


class ModelMessageCodecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.codec = ModelMessageCodec()

    def test_encodes_all_history_event_shapes_into_input_format(self) -> None:
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        plan = Plan(
            "plan",
            (
                PlanItem("done", "已完成", PlanStatus.COMPLETED),
                PlanItem("current", "处理中", PlanStatus.IN_PROGRESS),
                PlanItem("next", "待处理", PlanStatus.PENDING),
            ),
        )
        messages = self.codec.encode(
            "system",
            (
                MessageRecord("user-event", Role.USER, "question", now),
                MessageRecord("system-event", Role.SYSTEM, "repair", now),
                MessageRecord("finish-event", Role.ASSISTANT, "answer", now, thinking="hidden"),
                ToolCallRecord(
                    "call-event", "call-1", "search", {"query": "python"}, now,
                    plan=plan, thinking="hidden", content="Searching",
                ),
                ToolResultRecord("result-event", "call-1", "search", {"items": 1}, now, plan=plan),
            ),
        )

        self.assertEqual(6, len(messages))
        self.assertEqual(Role.SYSTEM, messages[0].role)
        payloads = [json.loads(message.content) for message in messages[1:]]
        self.assertEqual(
            ["user_input", "system_message", "finish", "tool_call", "tool_call_result"],
            [payload["event_type"] for payload in payloads],
        )
        self.assertEqual("call-event", payloads[3]["id"])
        self.assertEqual("call-1", payloads[3]["tool_call_id"])
        self.assertEqual({"query": "python"}, payloads[3]["event_payload"])
        self.assertEqual("call-1", payloads[4]["tool_call_id"])
        self.assertEqual(
            {"current": "1|处理中", "completed": ["0|已完成"], "remaining": ["2|待处理"]},
            payloads[3]["plan_status"],
        )
        self.assertNotIn("thinking", payloads[2])
        self.assertNotIn("thinking", payloads[3])

    def test_parses_flat_finish_and_tool_call_into_same_entity(self) -> None:
        finish = self.codec.parse(
            '{"event_type":"finish","message":"answer","thinking":"summary"}'
        )
        tool_call = self.codec.parse(
            '{"event_type":"tool_call","message":"Searching",'
            '"tool":"search","event_payload":{"query":"python"}}'
        )

        self.assertEqual(ModelMessageEventType.FINISH, finish.event_type)
        self.assertEqual("answer", finish.message)
        self.assertIsNone(finish.id)
        self.assertIsNone(finish.role)
        self.assertEqual(ModelMessageEventType.TOOL_CALL, tool_call.event_type)
        self.assertEqual("search", tool_call.tool)
        self.assertEqual({"query": "python"}, dict(tool_call.event_payload or {}))
        with self.assertRaises(TypeError):
            (tool_call.event_payload or {})["query"] = "changed"  # type: ignore[index]

    def test_ignores_internal_and_unknown_output_fields(self) -> None:
        reply = self.codec.parse(
            '{"id":"untrusted","role":"user","timestamp":"wrong",'
            '"tool_call_id":"untrusted-call","plan_status":{"current":"wrong"},'
            '"unknown":"ignored","event_type":"finish","message":"answer"}'
        )

        self.assertEqual("answer", reply.message)
        self.assertIsNone(reply.id)
        self.assertIsNone(reply.role)
        self.assertIsNone(reply.tool_call_id)
        self.assertIsNone(reply.plan_status)

    def test_repairs_json_syntax_without_changing_semantic_validation(self) -> None:
        reply = self.codec.parse(
            '{"event_type":"finish","message":"line1\nline2",}'
        )

        self.assertEqual("json_repair", reply.repair_kind)
        self.assertEqual("line1\nline2", reply.message)

    def test_rejects_invalid_flat_output_combinations(self) -> None:
        cases = (
            ('{"message":"answer"}', "event_type"),
            ('{"event_type":"user_input","message":"answer"}', "finish or tool_call"),
            ('{"event_type":"finish","message":""}', "non-empty"),
            ('{"event_type":"finish","message":"  \\n\\t"}', "non-empty"),
            ('{"event_type":"finish","message":"answer","tool":"search"}', "tool"),
            ('{"event_type":"tool_call","message":"","tool":"search","event_payload":{}}', "non-empty"),
            ('{"event_type":"tool_call","message":"  \\n\\t","tool":"search","event_payload":{}}', "non-empty"),
            ('{"event_type":"tool_call","message":"run","tool":"search"}', "event_payload"),
            ('{"event_type":"tool_call","message":"run","tool":"search","event_payload":[]}', "event_payload"),
        )
        for raw, error in cases:
            with self.subTest(raw=raw), self.assertRaisesRegex(ModelMessageParseError, error):
                self.codec.parse(raw)

    def test_allows_optional_thinking_with_non_empty_messages(self) -> None:
        finish = self.codec.parse('{"event_type":"finish","message":"answer","thinking":null}')
        tool_call = self.codec.parse(
            '{"event_type":"tool_call","message":"**Searching**","thinking":"",'
            '"tool":"search","event_payload":{}}'
        )

        self.assertIsNone(finish.thinking)
        self.assertEqual("**Searching**", tool_call.message)
        self.assertEqual("", tool_call.thinking)
        self.assertEqual({}, dict(tool_call.event_payload or {}))
