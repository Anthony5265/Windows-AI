"""
Sync protocol for Windows-AI Cloud Sync

Handles communication with the sync server using REST API with
pull, push, and bidirectional sync operations.
"""

import gzip
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import urllib.request
    import urllib.error

from .models import (
    DataCategory,
    SyncChange,
    SyncConflict,
    ConflictResolution,
    DeviceInfo,
)
from .encryption import SyncEncryption, EncryptionKey


class SyncProtocol:
    """
    Handles communication with the sync server

    Features:
    - REST API for sync operations
    - Incremental sync (only changed data)
    - Compression for bandwidth efficiency
    - Retry logic with exponential backoff
    - Protocol versioning
    """

    PROTOCOL_VERSION = "1.0"
    MAX_RETRIES = 4
    BASE_RETRY_DELAY = 2  # seconds

    def __init__(
        self,
        server_url: str,
        encryption: SyncEncryption,
        encryption_key: EncryptionKey,
        device_id: str,
        auth_token: Optional[str] = None,
        timeout: int = 30,
    ):
        self.server_url = server_url.rstrip("/")
        self.encryption = encryption
        self.encryption_key = encryption_key
        self.device_id = device_id
        self.auth_token = auth_token
        self.timeout = timeout
        self.use_httpx = HTTPX_AVAILABLE

        if self.use_httpx:
            self.client = httpx.Client(timeout=timeout)
        else:
            self.client = None

    def close(self) -> None:
        """Close HTTP client"""
        if self.client and self.use_httpx:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {
            "Content-Type": "application/json",
            "X-Protocol-Version": self.PROTOCOL_VERSION,
            "X-Device-ID": self.device_id,
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            retry_count: Current retry attempt

        Returns:
            Response data as dictionary

        Raises:
            Exception: If request fails after all retries
        """
        url = urljoin(self.server_url, endpoint)
        headers = self._get_headers()

        try:
            if self.use_httpx:
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                return response.json()
            else:
                # Fallback to urllib
                req_data = json.dumps(data).encode() if data else None
                request = urllib.request.Request(
                    url,
                    data=req_data,
                    headers=headers,
                    method=method,
                )
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode())

        except Exception as e:
            if retry_count < self.MAX_RETRIES:
                # Exponential backoff
                delay = self.BASE_RETRY_DELAY * (2 ** retry_count)
                time.sleep(delay)
                return self._make_request(method, endpoint, data, retry_count + 1)
            else:
                raise Exception(f"Request failed after {self.MAX_RETRIES} retries: {e}")

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        return gzip.compress(data, compresslevel=6)

    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress gzip data"""
        return gzip.decompress(data)

    # ========== Device Registration ==========

    def register_device(self, device_info: DeviceInfo) -> Dict[str, Any]:
        """
        Register device with sync server

        Args:
            device_info: Device information

        Returns:
            Server response with device_id and auth_token
        """
        response = self._make_request(
            "POST",
            "/api/sync/v1/devices/register",
            data=device_info.to_dict(),
        )
        return response

    def update_device_status(self, is_active: bool) -> Dict[str, Any]:
        """
        Update device activity status

        Args:
            is_active: Whether device is active

        Returns:
            Server response
        """
        response = self._make_request(
            "PUT",
            f"/api/sync/v1/devices/{self.device_id}/status",
            data={"is_active": is_active, "last_seen": datetime.utcnow().isoformat()},
        )
        return response

    def list_devices(self) -> List[DeviceInfo]:
        """
        List all registered devices for this user

        Returns:
            List of DeviceInfo objects
        """
        response = self._make_request("GET", "/api/sync/v1/devices")
        devices = []
        for device_data in response.get("devices", []):
            devices.append(DeviceInfo.from_dict(device_data))
        return devices

    # ========== Pull Sync (Download Changes) ==========

    def pull_changes(
        self,
        category: DataCategory,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Pull changes from server for a data category

        Args:
            category: Data category to sync
            since: Only get changes after this timestamp
            limit: Maximum number of changes to fetch

        Returns:
            List of encrypted change records
        """
        params = {
            "category": category.value,
            "limit": limit,
        }
        if since:
            params["since"] = since.isoformat()

        response = self._make_request(
            "GET",
            f"/api/sync/v1/pull?{self._encode_params(params)}",
        )

        changes = response.get("changes", [])
        return changes

    def pull_and_decrypt_changes(
        self,
        category: DataCategory,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Pull and decrypt changes from server

        Args:
            category: Data category to sync
            since: Only get changes after this timestamp
            limit: Maximum number of changes to fetch

        Returns:
            List of decrypted change records
        """
        encrypted_changes = self.pull_changes(category, since, limit)
        decrypted_changes = []

        for change in encrypted_changes:
            try:
                # Decrypt the data field
                if "data" in change and change["data"]:
                    encrypted_data = change["data"]
                    if isinstance(encrypted_data, str):
                        decrypted_data = self.encryption.decrypt_from_base64(
                            encrypted_data,
                            self.encryption_key,
                        )
                        change["data"] = json.loads(decrypted_data)
                decrypted_changes.append(change)
            except Exception as e:
                print(f"Failed to decrypt change {change.get('change_id')}: {e}")
                continue

        return decrypted_changes

    # ========== Push Sync (Upload Changes) ==========

    def push_changes(
        self,
        category: DataCategory,
        changes: List[SyncChange],
        compress: bool = True,
    ) -> Dict[str, Any]:
        """
        Push changes to server

        Args:
            category: Data category
            changes: List of changes to push
            compress: Whether to compress data

        Returns:
            Server response with sync results
        """
        # Encrypt changes
        encrypted_changes = []
        for change in changes:
            encrypted_change = change.to_dict()
            if change.data:
                encrypted_data = self.encryption.encrypt_json(change.data, self.encryption_key)
                encrypted_change["data"] = self.encryption.encrypt_to_base64(
                    json.dumps(change.data).encode(),
                    self.encryption_key,
                )
            encrypted_changes.append(encrypted_change)

        payload = {
            "category": category.value,
            "changes": encrypted_changes,
            "device_id": self.device_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = self._make_request(
            "POST",
            "/api/sync/v1/push",
            data=payload,
        )

        return response

    # ========== Bidirectional Sync ==========

    def sync(
        self,
        category: DataCategory,
        local_changes: List[SyncChange],
        since: Optional[datetime] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Perform bidirectional sync (pull and push in one operation)

        Args:
            category: Data category to sync
            local_changes: Local changes to push
            since: Only get remote changes after this timestamp

        Returns:
            Tuple of (remote_changes, push_response)
        """
        # First, pull remote changes
        remote_changes = self.pull_and_decrypt_changes(category, since)

        # Then, push local changes
        push_response = {}
        if local_changes:
            push_response = self.push_changes(category, local_changes)

        return remote_changes, push_response

    # ========== Conflict Detection ==========

    def detect_conflicts(
        self,
        local_changes: List[Dict[str, Any]],
        remote_changes: List[Dict[str, Any]],
    ) -> List[SyncConflict]:
        """
        Detect conflicts between local and remote changes

        Args:
            local_changes: Local changes
            remote_changes: Remote changes

        Returns:
            List of SyncConflict objects
        """
        conflicts = []
        local_by_id = {c["item_id"]: c for c in local_changes}
        remote_by_id = {c["item_id"]: c for c in remote_changes}

        # Find items that exist in both and have different versions
        for item_id in local_by_id.keys() & remote_by_id.keys():
            local = local_by_id[item_id]
            remote = remote_by_id[item_id]

            # Check if versions differ
            local_version = local.get("version", 1)
            remote_version = remote.get("version", 1)

            if local_version != remote_version:
                conflict = SyncConflict(
                    category=DataCategory(local.get("category", "conversations")),
                    item_id=item_id,
                    local_version=local_version,
                    remote_version=remote_version,
                    local_data=local.get("data"),
                    remote_data=remote.get("data"),
                    local_timestamp=datetime.fromisoformat(local["timestamp"]) if "timestamp" in local else None,
                    remote_timestamp=datetime.fromisoformat(remote["timestamp"]) if "timestamp" in remote else None,
                )
                conflicts.append(conflict)

        return conflicts

    def resolve_conflict(
        self,
        conflict: SyncConflict,
        resolution: ConflictResolution,
    ) -> Dict[str, Any]:
        """
        Send conflict resolution to server

        Args:
            conflict: The conflict to resolve
            resolution: Resolution strategy

        Returns:
            Server response
        """
        response = self._make_request(
            "POST",
            "/api/sync/v1/conflicts/resolve",
            data={
                "conflict_id": conflict.conflict_id,
                "resolution": resolution.value,
                "device_id": self.device_id,
            },
        )
        return response

    # ========== Sync History ==========

    def get_sync_history(
        self,
        category: Optional[DataCategory] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get sync history from server

        Args:
            category: Optional category filter
            limit: Maximum number of records

        Returns:
            List of sync history records
        """
        params = {"limit": limit}
        if category:
            params["category"] = category.value

        response = self._make_request(
            "GET",
            f"/api/sync/v1/history?{self._encode_params(params)}",
        )

        return response.get("history", [])

    # ========== Utility Methods ==========

    def _encode_params(self, params: Dict[str, Any]) -> str:
        """Encode URL parameters"""
        from urllib.parse import urlencode
        return urlencode(params)

    def ping(self) -> Dict[str, Any]:
        """Ping server to check connectivity"""
        try:
            response = self._make_request("GET", "/api/sync/v1/ping")
            return {"status": "ok", "response": response}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities"""
        response = self._make_request("GET", "/api/sync/v1/info")
        return response
