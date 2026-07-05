import logging
import sys
from typing import Any

def get_logger(name: str) -> logging.Logger:
    """
    Configures and retrieves a structured logger for TruthGuard components.

    Args:
        name: Name of the logger, typically __name__.

    Returns:
        logging.Logger: A configured structured logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Structured log format using JSON-like key-values
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
