"""Session-scoped workspace revision authorization tests."""

from pathlib import Path
import unittest

from src.get_me_in.application.workspace_access import WorkspaceAccessState
from src.get_me_in.ports.workspace import RevisionMismatchError


class WorkspaceAccessStateTests(unittest.TestCase):
    def test_revision_authorization_cannot_cross_sessions(self) -> None:
        access = WorkspaceAccessState()
        access.authorize_read("first", Path("resume.tex"), "revision")

        access.require_revision("first", Path("resume.tex"), "revision")
        with self.assertRaises(RevisionMismatchError):
            access.require_revision("second", Path("resume.tex"), "revision")

    def test_clear_session_requires_a_fresh_read(self) -> None:
        access = WorkspaceAccessState()
        access.authorize_read("session", Path("resume.tex"), "revision")
        access.clear_session("session")

        with self.assertRaises(RevisionMismatchError):
            access.require_revision("session", Path("resume.tex"), "revision")

    def test_consumed_revision_requires_a_fresh_read(self) -> None:
        access = WorkspaceAccessState()
        access.authorize_read("session", Path("resume.tex"), "revision")

        access.consume_revision("session", Path("resume.tex"), "revision")

        with self.assertRaises(RevisionMismatchError):
            access.require_revision("session", Path("resume.tex"), "revision")
