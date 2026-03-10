"""Re-export cloud_sync from windows_ai.cloud_sync for backwards compatibility."""

from windows_ai.cloud_sync import CloudSync, InMemoryProvider, FilesystemProvider, encrypt, decrypt

__all__ = ["CloudSync", "InMemoryProvider", "FilesystemProvider", "encrypt", "decrypt"]
