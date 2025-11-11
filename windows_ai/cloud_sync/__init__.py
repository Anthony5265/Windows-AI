"""
Windows-AI Cloud Sync - Multi-Device Synchronization System

Provides secure end-to-end encrypted synchronization of conversations, settings,
automations, and workflows across multiple Windows-AI installations.

Key Features:
- End-to-end encryption using NaCl/libsodium
- Zero-knowledge architecture (server never sees plaintext)
- Conflict resolution strategies
- Offline queue for pending changes
- Background sync scheduler
- Multi-device coordination
"""

from .client import SyncClient
from .database import SyncDatabase
from .encryption import SyncEncryption
from .models import (
    SyncState,
    SyncConflict,
    ConflictResolution,
    DataCategory,
    DeviceInfo,
)
from .protocol import SyncProtocol

__all__ = [
    "SyncClient",
    "SyncDatabase",
    "SyncEncryption",
    "SyncState",
    "SyncConflict",
    "ConflictResolution",
    "DataCategory",
    "DeviceInfo",
    "SyncProtocol",
]

__version__ = "1.0.0"
