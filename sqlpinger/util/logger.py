import logging

import sqlpinger.config as config


class Logger:
    FORMAT = (
        "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d]"
        " - %(message)s"
    )

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        log_level = logging.DEBUG if config.verbose else logging.INFO
        logger = logging.getLogger(name)
        logger.setLevel(level=log_level)
        logger.propagate = False

        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(Logger.FORMAT))
            logger.addHandler(handler)

        for handler in logger.handlers:
            handler.setLevel(log_level)

        return logger
