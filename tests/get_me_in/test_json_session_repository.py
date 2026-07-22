"""Atomic JSON session repository tests."""

from pathlib import Path
import tempfile
import unittest

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
            self.assertEqual(("session-1",), tuple(item.session_id for item in repository.list()))

    def test_rejects_path_like_session_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = JsonSessionRepository(Path(temporary), codec=SessionSnapshotCodec())
            with self.assertRaises(ValueError):
                repository.load("../not-a-session")
