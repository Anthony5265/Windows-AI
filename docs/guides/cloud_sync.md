# Windows-AI Cloud Sync Documentation

## Overview

Windows-AI Cloud Sync provides secure, end-to-end encrypted synchronization of your conversations, settings, automations, and workflows across multiple devices. With zero-knowledge architecture, your data remains encrypted on the server - only you can decrypt it.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Data Categories](#data-categories)
- [Conflict Resolution](#conflict-resolution)
- [Multi-Device Setup](#multi-device-setup)
- [Offline Mode](#offline-mode)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Features

### Core Features
- **End-to-End Encryption**: All data encrypted client-side using NaCl/libsodium
- **Zero-Knowledge Architecture**: Server never sees your plaintext data
- **Multi-Device Sync**: Seamlessly sync across Windows, Linux, and macOS
- **Background Sync**: Automatic sync every 5 minutes
- **Offline Queue**: Changes queued when offline, synced when reconnected
- **Conflict Resolution**: Multiple strategies for handling sync conflicts
- **Selective Sync**: Choose which data categories to sync
- **Bandwidth Efficient**: Compression and incremental sync

### Security Features
- Argon2id password-based key derivation
- XSalsa20-Poly1305 authenticated encryption
- HMAC integrity verification
- Encrypted key backup and recovery
- Audit trail with SHA-256 hashing
- Certificate pinning ready

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Windows-AI Client                     │
│                                                          │
│  ┌────────────────┐      ┌──────────────────┐          │
│  │  SyncClient    │─────▶│  SyncDatabase    │          │
│  │  (Background)  │      │  (SQLite)        │          │
│  └────────┬───────┘      └──────────────────┘          │
│           │                                              │
│           ▼                                              │
│  ┌────────────────┐      ┌──────────────────┐          │
│  │ SyncEncryption │      │  SyncProtocol    │          │
│  │ (E2E Crypto)   │      │  (REST API)      │          │
│  └────────────────┘      └────────┬─────────┘          │
└──────────────────────────────────┼──────────────────────┘
                                    │
                          HTTPS + E2E Encryption
                                    │
┌──────────────────────────────────▼──────────────────────┐
│                  Sync Server (Express.js)                │
│                                                          │
│  ┌────────────────┐      ┌──────────────────┐          │
│  │ REST API       │      │  JWT Auth        │          │
│  │ /api/sync/v1/* │      │                  │          │
│  └────────┬───────┘      └──────────────────┘          │
│           │                                              │
│           ▼                                              │
│  ┌────────────────┐      ┌──────────────────┐          │
│  │  Database      │      │  Storage Backend │          │
│  │  (SQLite)      │      │  (S3-compatible) │          │
│  └────────────────┘      └──────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Local Changes**: User makes changes (e.g., new conversation)
2. **Queue**: Changes added to local sync queue
3. **Encryption**: Changes encrypted with user's encryption key
4. **Upload**: Encrypted changes pushed to sync server
5. **Server Storage**: Server stores encrypted data (cannot decrypt)
6. **Other Devices**: Other devices pull encrypted changes
7. **Decryption**: Devices decrypt using their copy of encryption key
8. **Apply**: Changes applied to local database

## Getting Started

### Installation

1. **Install Dependencies**:
```bash
# Python dependencies
pip install pynacl httpx

# Server dependencies
cd update-server/sync
npm install
```

2. **Start Sync Server**:
```bash
cd update-server/sync
npm start
```

Server will start on `http://localhost:8765`

### First-Time Setup

1. **Create Account**:
```python
from windows_ai.cloud_sync.client import SyncClient

# Initialize client
client = SyncClient(
    db_path="~/.windows-ai/sync.db",
    server_url="http://localhost:8765",
    password="your_secure_password",  # Used for encryption
    device_name="My Laptop",
)
```

2. **Start Background Sync**:
```python
client.start_background_sync()
```

3. **Queue Some Changes**:
```python
client.queue_change(
    category=DataCategory.CONVERSATIONS,
    operation="create",
    item_id="conv_123",
    data={
        "title": "My Conversation",
        "messages": [...],
        "model": "gpt-4"
    }
)
```

4. **Manual Sync** (optional):
```python
# Sync all categories
client.sync_all()

# Or sync specific category
client.sync_category(DataCategory.CONVERSATIONS)
```

## Configuration

### Client Configuration

```python
client = SyncClient(
    db_path="~/.windows-ai/sync.db",
    server_url="http://your-sync-server.com",
    password="your_secure_password",
    device_name="My Device",

    # Optional settings
    auth_token="jwt_token",  # If you have existing token
    sync_interval=300,  # 5 minutes (default)
    auto_resolve_conflicts=False,  # Manual conflict resolution
    conflict_strategy=ConflictResolution.NEWEST_WINS,
)
```

### Selective Sync

Choose which data categories to sync:

```python
from windows_ai.cloud_sync.models import DataCategory

# Sync only conversations and settings
client.set_selective_sync([
    DataCategory.CONVERSATIONS,
    DataCategory.SETTINGS
])

# Sync all categories
client.set_selective_sync(None)
```

### Conflict Resolution Strategies

```python
from windows_ai.cloud_sync.models import ConflictResolution

# Server version always wins
client.set_conflict_strategy(ConflictResolution.SERVER_WINS)

# Client version always wins
client.set_conflict_strategy(ConflictResolution.CLIENT_WINS)

# Newest version wins (based on timestamp)
client.set_conflict_strategy(ConflictResolution.NEWEST_WINS)

# Prompt user for each conflict
client.set_conflict_strategy(ConflictResolution.PROMPT_USER)

# Enable auto-resolution
client.enable_auto_resolve(True)
```

## Data Categories

Windows-AI syncs the following data categories:

### 1. Conversations
- Full chat history with messages
- Conversation metadata (title, model, tags)
- Timestamps and versioning

### 2. Settings
- User preferences
- Application configuration
- Theme and UI settings

### 3. Automations
- Folder watchers
- Scheduled tasks
- Automation rules

### 4. Workflows
- Visual workflow definitions
- Workflow state and history

### 5. Documents
- RAG indexed documents (metadata only by default)
- Optional full document sync

### 6. Plugins
- Plugin configurations
- Plugin state and preferences

### 7. Models
- Model preferences
- Custom prompts
- Model settings

## Conflict Resolution

### What is a Conflict?

A conflict occurs when the same item is modified on multiple devices before sync completes.

Example:
1. Device A modifies conversation "conv_123" → version 2
2. Device B modifies conversation "conv_123" → version 2 (different content)
3. Both try to sync → CONFLICT

### Resolution Strategies

#### 1. Server Wins
```python
conflict_strategy = ConflictResolution.SERVER_WINS
# Remote version always applied, local changes discarded
```

#### 2. Client Wins
```python
conflict_strategy = ConflictResolution.CLIENT_WINS
# Local version always uploaded, remote changes discarded
```

#### 3. Newest Wins
```python
conflict_strategy = ConflictResolution.NEWEST_WINS
# Version with latest timestamp wins
```

#### 4. Prompt User
```python
conflict_strategy = ConflictResolution.PROMPT_USER

# Register callback
def handle_conflict(conflict):
    print(f"Conflict in {conflict.category}")
    print(f"Local: {conflict.local_data}")
    print(f"Remote: {conflict.remote_data}")

    # User chooses resolution
    choice = input("Keep (L)ocal or (R)emote? ")
    resolution = (ConflictResolution.CLIENT_WINS
                 if choice == 'L'
                 else ConflictResolution.SERVER_WINS)

    client.resolve_conflict_manually(conflict.conflict_id, resolution)

client.on_conflict(handle_conflict)
```

### Manual Conflict Resolution

```python
# Get all conflicts
conflicts = client.get_conflicts()

for conflict in conflicts:
    print(f"Conflict ID: {conflict.conflict_id}")
    print(f"Item: {conflict.item_id}")
    print(f"Local version: {conflict.local_version}")
    print(f"Remote version: {conflict.remote_version}")

    # Resolve manually
    client.resolve_conflict_manually(
        conflict.conflict_id,
        ConflictResolution.CLIENT_WINS
    )
```

## Multi-Device Setup

### Adding a New Device

1. **Install Windows-AI** on new device

2. **Use Same Password**:
```python
# IMPORTANT: Use the SAME password on all devices
# This password derives your encryption key
client = SyncClient(
    db_path="~/.windows-ai/sync.db",
    server_url="http://your-sync-server.com",
    password="same_password_as_other_devices",
    device_name="My New Device",
)
```

3. **Initial Sync**:
```python
# Start background sync
client.start_background_sync()

# Or pull everything immediately
for category in DataCategory:
    client.pull_now(category)
```

### Device Management

```python
# List all registered devices
devices = client.get_device_list()

for device in devices:
    print(f"Device: {device.device_name}")
    print(f"Platform: {device.platform}")
    print(f"Last seen: {device.last_seen}")
    print(f"Active: {device.is_active}")
```

### Device Priority

Set which device has priority in conflicts:

```python
device_info = client.device_info
device_info.sync_priority = 1  # Lower = higher priority (default 100)
client.db.register_device(device_info)
```

## Offline Mode

### How It Works

1. **Offline**: Network unavailable
2. **Queue**: All changes added to local queue
3. **Retry**: Background sync attempts connection
4. **Online**: Connection restored
5. **Sync**: All queued changes uploaded

### Queue Management

```python
# Check queue status
status = client.get_queue_status()
print(f"Pending conversations: {status[DataCategory.CONVERSATIONS]}")
print(f"Pending settings: {status[DataCategory.SETTINGS]}")

# Manual queue operations
change_id = client.queue_change(
    category=DataCategory.CONVERSATIONS,
    operation="update",
    item_id="conv_123",
    data={"title": "Updated Title"}
)

# Force sync when online
client.sync_all()
```

### Retry Logic

The sync client uses exponential backoff for retries:
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds
- Attempt 4: Wait 8 seconds
- Attempt 5: Wait 16 seconds (max)

## API Reference

### SyncClient

#### Initialization
```python
SyncClient(
    db_path: str | Path,
    server_url: str,
    password: str,
    device_name: Optional[str] = None,
    auth_token: Optional[str] = None,
    sync_interval: int = 300,
    auto_resolve_conflicts: bool = False,
    conflict_strategy: ConflictResolution = ConflictResolution.NEWEST_WINS
)
```

#### Methods

**Sync Control**:
- `start_background_sync()` - Start automatic sync
- `stop_background_sync()` - Stop automatic sync
- `sync_all()` - Sync all categories
- `sync_category(category)` - Sync specific category
- `push_now(category)` - Push local changes immediately
- `pull_now(category)` - Pull remote changes immediately

**Queue Management**:
- `queue_change(category, operation, item_id, data)` - Add change to queue
- `get_queue_status()` - Get pending changes per category

**Conflict Management**:
- `get_conflicts(category=None)` - Get unresolved conflicts
- `resolve_conflict_manually(conflict_id, resolution)` - Resolve conflict

**Configuration**:
- `set_selective_sync(categories)` - Set categories to sync
- `set_conflict_strategy(strategy)` - Set conflict resolution strategy
- `enable_auto_resolve(enabled)` - Enable/disable auto-resolution

**Status**:
- `get_sync_status()` - Get overall sync status
- `get_device_list()` - Get all registered devices
- `ping_server()` - Check server connectivity

**Callbacks**:
- `on_sync_complete(callback)` - Called after sync
- `on_conflict(callback)` - Called when conflict detected
- `on_error(callback)` - Called on sync error

### REST API Endpoints

**Authentication**:
- `POST /api/sync/v1/auth/register` - Register new user
- `POST /api/sync/v1/auth/login` - Login and get JWT token

**Device Management**:
- `POST /api/sync/v1/devices/register` - Register device
- `GET /api/sync/v1/devices` - List user's devices
- `PUT /api/sync/v1/devices/:id/status` - Update device status

**Sync Operations**:
- `GET /api/sync/v1/pull` - Pull changes
- `POST /api/sync/v1/push` - Push changes
- `GET /api/sync/v1/history` - Get sync history

**Conflict Resolution**:
- `POST /api/sync/v1/conflicts/resolve` - Resolve conflict

**Server Info**:
- `GET /api/sync/v1/ping` - Health check
- `GET /api/sync/v1/info` - Server capabilities

## Troubleshooting

### Sync Not Working

1. **Check Server Connection**:
```python
result = client.ping_server()
print(result)  # Should show {"status": "ok"}
```

2. **Check Sync Status**:
```python
status = client.get_sync_status()
print(f"Background sync enabled: {status['background_sync_enabled']}")
```

3. **Check for Errors**:
```python
def on_error(error):
    print(f"Sync error: {error}")

client.on_error(on_error)
```

### Decryption Errors

**Cause**: Wrong password or corrupted encryption key

**Solution**: Ensure all devices use the same password

```python
# If you need to reset encryption
client.encryption_key = client.encryption.create_key_from_password("new_password")
```

### Conflicts Keep Occurring

**Cause**: Multiple devices actively editing same data

**Solutions**:
1. Use `ConflictResolution.NEWEST_WINS` strategy
2. Set device priority (lower priority = wins conflicts)
3. Use selective sync to avoid conflicting edits

### High Bandwidth Usage

**Solutions**:
1. Increase sync interval:
```python
client.sync_interval = 600  # 10 minutes
```

2. Use selective sync:
```python
client.set_selective_sync([DataCategory.CONVERSATIONS])
```

3. Enable compression (enabled by default)

### Database Locked Errors

**Cause**: Multiple processes accessing sync database

**Solution**: Ensure only one SyncClient instance per database:
```python
# Use context manager to ensure cleanup
with SyncClient(...) as client:
    client.start_background_sync()
    # Your code here
# Client automatically closed
```

## Performance Tips

1. **Optimize Sync Interval**: Balance between data freshness and battery/bandwidth
2. **Use Selective Sync**: Only sync categories you need on each device
3. **Clean Old Data**: Regularly clear synced queue items
4. **Monitor Queue**: Keep queue size reasonable (<1000 items)

## Security Best Practices

1. **Strong Password**: Use long, random password for encryption
2. **Secure Storage**: Store encryption key backup securely
3. **HTTPS Only**: Always use HTTPS for sync server
4. **Regular Backups**: Backup encryption key regularly
5. **Key Rotation**: Rotate encryption keys periodically (advanced)

## Advanced Usage

### Encryption Key Backup

```python
# Create encrypted backup
backup = client.encryption.generate_key_backup(
    client.encryption_key,
    backup_password="different_strong_password"
)

# Save backup securely (e.g., encrypted file, password manager)
with open("key_backup.txt", "w") as f:
    f.write(backup)

# Restore from backup
restored_key = client.encryption.restore_key_from_backup(
    backup,
    backup_password="different_strong_password"
)
```

### Custom Storage Backend

The sync server can be configured with S3-compatible storage:

```javascript
// server.js
const storage = new S3Storage({
    endpoint: process.env.S3_ENDPOINT,
    accessKey: process.env.S3_ACCESS_KEY,
    secretKey: process.env.S3_SECRET_KEY,
    bucket: process.env.S3_BUCKET
});
```

### Monitoring and Analytics

```python
# Get sync history
history = client.protocol.get_sync_history(
    category=DataCategory.CONVERSATIONS,
    limit=50
)

for entry in history:
    print(f"{entry['timestamp']}: {entry['operation']} - {entry['item_count']} items")
```

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/Anthony5265/Windows-AI/issues
- Documentation: https://docs.windows-ai.com
- Community: https://discord.gg/windows-ai

## License

Windows-AI Cloud Sync is part of the Windows-AI project and is licensed under the MIT License.
