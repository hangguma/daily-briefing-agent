"""
Logging setup - console + file output.

Why this design?
- Replaces scattered print() calls with a single configured logger that writes
  to BOTH the console and a timestamped file under outputs/logs/.
- Centralized here so every module shares the same format and handlers.
- Plays well with AWS CloudWatch in Step 4: on Lambda we write to the console
  only (CloudWatch captures stdout), skipping the file handler.
"""

import logging
import os
from datetime import datetime

_CONFIGURED = False
LOG_DIR = os.path.join("outputs", "logs")


def setup_logging(to_file: bool = True) -> logging.Logger:
    """Configure and return the project logger.

    Args:
        to_file: also write logs to outputs/logs/run_<timestamp>.log.
                 Set False on Lambda (CloudWatch captures stdout already).

    Returns:
        The configured "briefing" logger. Safe to call multiple times.
    """
    global _CONFIGURED
    logger = logging.getLogger("briefing")

    if _CONFIGURED:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    # Console handler (always)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler (optional)
    if to_file:
        os.makedirs(LOG_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = os.path.join(LOG_DIR, f"run_{stamp}.log")
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        logger.info("Logging to file: %s", path)

    _CONFIGURED = True
    return logger


def get_logger() -> logging.Logger:
    """Return the project logger (configures with defaults if not yet set up)."""
    if not _CONFIGURED:
        return setup_logging()
    return logging.getLogger("briefing")
