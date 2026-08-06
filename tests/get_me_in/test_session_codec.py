"""Session snapshot codec tests."""

from dataclasses import replace
from datetime import datetime, timezone
import unittest

from src.get_me_in.application.session_codec import (
    SessionSnapshot,
    SessionSnapshotCodec,
    UnsupportedSessionSchemaError,
)
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus
from src.get_me_in.domain.sessions import AgentSessionState, HandoffFrame, PendingToolCall, RuntimePhase, SessionState


class SessionSnapshotCodecTests(unittest.TestCase):
    def test_round_trip_preserves_tagged_records_and_turn_id(self) -> None:
        codec = SessionSnapshotCodec()
        snapshot = _snapshot(format_repairs_used=2)

        payload = codec.encode(snapshot)
        restored = codec.decode(payload)

        record = restored.session.agents[AgentKey.MAIN].history[1]
        self.assertIsInstance(record, MessageRecord)
        self.assertEqual("turn-1", record.turn_id)
        self.assertEqual("summary", record.thinking)
        self.assertEqual("plan-1", record.plan.plan_id)
        self.assertEqual("session-1", restored.session.session_id)
        self.assertEqual("turn-1", restored.session.agents[AgentKey.MAIN].turn_id)
        self.assertEqual(2, restored.session.agents[AgentKey.MAIN].format_repairs_used)
        self.assertEqual(2, payload["agents"]["main"]["format_repairs_used"])
        self.assertTrue(payload["agents"]["main"]["repair_attempted"])
        self.assertEqual(3, payload["schema_version"])

    def test_decode_prefers_new_repair_count_and_reads_legacy_bool_projection(self) -> None:
        codec = SessionSnapshotCodec()
        payload = codec.encode(_snapshot(format_repairs_used=2))
        payload["agents"]["main"]["repair_attempted"] = False

        self.assertEqual(
            2,
            codec.decode(payload).session.agents[AgentKey.MAIN].format_repairs_used,
        )

        del payload["agents"]["main"]["format_repairs_used"]
        payload["agents"]["main"]["repair_attempted"] = True
        self.assertEqual(
            1,
            codec.decode(payload).session.agents[AgentKey.MAIN].format_repairs_used,
        )

    def test_rejects_invalid_repair_count_and_legacy_projection_types(self) -> None:
        codec = SessionSnapshotCodec()
        for value in (-1, True, "2", 1.5):
            with self.subTest(value=value):
                payload = codec.encode(_snapshot())
                payload["agents"]["main"]["format_repairs_used"] = value
                with self.assertRaises(ValueError):
                    codec.decode(payload)

        payload = codec.encode(_snapshot())
        del payload["agents"]["main"]["format_repairs_used"]
        payload["agents"]["main"]["repair_attempted"] = "yes"
        with self.assertRaises(ValueError):
            codec.decode(payload)

    def test_rejects_v3_handoff_snapshot_without_agent_turn_id(self) -> None:
        codec = SessionSnapshotCodec()
        snapshot = _handoff_snapshot()
        payload = codec.encode(snapshot)
        del payload["agents"]["main"]["turn_id"]

        with self.assertRaisesRegex(ValueError, "turn_id"):
            codec.decode(payload)

    def test_rejects_missing_or_malformed_schema_version_as_corruption(self) -> None:
        for value in (None, "3", True, 3.0):
            with self.subTest(value=value):
                payload = SessionSnapshotCodec().encode(_snapshot())
                if value is None:
                    del payload["schema_version"]
                else:
                    payload["schema_version"] = value

                with self.assertRaises(ValueError) as raised:
                    SessionSnapshotCodec().decode(payload)
                self.assertNotIsInstance(raised.exception, UnsupportedSessionSchemaError)

    def test_round_trip_preserves_tool_call_thinking_and_accepts_missing_fields(self) -> None:
        codec = SessionSnapshotCodec()
        snapshot = _snapshot(tool_thinking=True)
        payload = codec.encode(snapshot)

        restored = codec.decode(payload)
        tool_call = restored.session.agents[AgentKey.MAIN].history[2]
        self.assertIsInstance(tool_call, ToolCallRecord)
        self.assertEqual("tool summary", tool_call.thinking)
        self.assertEqual("Searching", tool_call.content)

        del payload["agents"]["main"]["history"][1]["thinking"]
        restored_without_thinking = codec.decode(payload)
        self.assertIsNone(restored_without_thinking.session.agents[AgentKey.MAIN].history[1].thinking)

    def test_rejects_old_schema_and_unsafe_phase(self) -> None:
        codec = SessionSnapshotCodec()
        payload = codec.encode(_snapshot())
        payload["schema_version"] = 1
        with self.assertRaises(UnsupportedSessionSchemaError):
            codec.decode(payload)

        unsafe = _snapshot(phase=RuntimePhase.TOOL_READY)
        with self.assertRaisesRegex(ValueError, "cannot be restored safely"):
            codec.encode(unsafe)

    def test_rejects_v2_with_typed_unsupported_schema_error(self) -> None:
        payload = SessionSnapshotCodec().encode(_snapshot())
        payload["schema_version"] = 2

        with self.assertRaises(UnsupportedSessionSchemaError):
            SessionSnapshotCodec().decode(payload)

    def test_rejects_non_empty_inactive_subagent_state(self) -> None:
        snapshot = _snapshot()
        agents = dict(snapshot.session.agents)
        agents[AgentKey.RESUME] = AgentSessionState(
            phase=RuntimePhase.COMPLETED,
            history=(MessageRecord("old", Role.ASSISTANT, "old episode", _now(), "old-turn"),),
        )
        invalid = SessionSnapshot(replace(snapshot.session, agents=agents), snapshot.saved_at)

        with self.assertRaisesRegex(ValueError, "Inactive SubAgent state must be empty"):
            SessionSnapshotCodec().encode(invalid)

    def test_active_handoff_rejects_non_target_subagent_state(self) -> None:
        snapshot = _handoff_snapshot()
        agents = dict(snapshot.session.agents)
        agents[AgentKey.JOB_SEARCH] = AgentSessionState(phase=RuntimePhase.COMPLETED)
        invalid = SessionSnapshot(replace(snapshot.session, agents=agents), snapshot.saved_at)

        with self.assertRaisesRegex(ValueError, "Inactive SubAgent state must be empty"):
            SessionSnapshotCodec().encode(invalid)

    def test_rejects_unmatched_tool_result(self) -> None:
        codec = SessionSnapshotCodec()
        payload = codec.encode(_snapshot())
        agent = payload["agents"]["main"]
        agent["history"] = [{
            "kind": "tool_result", "event_id": "event-2", "call_id": "call-2",
            "tool_name": "tool", "output": "result", "timestamp": _now().isoformat(), "turn_id": "turn-1",
        }]
        with self.assertRaisesRegex(ValueError, "matching tool call"):
            codec.decode(payload)

    def test_rejects_inconsistent_handoff_frame(self) -> None:
        snapshot = _snapshot()
        session = snapshot.session
        agents = dict(session.agents)
        agents[AgentKey.RESUME] = AgentSessionState()
        inconsistent = SessionSnapshot(
            SessionState(
                session_id=session.session_id,
                active_agent=AgentKey.RESUME,
                agents=agents,
                handoff_stack=(HandoffFrame(AgentKey.MAIN, AgentKey.RESUME, "call-1", "turn-1", "context"),),
                created_at=session.created_at,
                updated_at=session.updated_at,
            ),
            snapshot.saved_at,
        )

        with self.assertRaisesRegex(ValueError, "waiting for completion"):
            SessionSnapshotCodec().encode(inconsistent)


def _snapshot(
    *,
    phase: RuntimePhase = RuntimePhase.READY,
    tool_thinking: bool = False,
    format_repairs_used: int = 0,
) -> SessionSnapshot:
    plan = Plan(
        "plan-1",
        (PlanItem("item-1", "step", PlanStatus.IN_PROGRESS),),
    )
    history = [
        MessageRecord("event-1", Role.USER, "hello", _now(), "turn-1", plan=plan),
        MessageRecord("event-2", Role.ASSISTANT, "answer", _now(), "turn-1", "summary", plan),
    ]
    if tool_thinking:
        history.append(ToolCallRecord("event-3", "call-1", "search", {}, _now(), "turn-1", "tool summary", plan, "Searching"))
    session = SessionState(
        session_id="session-1",
        active_agent=AgentKey.MAIN,
        agents={AgentKey.MAIN: AgentSessionState(
            phase=phase,
            history=tuple(history),
            turn_id="turn-1",
            format_repairs_used=format_repairs_used,
        )},
        handoff_stack=(),
        created_at=_now(),
        updated_at=_now(),
    )
    return SessionSnapshot(session, _now())


def _handoff_snapshot() -> SessionSnapshot:
    history = (
        MessageRecord("event-1", Role.USER, "delegate", _now(), "turn-1"),
        ToolCallRecord("event-2", "call-1", "switch_to_subagent", {}, _now(), "turn-1"),
    )
    session = SessionState(
        session_id="handoff-session",
        active_agent=AgentKey.RESUME,
        agents={
            AgentKey.MAIN: AgentSessionState(
                phase=RuntimePhase.WAITING_FOR_HANDOFF,
                history=history,
                pending_tool=PendingToolCall("call-1", "switch_to_subagent", {}),
                turn_id="turn-1",
            ),
            AgentKey.RESUME: AgentSessionState(phase=RuntimePhase.WAITING_FOR_USER),
        },
        handoff_stack=(HandoffFrame(AgentKey.MAIN, AgentKey.RESUME, "call-1", "turn-1", "context"),),
        created_at=_now(),
        updated_at=_now(),
    )
    return SessionSnapshot(session, _now())


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
