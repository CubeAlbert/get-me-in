"""Tests for read-only v2 workspace tool definitions."""

from pathlib import Path
import tempfile
import unittest

from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.tools import ToolSuccess
from src.get_me_in.tools.workspace import build_workspace_tools


class WorkspaceToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.workspace = LocalWorkspace(Path(self.temporary_dir.name))
        self.context = ToolContext("session", AgentKey.MAIN, CancellationToken(), workspace=self.workspace)
        self.executor = ToolExecutor(ToolCatalog(build_workspace_tools()))

    def test_read_returns_one_based_lines_and_revision(self) -> None:
        self.workspace.write(Path("notes.txt"), "one\ntwo\nthree")

        outcome = self.executor.execute(
            "read", "workspace_read", {"path": "notes.txt", "offset": 2, "limit": 1}, self.context
        )

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual(((2, "two"),), outcome.output["lines"])
        self.assertTrue(outcome.output["truncated"])
        self.assertTrue(outcome.output["revision"])

    def test_list_returns_single_directory_level(self) -> None:
        self.workspace.write(Path("folder") / "note.txt", "text")

        outcome = self.executor.execute("list", "workspace_list", {"path": "folder"}, self.context)

        self.assertIsInstance(outcome, ToolSuccess)
        self.assertEqual(({"name": "note.txt", "type": "file"},), outcome.output["entries"])

    def test_grep_and_file_search_respect_scope_and_limits(self) -> None:
        self.workspace.write(Path("notes") / "one.txt", "needle one\nneedle two")
        self.workspace.write(Path("other.txt"), "needle other")

        grep = self.executor.execute(
            "grep", "workspace_grep", {"pattern": r"needle\s+two", "path": "notes", "regex": True}, self.context
        )
        files = self.executor.execute(
            "files", "workspace_search_file", {"pattern": "*.txt", "path": "notes", "max_results": 1}, self.context
        )

        expected_path = str(Path("notes") / "one.txt")
        self.assertEqual({expected_path: [(2, "needle two")]}, grep.output["files"])
        self.assertEqual((expected_path,), files.output["files"])
        self.assertTrue(files.output["truncated"])

    def test_approved_write_replace_delete_and_move_operations(self) -> None:
        write = self.executor.execute("write", "workspace_write", {"path": "one.txt", "content": "old old"}, self.context)
        self.assertEqual("approval", write.kind)
        approved = type(self.context)("session", AgentKey.MAIN, CancellationToken(), workspace=self.workspace, approved=True)
        self.executor.execute("write", "workspace_write", {"path": "one.txt", "content": "old old"}, approved)
        replaced = self.executor.execute("replace", "workspace_replace", {"path": "one.txt", "old_str": "old", "new_str": "new"}, approved)
        moved = self.executor.execute("move", "workspace_move", {"src": "one.txt", "dst": "folder/two.txt"}, approved)
        deleted = self.executor.execute("delete", "workspace_delete", {"paths": ["folder/two.txt", "missing.txt"]}, approved)
        self.assertEqual(2, replaced.output["replacements"])
        self.assertTrue(moved.output["moved"])
        self.assertEqual(("folder\\two.txt",), deleted.output["deleted"])
        self.assertEqual("missing.txt", deleted.output["errors"][0]["path"])

    def test_edit_requires_current_revision_and_applies_multiple_original_lines(self) -> None:
        self.workspace.write(Path("edit.txt"), "one\ntwo\nthree")
        snapshot = self.workspace.read(Path("edit.txt"))
        approved = type(self.context)("session", AgentKey.MAIN, CancellationToken(), workspace=self.workspace, approved=True)
        outcome = self.executor.execute(
            "edit", "workspace_edit", {"path": "edit.txt", "revision": snapshot.revision,
              "edits": [{"line": 1, "old_content": "one", "content": "ONE"}, {"line": 3, "old_content": "three", "content": ""}]}, approved
        )
        stale = self.executor.execute(
            "stale", "workspace_edit", {"path": "edit.txt", "revision": snapshot.revision, "edits": []}, approved
        )
        self.assertEqual("ONE\ntwo", self.workspace.read(Path("edit.txt")).content.replace("\r\n", "\n"))
        self.assertEqual(2, outcome.output["edits_applied"])
        self.assertEqual("workspace_revision_mismatch", stale.code)

    def test_open_uses_the_injected_frontend(self) -> None:
        self.workspace.write(Path("preview.pdf"), "placeholder")
        frontend = _Frontend()
        approved = type(self.context)("session", AgentKey.MAIN, CancellationToken(), workspace=self.workspace, frontend=frontend, approved=True)
        outcome = self.executor.execute("open", "workspace_open", {"path": "preview.pdf"}, approved)
        self.assertTrue(outcome.output["opened"])
        self.assertEqual(Path(self.temporary_dir.name).resolve() / "preview.pdf", frontend.opened)


class _Frontend:
    def __init__(self) -> None:
        self.opened: Path | None = None

    def open_file(self, path: Path) -> None:
        self.opened = path
