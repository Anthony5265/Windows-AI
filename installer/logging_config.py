import logging
import os
from pathlib import Path

# Determine the base directory for log files.  Default to the user's home
# directory when the USERPROFILE environment variable is not set (e.g. on
# non-Windows systems).
LOG_DIR = Path(os.environ.get("USERPROFILE", Path.home())) / "AI" / "Logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "installer.log"

# Set up a file handler that records only errors.  The handler is attached to
# the root logger so modules can obtain child loggers via ``logging.getLogger``
# and automatically inherit this configuration.
_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setLevel(logging.ERROR)
_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
_file_handler.setFormatter(_formatter)

# Configure the root logger level via environment variable.  When the level is
# set below ``ERROR`` a console handler is added so messages are visible in the
# terminal as well.  If the provided level is not recognised it defaults to
# ``ERROR``.
_level_name = os.getenv("WINDOWS_AI_LOG_LEVEL", "ERROR").upper()
_root_level = getattr(logging, _level_name, logging.ERROR)
_handlers = [_file_handler]
if _root_level < logging.ERROR:
    _console_handler = logging.StreamHandler()
    _console_handler.setLevel(_root_level)
    _console_handler.setFormatter(_formatter)
    _handlers.append(_console_handler)

logging.basicConfig(level=_root_level, handlers=_handlers)


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured to write errors to the log file."""

    return logging.getLogger(name)
