"""Tests for explicitly authorized external-file access."""

from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.authorized_file_reader import AuthorizedFileReader
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolApproval, ToolFailure, ToolSuccess
from src.get_me_in.tools.customer_file import build_customer_file_tools


class CustomerFileToolTests(unittest.TestCase):
    def test_approval_allows_supported_absolute_file_without_path_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.txt"
            path.write_text("one\ntwo", encoding="utf-8")
            executor = ToolExecutor(ToolCatalog(build_customer_file_tools()))
            context = ToolContext("session", AgentKey.MAIN, CancellationToken(), external_files=AuthorizedFileReader(), approved=True)
            outcome = executor.execute("call", "read_customer_file", {"path": str(path), "offset": 2}, context)
            self.assertIsInstance(outcome, ToolSuccess)
            self.assertEqual(((2, "two"),), outcome.output["lines"])

    def test_unapproved_call_is_intercepted_before_reader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.txt"
            path.write_text("text", encoding="utf-8")
            executor = ToolExecutor(ToolCatalog(build_customer_file_tools()))
            context = ToolContext("session", AgentKey.MAIN, CancellationToken(), external_files=AuthorizedFileReader())
            outcome = executor.execute("call", "read_customer_file", {"path": str(path)}, context)
            self.assertIsInstance(outcome, ToolApproval)

    def test_relative_and_unsupported_paths_still_fail_after_approval(self) -> None:
        executor = ToolExecutor(ToolCatalog(build_customer_file_tools()))
        context = ToolContext("session", AgentKey.MAIN, CancellationToken(), external_files=AuthorizedFileReader(), approved=True)

        relative = executor.execute("call", "read_customer_file", {"path": "resume.txt"}, context)
        self.assertEqual(ToolFailure("external_path_not_absolute", "Customer file path must be absolute"), relative)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.tex"
            path.write_text("\\documentclass{article}", encoding="utf-8")
            unsupported = executor.execute("call", "read_customer_file", {"path": str(path)}, context)
            self.assertIsInstance(unsupported, ToolFailure)
            self.assertEqual("external_file_read_failed", unsupported.code)
