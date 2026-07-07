"""
Standard logging configuration for PitchPilot.

Provides basic console formatting and handles logging level setups.
Uses standard logging libraries instead of structlog.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """
    Configure standard logging for the application.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: Ignored, keeping standard formatting simple.
    """
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Simple clean string formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Reduce noise from third-party libraries
    for noisy_logger in [
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "websockets",
        "sqlalchemy.engine",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a standard logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured Logger.
    """
    return logging.getLogger(name)
