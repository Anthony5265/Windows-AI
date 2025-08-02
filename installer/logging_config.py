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
logging.basicConfig(level=logging.INFO, handlers=[_file_handler])


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured to write errors to the log file."""

    return logging.getLogger(name)
