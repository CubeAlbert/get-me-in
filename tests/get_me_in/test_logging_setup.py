import logging
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.logging_setup import configure_logging


class LoggingSetupTests(unittest.TestCase):
    def tearDown(self) -> None:
        logger = logging.getLogger("src.get_me_in")
        for handler in tuple(logger.handlers):
            logger.removeHandler(handler)
            handler.close()

    def test_writes_logs_and_replaces_existing_handlers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            log_dir = Path(temporary_dir)
            first_path = configure_logging(log_dir, "INFO", "app.log", 10485760, 5)
            second_path = configure_logging(log_dir, "INFO", "app.log", 10485760, 5)

            logging.getLogger("src.get_me_in.application.runtime").info("runtime ready")
            package_logger = logging.getLogger("src.get_me_in")
            self.assertEqual(2, len(package_logger.handlers))
            for handler in package_logger.handlers:
                handler.flush()

            content = second_path.read_text(encoding="utf-8")
            for handler in tuple(package_logger.handlers):
                package_logger.removeHandler(handler)
                handler.close()

        self.assertEqual(first_path, second_path)
        self.assertEqual(1, content.count("runtime ready"))

    def test_rejects_unknown_level(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            with self.assertRaisesRegex(ValueError, "Unsupported log level"):
                configure_logging(Path(temporary_dir), "VERBOSE", "app.log", 1, 0)

    def test_rejects_platform_specific_path_separators_in_file_name(self) -> None:
        invalid_names = ("nested/app.log", "nested\\app.log", "C:\\app.log")
        with tempfile.TemporaryDirectory() as temporary_dir:
            for file_name in invalid_names:
                with self.subTest(file_name=file_name):
                    with self.assertRaisesRegex(ValueError, "single ordinary file name"):
                        configure_logging(Path(temporary_dir), "INFO", file_name, 1, 0)
