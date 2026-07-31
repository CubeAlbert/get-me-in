"""Atomic JSON session repository tests."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.get_me_in.adapters.json_session_repository import JsonSessionRepository
from src.get_me_in.application.session_codec import SessionSnapshotCodec
from tests.get_me_in.test_session_codec import _snapshot


class JsonSessionRepositoryTests(unittest.TestCase):
    def test_save_load_and_list_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonSessionRepository(Path(temporary), codec=SessionSnapshotCodec())
            repository.save(_snapshot())

            loaded = repository.load("session-1")

            self.assertEqual("session-1", loaded.session.session_id)
            previews = repository.list()
            self.assertEqual(("session-1",), tuple(item.session_id for item in previews))
            self.assertEqual("hello", previews[0].preview)

    def test_dump_uses_separate_directory_and_list_ignores_legacy_root_dumps(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = JsonSessionRepository(root, codec=SessionSnapshotCodec())
            snapshot = _snapshot()
            repository.save(snapshot)
            legacy_dump = root / "old-session.dump.json"
            legacy_dump.write_text("not a canonical session", encoding="utf-8")

            dump_path = repository.dump(snapshot)

            self.assertEqual(root / "dumps" / "session-1.json", dump_path)
            self.assertTrue(dump_path.exists())
            self.assertTrue(legacy_dump.exists())
            self.assertEqual("session-1", repository.load("session-1").session.session_id)
            self.assertEqual(("session-1",), tuple(item.session_id for item in repository.list()))

    def test_rejects_path_like_session_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonSessionRepository(Path(temporary), codec=SessionSnapshotCodec())
            with self.assertRaises(ValueError):
                repository.load("../not-a-session")

    def test_failed_replace_preserves_existing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonSessionRepository(Path(temporary), codec=SessionSnapshotCodec())
            repository.save(_snapshot())
            with patch.object(Path, "replace", side_effect=OSError("disk failure")):
                with self.assertRaises(OSError):
                    repository.save(_snapshot())

            self.assertEqual("session-1", repository.load("session-1").session.session_id)
