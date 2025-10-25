"""Smoke tests for installer.logging_config."""

from installer.logging_config import get_logger


def test_get_logger_returns_named_logger():
    """get_logger should return a logger with the requested name."""

    logger = get_logger("smoke")
    assert logger.name == "smoke"
