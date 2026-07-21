"""Tests for confined, revision-aware local workspace operations."""

import tempfile
import unittest
from pathlib import Path

from src.get_me_in.adapters.local_workspace import LocalWorkspace
from src.get_me_in.ports.workspace import RevisionMismatchError, WorkspacePathError


class LocalWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.workspace = LocalWorkspace(Path(self.temporary_dir.name))

    def test_write_read_and_revision_checked_edit(self) -> None:
        original = self.workspace.write(Path("note.txt"), "one")
        updated = self.workspace.edit(Path("note.txt"), original.revision, "two")

        self.assertEqual("two", self.workspace.read(Path("note.txt")).content)
        self.assertNotEqual(original.revision, updated.revision)

    def test_stale_edit_is_rejected(self) -> None:
        original = self.workspace.write(Path("note.txt"), "one")
        self.workspace.write(Path("note.txt"), "two")

        with self.assertRaises(RevisionMismatchError):
            self.workspace.edit(Path("note.txt"), original.revision, "three")

    def test_path_cannot_escape_root(self) -> None:
        with self.assertRaises(WorkspacePathError):
            self.workspace.resolve(Path("..") / "outside.txt")

    def test_read_lines_and_search_report_one_based_line_numbers(self) -> None:
        self.workspace.write(Path("notes.txt"), "first\nneedle here\nlast")

        lines = self.workspace.read_lines(Path("notes.txt"), offset=1, limit=1)
        matches = self.workspace.search("needle", glob="*.txt")

        self.assertEqual((2, "needle here"), (lines[0].number, lines[0].content))
        self.assertEqual((Path("notes.txt"), 2), (matches[0].path, matches[0].line.number))
