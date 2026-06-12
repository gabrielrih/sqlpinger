import logging

from unittest import TestCase

import sqlpinger.config as config
from sqlpinger.util.logger import Logger


class TestLogger(TestCase):
    def test_get_logger(self):
        logger = Logger.get_logger(__name__)
        self.assertIsInstance(logger, logging.Logger)

    def test_get_logger_does_not_add_duplicate_handlers(self):
        logger_name = f"{__name__}.duplicate"
        logging.getLogger(logger_name).handlers.clear()

        logger = Logger.get_logger(logger_name)
        Logger.get_logger(logger_name)

        self.assertEqual(len(logger.handlers), 1)

    def test_get_logger_updates_level_from_verbose_config(self):
        logger_name = f"{__name__}.level"
        logging.getLogger(logger_name).handlers.clear()

        try:
            config.verbose = False
            logger = Logger.get_logger(logger_name)
            self.assertEqual(logger.level, logging.INFO)
            self.assertEqual(logger.handlers[0].level, logging.INFO)

            config.verbose = True
            logger = Logger.get_logger(logger_name)
            self.assertEqual(logger.level, logging.DEBUG)
            self.assertEqual(logger.handlers[0].level, logging.DEBUG)
        finally:
            config.verbose = False
