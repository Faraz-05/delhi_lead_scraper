"""
Rotating file + console logger for the scraping pipeline.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_DIR


def get_logger(name: str = "lead_scraper") -> logging.Logger:
    """Return a configured logger that writes to both console and a rotating file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Rotating file handler (5 MB x 3 backups)
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    fh = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
