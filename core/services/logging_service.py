import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


_DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "..", "logs")
_DEFAULT_LOG_DIR = os.path.abspath(_DEFAULT_LOG_DIR)
_DEFAULT_LOG_FILE = os.path.join(_DEFAULT_LOG_DIR, "zeno_app.log")


def get_logger(
    name: str = "zeno",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Thread-safe, process-local logger factory with rotating file handler.

    - Keeps formatting consistent across the app
    - Prevents duplicate handlers for the same logger name
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if getattr(logger, "_zeno_configured", False):
        return logger

    os.makedirs(os.path.dirname(log_file or _DEFAULT_LOG_FILE), exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler
    file_path = log_file or _DEFAULT_LOG_FILE
    fh = RotatingFileHandler(file_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.propagate = False
    setattr(logger, "_zeno_configured", True)
    return logger
