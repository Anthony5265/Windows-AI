# Windows AI - API Reference

Complete reference for the Windows AI HTTP API.

## Base URL

```
http://localhost:8010
```

All API endpoints are served from port 8010 by default.

## Authentication

Currently, the API does not require authentication when accessed locally.

> **Note:** Future versions will support API keys for remote access.

## Response Format

All responses follow this structure:

```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": {}  // Response-specific data
}
```

---

## Endpoints

### Health Check

Check if the backend is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "0.5.0",
  "uptime": 3600
}
```

---

### Chat

Send a message to the AI and get a response.

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "model": "llama2",  // Optional, uses default if not specified
  "temperature": 0.7,  // Optional, default 0.7
  "max_tokens": 2048,  // Optional, default 2048
  "stream": false      // Optional, default false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Chat response generated",
  "data": {
    "reply": "I'm doing well, thank you! How can I help you today?",
    "model": "llama2",
    "tokens_used": 156,
    "response_time": 2.34
  }
}
```

**Streaming Response:**

If `stream: true`, responses are sent as Server-Sent Events (SSE):

```
data: {"token": "I'm"}
data: {"token": " doing"}
data: {"token": " well"}
data: {"done": true, "tokens_used": 156}
```

**Example (Python):**
```python
import requests

response = requests.post('http://localhost:8010/chat', json={
    'message': 'List files in C:\\Downloads',
    'model': 'llama2'
})

data = response.json()
print(data['data']['reply'])
```

**Example (PowerShell):**
```powershell
$body = @{
    message = "What is my CPU usage?"
    model = "llama2"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8010/chat" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

Write-Host $response.data.reply
```

---

### Models

#### List Models

Get all available AI models.

**Endpoint:** `GET /models`

**Response:**
```json
{
  "status": "success",
  "data": {
    "models": [
      {
        "name": "llama2",
        "size": "4.1 GB",
        "downloaded": true,
        "default": true
      },
      {
        "name": "codellama",
        "size": "4.1 GB",
        "downloaded": true,
        "default": false
      }
    ]
  }
}
```

#### Download Model

Download a new AI model.

**Endpoint:** `POST /models/download`

**Request Body:**
```json
{
  "model": "mistral"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Download started",
  "data": {
    "model": "mistral",
    "size": "4.1 GB",
    "download_id": "abc123"
  }
}
```

#### Get Download Progress

Check download progress.

**Endpoint:** `GET /models/download/<download_id>`

**Response:**
```json
{
  "status": "success",
  "data": {
    "download_id": "abc123",
    "model": "mistral",
    "progress": 75.5,
    "downloaded": "3.1 GB",
    "total": "4.1 GB",
    "status": "downloading"
  }
}
```

#### Delete Model

Remove a downloaded model.

**Endpoint:** `DELETE /models/<model_name>`

**Response:**
```json
{
  "status": "success",
  "message": "Model deleted",
  "data": {
    "model": "mistral",
    "freed_space": "4.1 GB"
  }
}
```

---

### File Operations

#### List Directory

List files in a directory.

**Endpoint:** `GET /files/list`

**Query Parameters:**
- `path` (required): Directory path
- `recursive` (optional): Include subdirectories (default: false)

**Example:** `GET /files/list?path=C:\Downloads&recursive=true`

**Response:**
```json
{
  "status": "success",
  "data": {
    "path": "C:\\Downloads",
    "files": [
      {
        "name": "document.pdf",
        "size": 1048576,
        "type": "file",
        "modified": "2025-01-10T10:30:00Z"
      },
      {
        "name": "images",
        "type": "directory",
        "size": 10485760,
        "modified": "2025-01-09T14:20:00Z"
      }
    ]
  }
}
```

#### Read File

Read file contents.

**Endpoint:** `GET /files/read`

**Query Parameters:**
- `path` (required): File path

**Response:**
```json
{
  "status": "success",
  "data": {
    "path": "C:\\Documents\\file.txt",
    "content": "File contents here...",
    "size": 1024
  }
}
```

#### Write File

Write content to a file.

**Endpoint:** `POST /files/write`

**Request Body:**
```json
{
  "path": "C:\\Documents\\file.txt",
  "content": "New file contents"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "File written successfully",
  "data": {
    "path": "C:\\Documents\\file.txt",
    "size": 1024
  }
}
```

#### Delete File

Delete a file or directory.

**Endpoint:** `DELETE /files/delete`

**Request Body:**
```json
{
  "path": "C:\\Temp\\file.txt"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "File deleted",
  "data": {
    "path": "C:\\Temp\\file.txt"
  }
}
```

---

### Automation

#### List Watchers

Get all folder watchers.

**Endpoint:** `GET /automation/watchers`

**Response:**
```json
{
  "status": "success",
  "data": {
    "watchers": [
      {
        "id": "watcher_1",
        "name": "Downloads Organizer",
        "folder": "C:\\Users\\Me\\Downloads",
        "enabled": true,
        "last_run": "2025-01-10T10:30:00Z"
      }
    ]
  }
}
```

#### Create Watcher

Create a new folder watcher.

**Endpoint:** `POST /automation/watchers`

**Request Body:**
```json
{
  "name": "Downloads Organizer",
  "folder": "C:\\Users\\Me\\Downloads",
  "rules": [
    {
      "condition": "extension",
      "value": ".pdf",
      "action": "move",
      "destination": "C:\\Documents\\PDFs"
    }
  ],
  "enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Watcher created",
  "data": {
    "id": "watcher_2",
    "name": "Downloads Organizer"
  }
}
```

#### Delete Watcher

Remove a folder watcher.

**Endpoint:** `DELETE /automation/watchers/<watcher_id>`

**Response:**
```json
{
  "status": "success",
  "message": "Watcher deleted"
}
```

#### List Tasks

Get all scheduled tasks.

**Endpoint:** `GET /automation/tasks`

**Response:**
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "id": "task_1",
        "name": "Weekly Cleanup",
        "schedule": "0 3 * * 1",
        "enabled": true,
        "next_run": "2025-01-13T03:00:00Z"
      }
    ]
  }
}
```

---

### Plugins

#### List Plugins

Get all installed plugins.

**Endpoint:** `GET /plugins`

**Response:**
```json
{
  "status": "success",
  "data": {
    "plugins": [
      {
        "name": "file_manager",
        "display_name": "File Manager",
        "version": "1.2.0",
        "enabled": true,
        "capabilities": ["chat_command"]
      }
    ]
  }
}
```

#### Enable Plugin

Enable a plugin.

**Endpoint:** `POST /plugins/<plugin_name>/enable`

**Response:**
```json
{
  "status": "success",
  "message": "Plugin enabled"
}
```

#### Disable Plugin

Disable a plugin.

**Endpoint:** `POST /plugins/<plugin_name>/disable`

**Response:**
```json
{
  "status": "success",
  "message": "Plugin disabled"
}
```

#### Execute Plugin

Execute a plugin command.

**Endpoint:** `POST /plugins/<plugin_name>/execute`

**Request Body:**
```json
{
  "command": "backup",
  "args": {
    "source": "C:\\Documents",
    "destination": "D:\\Backups"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Backup completed",
  "data": {
    "files_backed_up": 234,
    "backup_path": "D:\\Backups\\backup_20250110"
  }
}
```

---

### System

#### System Info

Get system information.

**Endpoint:** `GET /system/info`

**Response:**
```json
{
  "status": "success",
  "data": {
    "os": "Windows 11",
    "version": "23H2",
    "cpu": {
      "model": "Intel Core i7-9700K",
      "cores": 8,
      "usage": 25.5
    },
    "memory": {
      "total": 17179869184,
      "used": 8589934592,
      "percent": 50.0
    },
    "disk": {
      "total": 1099511627776,
      "used": 549755813888,
      "percent": 50.0
    }
  }
}
```

#### System Stats

Get current system statistics.

**Endpoint:** `GET /system/stats`

**Response:**
```json
{
  "status": "success",
  "data": {
    "cpu_percent": 25.5,
    "ram_percent": 50.0,
    "disk_percent": 50.0,
    "network": {
      "sent": 1048576,
      "received": 2097152
    }
  }
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Backend offline |

**Error Response:**
```json
{
  "status": "error",
  "message": "File not found",
  "error_code": "FILE_NOT_FOUND",
  "details": "C:\\path\\to\\file.txt does not exist"
}
```

---

## Rate Limiting

Currently, there is no rate limiting for local API access.

Future versions may implement:
- 100 requests per minute for /chat
- 1000 requests per minute for other endpoints

---

## Examples

### Complete Chat Application (Python)

```python
import requests
import json

class WindowsAI:
    def __init__(self, base_url="http://localhost:8010"):
        self.base_url = base_url

    def chat(self, message, model="llama2"):
        response = requests.post(
            f"{self.base_url}/chat",
            json={"message": message, "model": model}
        )
        return response.json()["data"]["reply"]

    def list_files(self, path):
        response = requests.get(
            f"{self.base_url}/files/list",
            params={"path": path}
        )
        return response.json()["data"]["files"]

# Usage
ai = WindowsAI()

# Chat
reply = ai.chat("What files are in C:\\Downloads?")
print(reply)

# List files
files = ai.list_files("C:\\Downloads")
for file in files:
    print(f"{file['name']} - {file['size']} bytes")
```

### PowerShell Integration

```powershell
# Function to chat with AI
function Invoke-AIChat {
    param([string]$Message)

    $body = @{ message = $Message } | ConvertTo-Json

    $response = Invoke-RestMethod `
        -Uri "http://localhost:8010/chat" `
        -Method POST `
        -Body $body `
        -ContentType "application/json"

    return $response.data.reply
}

# Usage
Invoke-AIChat "Help me organize my Downloads folder"
```

---

## Interactive API Documentation

For interactive API documentation, visit:

**Swagger UI:** http://localhost:8010/docs
**ReDoc:** http://localhost:8010/redoc

These provide:
- Interactive request testing
- Complete schema documentation
- Code generation examples

---

## SDK/Libraries

### Official Libraries

Currently, there are no official SDK libraries. Use HTTP requests directly.

### Community Libraries

Check GitHub for community-contributed libraries:
- Python: `windows-ai-python`
- JavaScript: `windows-ai-js`
- PowerShell: `WindowsAI` module

---

## Webhook Support

Not currently supported. Future feature.

---

## WebSocket Support

Not currently supported. Use HTTP endpoints with polling or streaming.

For streaming chat responses, use the `stream: true` parameter with Server-Sent Events (SSE).

---

*Last updated: 2025-01-10 | Windows AI v0.5.0*

*For interactive documentation, see http://localhost:8010/docs*
