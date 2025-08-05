import logging

from installer.logging_config import get_logger


def test_get_logger_returns_logger() -> None:
    """Smoke test for the logging configuration module."""
    logger = get_logger(__name__)
    assert isinstance(logger, logging.Logger)

