"""Logging configuration for JARVIS.

Provides a consistent, structured logging setup across all modules.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure logs directory exists
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Console handler (color-free, clean output)
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.DEBUG)

# File handler (detailed logs)
_file_handler = logging.FileHandler(LOG_DIR / "jarvis.log", encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)

# Formatter
_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_console_handler.setFormatter(_formatter)
_file_handler.setFormatter(_formatter)


def setup_logger(level: str = "INFO") -> None:
    """Configure the root logger with console and file handlers.

    Args:
        level: Logging level as a string (DEBUG, INFO, WARNING, ERROR).
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on re-configuration
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(_console_handler)
    if not any(
        isinstance(h, logging.FileHandler) and h.baseFilename == str(LOG_DIR / "jarvis.log")
        for h in root.handlers
    ):
        root.addHandler(_file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance for the given module name.

    Args:
        name: Usually ``__name__`` from the calling module.

    Returns:
        Configured ``logging.Logger``.
    """
    return logging.getLogger(name)