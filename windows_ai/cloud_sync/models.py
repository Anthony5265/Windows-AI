"""
Data models for Windows-AI Cloud Sync system
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class DataCategory(str, Enum):
    """Types of data that can be synchronized"""
    CONVERSATIONS = "conversations"
    SETTINGS = "settings"
    AUTOMATIONS = "automations"
    WORKFLOWS = "workflows"
    DOCUMENTS = "documents"
    PLUGINS = "plugins"
    MODELS = "models"


class ConflictResolution(str, Enum):
    """Strategies for resolving sync conflicts"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MERGE = "merge"
    PROMPT_USER = "prompt_user"
    NEWEST_WINS = "newest_wins"


class SyncStatus(str, Enum):
    """Status of sync operations"""
    IDLE = "idle"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class DeviceInfo:
    """Information about a synced device"""
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_name: str = ""
    platform: str = ""
    os_version: str = ""
    app_version: str = ""
    last_seen: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    sync_priority: int = 100  # Lower number = higher priority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "platform": self.platform,
            "os_version": self.os_version,
            "app_version": self.app_version,
            "last_seen": self.last_seen.isoformat(),
            "is_active": self.is_active,
            "sync_priority": self.sync_priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceInfo":
        data = data.copy()
        if "last_seen" in data and isinstance(data["last_seen"], str):
            data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        return cls(**data)


@dataclass
class SyncState:
    """Tracks synchronization state for a data category"""
    category: DataCategory
    last_sync: Optional[datetime] = None
    last_pull: Optional[datetime] = None
    last_push: Optional[datetime] = None
    pending_changes: int = 0
    conflicts: int = 0
    status: SyncStatus = SyncStatus.IDLE
    error_message: Optional[str] = None
    sync_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "last_pull": self.last_pull.isoformat() if self.last_pull else None,
            "last_push": self.last_push.isoformat() if self.last_push else None,
            "pending_changes": self.pending_changes,
            "conflicts": self.conflicts,
            "status": self.status.value,
            "error_message": self.error_message,
            "sync_version": self.sync_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncState":
        data = data.copy()
        data["category"] = DataCategory(data["category"])
        data["status"] = SyncStatus(data["status"])
        for key in ["last_sync", "last_pull", "last_push"]:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


@dataclass
class SyncConflict:
    """Represents a sync conflict between local and remote data"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: DataCategory = DataCategory.CONVERSATIONS
    item_id: str = ""
    local_version: int = 0
    remote_version: int = 0
    local_data: Optional[Dict[str, Any]] = None
    remote_data: Optional[Dict[str, Any]] = None
    local_timestamp: Optional[datetime] = None
    remote_timestamp: Optional[datetime] = None
    resolution: Optional[ConflictResolution] = None
    resolved: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "category": self.category.value,
            "item_id": self.item_id,
            "local_version": self.local_version,
            "remote_version": self.remote_version,
            "local_data": self.local_data,
            "remote_data": self.remote_data,
            "local_timestamp": self.local_timestamp.isoformat() if self.local_timestamp else None,
            "remote_timestamp": self.remote_timestamp.isoformat() if self.remote_timestamp else None,
            "resolution": self.resolution.value if self.resolution else None,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncConflict":
        data = data.copy()
        data["category"] = DataCategory(data["category"])
        if data.get("resolution"):
            data["resolution"] = ConflictResolution(data["resolution"])
        for key in ["local_timestamp", "remote_timestamp", "created_at"]:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


@dataclass
class SyncChange:
    """Represents a pending change in the sync queue"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: DataCategory = DataCategory.CONVERSATIONS
    operation: str = "update"  # create, update, delete
    item_id: str = ""
    data: Optional[Dict[str, Any]] = None
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    synced: bool = False
    retry_count: int = 0
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_id": self.change_id,
            "category": self.category.value,
            "operation": self.operation,
            "item_id": self.item_id,
            "data": self.data,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "synced": self.synced,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncChange":
        data = data.copy()
        data["category"] = DataCategory(data["category"])
        if data.get("timestamp"):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class ConversationData:
    """Conversation data for synchronization"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    model: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "messages": self.messages,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationData":
        data = data.copy()
        for key in ["created_at", "updated_at"]:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


@dataclass
class SettingsData:
    """Settings data for synchronization"""
    category: str = "general"
    settings: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "settings": self.settings,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SettingsData":
        data = data.copy()
        if data.get("updated_at") and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


@dataclass
class AutomationData:
    """Automation/workflow data for synchronization"""
    automation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = "folder_watcher"  # folder_watcher, scheduled, workflow
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "automation_id": self.automation_id,
            "name": self.name,
            "type": self.type,
            "config": self.config,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationData":
        data = data.copy()
        for key in ["created_at", "updated_at"]:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)
