"""Tests for confined, revision-aware local workspace operations."""

import tempfile
import unittest
from hashlib import sha256
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

    def test_write_preserves_existing_crlf_without_inserting_blank_lines(self) -> None:
        content = "one\r\ntwo\r\n"

        written = self.workspace.write(Path("windows.txt"), content)
        restored = self.workspace.read(Path("windows.txt"))

        self.assertEqual(content, restored.content)
        self.assertEqual(written.revision, restored.revision)
        self.assertEqual(content.encode("utf-8"), self.workspace.resolve(Path("windows.txt")).read_bytes())

    def test_content_hash_reads_binary_bytes_without_changing_text_read_contract(self) -> None:
        path = Path("resume.pdf")
        raw = b"%PDF-1.7\x00\xff\x10binary"
        self.workspace.resolve(path).write_bytes(raw)

        with self.assertRaises(UnicodeError):
            self.workspace.read(path)
        self.assertEqual(sha256(raw).hexdigest(), self.workspace.content_hash(path))

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

    def test_batch_delete_reports_partial_success(self) -> None:
        self.workspace.write(Path("delete-me.txt"), "temporary")
        self.workspace.write(Path("folder") / "keep.txt", "preserved")

        result = self.workspace.delete_many(
            (Path("delete-me.txt"), Path("missing.txt"), Path("folder"))
        )

        self.assertEqual((Path("delete-me.txt"),), result.deleted)
        self.assertEqual((Path("missing.txt"), Path("folder")), tuple(item.path for item in result.failures))
        self.assertTrue((Path(self.temporary_dir.name) / "folder" / "keep.txt").exists())
