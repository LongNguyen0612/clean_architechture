import logging

from asgi_correlation_id import CorrelationIdFilter

LOGGING_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def setup_app_level_logger(name: str, level: str = "INFO") -> logging.Logger:
    if level not in LOGGING_VALID_LEVELS:
        raise ValueError(
            f"'{level}' is not a valid logging level. Valid levels: {LOGGING_VALID_LEVELS}"
        )
    level = logging.getLevelName(level)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        (
            "%(asctime)s"
            " - [%(correlation_id)s]"
            " - %(process)s"
            " - %(threadName)s"
            " - %(name)s"
            " - %(funcName)s:%(lineno)s"
            " - %(levelname)s"
            " - %(message)s"
        )
    )
    # ISO8061 FORMAT
    formatter.default_time_format = "%Y-%m-%dT%H:%M:%S"

    stream_handler = logging.StreamHandler()
    stream_handler.addFilter(CorrelationIdFilter(default_value="-", uuid_length=32))
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    logger.addHandler(stream_handler)
    return logger