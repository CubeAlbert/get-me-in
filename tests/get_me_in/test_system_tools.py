"""Tests for stateless system tool definitions."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolFailure, ToolSuccess
from src.get_me_in.tools.system import build_system_tools


class SystemToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.workspace = LocalWorkspace(Path(self.temporary_dir.name))
        self.context = ToolContext(
            "session",
            AgentKey.MAIN,
            CancellationToken(),
            workspace=self.workspace,
        )
        self.executor = ToolExecutor(ToolCatalog(build_system_tools(_FixedClock())))

    def test_datetime_tool_uses_the_injected_clock(self) -> None:
        outcome = self.executor.execute("call", "get_current_datetime", {}, self.context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual("2026-07-21 10:30:00 +0000", outcome.output)

    def test_working_directory_is_the_workspace_root(self) -> None:
        outcome = self.executor.execute("call", "get_working_dir", {}, self.context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual(str(Path(self.temporary_dir.name).resolve()), outcome.output)

    def test_working_directory_requires_a_workspace(self) -> None:
        context = ToolContext("session", AgentKey.MAIN, CancellationToken())

        outcome = self.executor.execute("call", "get_working_dir", {}, context)

        self.assertIsInstance(outcome, ToolFailure)
        self.assertEqual("workspace_unavailable", outcome.code)


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 21, 10, 30, tzinfo=timezone.utc)
