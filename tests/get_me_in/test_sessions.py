"""Session aggregate domain tests."""

from datetime import datetime, timezone
import unittest

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role
from src.get_me_in.domain.sessions import AgentSessionState, RuntimePhase, SessionState


class SessionDomainTests(unittest.TestCase):
    def test_session_owns_agent_state_without_runtime_imports(self) -> None:
        record = MessageRecord("event-1", Role.USER, "hello", _now(), "turn-1")
        agent_state = AgentSessionState(history=(record,))
        session = SessionState(
            session_id="session-1",
            active_agent=AgentKey.MAIN,
            agents={AgentKey.MAIN: agent_state},
            handoff_stack=(),
            created_at=_now(),
            updated_at=_now(),
        )

        self.assertEqual(RuntimePhase.READY, session.agents[AgentKey.MAIN].phase)
        self.assertEqual("turn-1", session.agents[AgentKey.MAIN].history[0].turn_id)


def _now() -> datetime:
    return datetime(2026, 7, 22, tzinfo=timezone.utc)
