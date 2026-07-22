"""Session snapshot codec tests."""

from datetime import datetime, timezone
import unittest

from src.get_me_in.application.session_codec import SessionSnapshot, SessionSnapshotCodec
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role
from src.get_me_in.domain.sessions import AgentSessionState, RuntimePhase, SessionState


class SessionSnapshotCodecTests(unittest.TestCase):
    def test_round_trip_preserves_tagged_records_and_turn_id(self) -> None:
        codec = SessionSnapshotCodec()
        snapshot = _snapshot()

        restored = codec.decode(codec.encode(snapshot))

        record = restored.session.agents[AgentKey.MAIN].history[0]
        self.assertIsInstance(record, MessageRecord)
        self.assertEqual("turn-1", record.turn_id)
        self.assertEqual("session-1", restored.session.session_id)

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


def _snapshot(*, phase: RuntimePhase = RuntimePhase.READY) -> SessionSnapshot:
    session = SessionState(
        session_id="session-1",
        active_agent=AgentKey.MAIN,
        agents={AgentKey.MAIN: AgentSessionState(
            phase=phase,
            history=(MessageRecord("event-1", Role.USER, "hello", _now(), "turn-1"),),
        )},
        handoff_stack=(),
        created_at=_now(),
        updated_at=_now(),
    )
    return SessionSnapshot(session, _now())


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
