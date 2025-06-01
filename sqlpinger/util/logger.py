import logging

import sqlpinger.config as config


class Logger:
    @staticmethod
    def get_logger(name):
        LOG_LEVEL = 'INFO'
        print(str(config.verbose))
        if config.verbose:
            LOG_LEVEL = 'DEBUG'
        logger = logging.getLogger(name)
        logger.setLevel(level=LOG_LEVEL)
        handler = logging.StreamHandler()
        handler.setLevel(LOG_LEVEL)

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d]"
            " - %(message)s"
        )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
