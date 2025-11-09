"""
Compatibility shim for legacy plugin manager imports.

This module provides backward compatibility for tests and code that import
from 'plugins.manager' instead of the new structure.
"""

# Import from the installer plugins module for backward compatibility
from installer.plugins.manager import (
    Plugin,
    PluginManager,
    load_catalog,
    CATALOG_PATH,
    STATE_PATH,
)

# For tests that use SANDBOX_DIR
import tempfile
from pathlib import Path

SANDBOX_DIR = Path(tempfile.gettempdir()) / "windows_ai_sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

__all__ = [
    "Plugin",
    "PluginManager",
    "load_catalog",
    "CATALOG_PATH",
    "STATE_PATH",
    "SANDBOX_DIR",
]
