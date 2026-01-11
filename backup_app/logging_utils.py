from __future__ import annotations

import logging
from pathlib import Path

_LOGGER_NAME = "backup"


def get_logger(log_path: str | Path = "backup.log") -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_path = Path(log_path)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
