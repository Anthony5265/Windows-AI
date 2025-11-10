"""
Windows AI Auto-Update System

This module provides automatic update functionality for Windows AI,
including version checking, update downloading, and installation.

Components:
- version_manager: Version comparison and validation
- update_client: Client-side update checker and downloader
- update_server: FastAPI server for serving updates
"""

from .version_manager import VersionManager, Version
from .update_client import UpdateClient, UpdateStatus

__all__ = [
    "VersionManager",
    "Version",
    "UpdateClient",
    "UpdateStatus",
]

__version__ = "1.0.0"
