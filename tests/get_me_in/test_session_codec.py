"""Session snapshot codec tests."""

from datetime import datetime, timezone
import unittest

from src.get_me_in.application.session_codec import SessionSnapshot, SessionSnapshotCodec
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord
from src.get_me_in.domain.sessions import AgentSessionState, HandoffFrame, RuntimePhase, SessionState


class SessionSnapshotCodecTests(unittest.TestCase):
    def test_round_trip_preserves_tagged_records_and_turn_id(self) -> None:
        codec = SessionSnapshotCodec()
        snapshot = _snapshot()

        restored = codec.decode(codec.encode(snapshot))

        record = restored.session.agents[AgentKey.MAIN].history[1]
        self.assertIsInstance(record, MessageRecord)
        self.assertEqual("turn-1", record.turn_id)
        self.assertEqual("summary", record.thinking)
        self.assertEqual("session-1", restored.session.session_id)

    def test_round_trip_preserves_tool_call_thinking_and_accepts_missing_fields(self) -> None:
        codec = SessionSnapshotCodec()
        snapshot = _snapshot(tool_thinking=True)
        payload = codec.encode(snapshot)

        restored = codec.decode(payload)
        tool_call = restored.session.agents[AgentKey.MAIN].history[2]
        self.assertIsInstance(tool_call, ToolCallRecord)
        self.assertEqual("tool summary", tool_call.thinking)

        del payload["agents"]["main"]["history"][1]["thinking"]
        restored_without_thinking = codec.decode(payload)
        self.assertIsNone(restored_without_thinking.session.agents[AgentKey.MAIN].history[1].thinking)

    def test_rejects_old_schema_and_unsafe_phase(self) -> None:
        codec = SessionSnapshotCodec()
        payload = codec.encode(_snapshot())
        payload["schema_version"] = 1
        with self.assertRaises(ValueError):
            codec.decode(payload)

        unsafe = _snapshot(phase=RuntimePhase.TOOL_READY)
        with self.assertRaisesRegex(ValueError, "cannot be restored safely"):
            codec.encode(unsafe)

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


def _snapshot(*, phase: RuntimePhase = RuntimePhase.READY, tool_thinking: bool = False) -> SessionSnapshot:
    history = [
        MessageRecord("event-1", Role.USER, "hello", _now(), "turn-1"),
        MessageRecord("event-2", Role.ASSISTANT, "answer", _now(), "turn-1", "summary"),
    ]
    if tool_thinking:
        history.append(ToolCallRecord("event-3", "call-1", "search", {}, _now(), "turn-1", "tool summary"))
    session = SessionState(
        session_id="session-1",
        active_agent=AgentKey.MAIN,
        agents={AgentKey.MAIN: AgentSessionState(
            phase=phase,
            history=tuple(history),
        )},
        handoff_stack=(),
        created_at=_now(),
        updated_at=_now(),
    )
    return SessionSnapshot(session, _now())


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
