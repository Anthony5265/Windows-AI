"""
CloudSyncProvider - High-level API for cloud storage and synchronization
"""
from __future__ import annotations

import os
from typing import Optional, Dict, Any
from pathlib import Path
from . import CloudSync, FilesystemProvider, InMemoryProvider


class CloudSyncProvider:
    """High-level API for cloud sync operations"""

    def __init__(
        self,
        provider_type: str = "filesystem",
        storage_path: str = "cloud_storage",
        password: str = "default_encryption_key"
    ):
        """Initialize cloud sync provider

        Args:
            provider_type: Type of provider ('filesystem', 'memory')
            storage_path: Path for filesystem provider
            password: Encryption password
        """
        self.password = password

        # Initialize provider
        if provider_type == "filesystem":
            self.provider = FilesystemProvider(storage_path)
        elif provider_type == "memory":
            self.provider = InMemoryProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        # Initialize CloudSync
        self.sync = CloudSync(
            provider=self.provider,
            password=password,
            conflict_resolution="local"  # Default to local wins
        )

    def upload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload data to cloud storage

        Args:
            data: Dict containing 'name' and either 'content' (bytes/str) or 'file_path'

        Returns:
            Result dict with success status
        """
        try:
            name = data.get("name")
            if not name:
                return {"success": False, "error": "Missing 'name' field"}

            # Handle file upload
            if "file_path" in data:
                file_path = data["file_path"]
                if not os.path.exists(file_path):
                    return {"success": False, "error": f"File not found: {file_path}"}

                self.sync.backup_file(file_path, name)
                return {
                    "success": True,
                    "name": name,
                    "size": os.path.getsize(file_path)
                }

            # Handle raw content upload
            elif "content" in data:
                content = data["content"]
                if isinstance(content, str):
                    content = content.encode()

                from . import encrypt
                encrypted = encrypt(content, self.password)
                self.provider.upload(name, encrypted)

                return {
                    "success": True,
                    "name": name,
                    "size": len(content)
                }

            else:
                return {"success": False, "error": "Must provide either 'file_path' or 'content'"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def download(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Download data from cloud storage

        Args:
            name: Name of the file to download (if None, returns list of available files)

        Returns:
            Result dict with content or file list
        """
        try:
            if name is None:
                # Return list of available files (only works with filesystem provider)
                if isinstance(self.provider, FilesystemProvider):
                    files = []
                    for root, dirs, filenames in os.walk(self.provider.root):
                        for filename in filenames:
                            rel_path = os.path.relpath(
                                os.path.join(root, filename),
                                self.provider.root
                            )
                            files.append(rel_path)
                    return {"success": True, "files": files, "count": len(files)}
                else:
                    return {"success": False, "error": "List operation not supported for this provider"}

            # Download specific file
            encrypted_data = self.provider.download(name)
            if encrypted_data is None:
                return {"success": False, "error": f"File not found: {name}"}

            from . import decrypt
            decrypted_data = decrypt(encrypted_data, self.password)

            return {
                "success": True,
                "name": name,
                "content": decrypted_data.decode(errors="replace"),
                "size": len(decrypted_data)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def sync_file(self, file_path: str, name: str) -> Dict[str, Any]:
        """Synchronize a local file with cloud storage

        Args:
            file_path: Local file path
            name: Remote file name

        Returns:
            Result dict with sync action taken
        """
        try:
            action = self.sync.sync_file(file_path, name)
            return {
                "success": True,
                "action": action,
                "file": name
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def backup_profile(self, profile_path: str) -> Dict[str, Any]:
        """Backup user profile to cloud

        Args:
            profile_path: Path to user profile file

        Returns:
            Result dict
        """
        try:
            self.sync.backup_profile(profile_path)
            return {
                "success": True,
                "message": "Profile backed up successfully",
                "path": profile_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def restore_profile(self, profile_path: str) -> Dict[str, Any]:
        """Restore user profile from cloud

        Args:
            profile_path: Path where profile should be restored

        Returns:
            Result dict
        """
        try:
            success = self.sync.restore_profile(profile_path)
            if success:
                return {
                    "success": True,
                    "message": "Profile restored successfully",
                    "path": profile_path
                }
            else:
                return {"success": False, "error": "Profile not found in cloud storage"}
        except Exception as e:
            return {"success": False, "error": str(e)}
