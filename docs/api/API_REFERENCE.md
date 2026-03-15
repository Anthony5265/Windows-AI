# Windows AI API Reference

> Complete REST API reference for Windows AI v2.0.0

**Base URL:** `http://127.0.0.1:8010`

**Documentation:** Interactive API docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Table of Contents

- [Health & Status](#health--status)
- [Chat](#chat)
- [Plugins](#plugins)
- [Plugin Management (v1)](#plugin-management-v1)
- [Agents](#agents)
- [Credentials](#credentials)
- [Setup](#setup)
- [Marketplace](#marketplace)
- [Models](#models)
- [Conversations](#conversations)
- [System](#system)

---

## Health & Status

### `GET /health`
Quick health check.

**Response:**
```json
{
  "status": "healthy",
  "message": "Windows AI backend is running",
  "version": "2.0.0",
  "timestamp": 1710000000.0
}
```

### `GET /api/health/`
Detailed health status with all component checks.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-01T00:00:00",
  "checks": {
    "database": {"status": "healthy", "message": "..."},
    "disk_space": {"status": "healthy", "message": "..."},
    "memory": {"status": "healthy", "message": "..."},
    "api_connectivity": {"status": "healthy", "message": "..."},
    "plugins": {"status": "healthy", "message": "..."}
  }
}
```

### `GET /api/health/integrations`
Check health of all 46+ integration managers.

**Response:**
```json
{
  "status": "healthy",
  "total": 46,
  "healthy": 46,
  "unhealthy": 0,
  "managers": {
    "AIProvidersManager": {"status": "healthy", "initialized": true},
    "DatabaseManager": {"status": "healthy", "initialized": true}
  }
}
```

### `GET /api/health/memory`
Check memory usage.

### `GET /api/health/disk`
Check disk space.

### `GET /api/health/network`
Check network connectivity.

### `GET /api/health/plugins`
Check plugin system health.

### `GET /api/health/database`
Check database health.

### `GET /api/health/logs/recent`
Get recent log entries.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | string | null | Filter by log level |
| `limit` | int | 100 | Max entries to return |

### `GET /api/health/errors/summary`
Get error summary with counts by level and category.

---

## Chat

### `POST /chat`
Send a chat message and get AI response.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "provider": "openai",
  "model": "gpt-4",
  "conversation_id": "optional-id",
  "system_prompt": "You are a helpful assistant."
}
```

**Response:**
```json
{
  "response": "I'm doing well! How can I help you?",
  "provider": "openai",
  "model": "gpt-4",
  "conversation_id": "abc123",
  "tokens_used": 50
}
```

### `POST /chat/stream`
Stream chat response using Server-Sent Events.

Same request body as `/chat`. Response is an SSE stream.

---

## Plugins

### `GET /plugins`
List all available plugins.

**Response:**
```json
{
  "plugins": [
    {
      "id": "web-search",
      "name": "Web Search",
      "description": "Search the web",
      "version": "2.0.0",
      "enabled": true,
      "type": "TOOL"
    }
  ],
  "total": 2155
}
```

### `GET /plugins/{plugin_id}`
Get details of a specific plugin.

### `POST /plugins/{plugin_id}/enable`
Enable a plugin.

### `POST /plugins/{plugin_id}/disable`
Disable a plugin.

---

## Plugin Management (v1)

### `GET /api/v1/plugins/`
List all plugins with full details.

### `GET /api/v1/plugins/{plugin_id}`
Get plugin by ID.

### `POST /api/v1/plugins/{plugin_id}/execute`
Execute a plugin action.

**Request Body:**
```json
{
  "action": "status",
  "parameters": {}
}
```

**Response:**
```json
{
  "status": "success",
  "result": { ... }
}
```

### `POST /api/v1/plugins/{plugin_id}/connect`
Connect an integration plugin with credentials.

**Request Body:**
```json
{
  "api_key": "your-api-key",
  "endpoint": "https://api.example.com"
}
```

### `POST /api/v1/plugins/{plugin_id}/disconnect`
Disconnect an integration plugin.

---

## Agents

### `GET /api/v1/agents/`
List all agents.

**Response:**
```json
{
  "agents": [
    {
      "id": "agent-123",
      "name": "researcher",
      "capabilities": ["general", "search"],
      "status": "idle"
    }
  ]
}
```

### `POST /api/v1/agents/`
Create a new agent.

**Request Body:**
```json
{
  "name": "researcher",
  "capabilities": ["general", "search"],
  "auth_token": "your-16-char-token"
}
```

### `GET /api/v1/agents/{agent_id}`
Get agent details.

### `POST /api/v1/agents/{agent_id}/execute`
Execute a task on an agent.

**Request Body:**
```json
{
  "task": "Research the latest AI trends",
  "parameters": {}
}
```

### `DELETE /api/v1/agents/{agent_id}`
Delete an agent.

---

## Credentials

### `GET /api/credentials/status`
Check which AI providers have credentials configured.

**Response:**
```json
{
  "providers": {
    "openai": {"configured": true, "valid": true},
    "anthropic": {"configured": false, "valid": false}
  }
}
```

### `POST /api/credentials`
Store a credential.

**Request Body:**
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "endpoint": "https://api.openai.com"
}
```

### `GET /api/credentials/test`
Test all stored credentials.

### `DELETE /api/credentials/{provider}`
Delete credentials for a provider.

### `POST /api/credentials/azure/endpoint`
Set Azure OpenAI endpoint.

---

## Setup

### `GET /api/setup/status`
Get first-run setup status.

### `POST /api/setup/start`
Start first-run setup wizard.

### `GET /api/setup/system-requirements`
Check system requirements.

### `GET /api/setup/recommended-services`
Get recommended AI services to configure.

### `GET /api/setup/api-keys`
List configured API keys.

### `POST /api/setup/api-key`
Add an API key during setup.

**Request Body:**
```json
{
  "service": "openai",
  "api_key": "sk-..."
}
```

### `DELETE /api/setup/api-key/{service}`
Remove an API key.

### `POST /api/setup/reset`
Reset setup status.

---

## Marketplace

### `GET /api/marketplace/`
Browse the plugin marketplace.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | null | Filter by category |
| `search` | string | null | Search query |
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Results per page (max 200) |

### `GET /api/marketplace/categories`
List all plugin categories with counts.

### `GET /api/marketplace/stats`
Get marketplace statistics.

### `GET /api/marketplace/search/{query}`
Search plugins by keyword.

### `GET /api/marketplace/{plugin_id}`
Get details for a specific marketplace plugin.

### `POST /api/marketplace/install`
Install a plugin.

**Request Body:**
```json
{
  "plugin_id": "windows/clipboard_sync_plugin",
  "version": "2.0.0"
}
```

### `POST /api/marketplace/uninstall/{plugin_id}`
Uninstall a marketplace plugin.

---

## Models

### `GET /models`
List available AI models.

### `GET /models/{model_id}`
Get model details.

### `POST /models/{model_id}/download`
Download a model for local use.

### `DELETE /models/{model_id}`
Delete a local model.

---

## Conversations

### `GET /conversations`
List all conversations.

### `GET /conversations/{conversation_id}`
Get a specific conversation.

### `DELETE /conversations/{conversation_id}`
Delete a conversation.

### `DELETE /conversations`
Delete all conversations.

---

## System

### `GET /api/v1/system/health`
System health check.

### `GET /api/v1/system/info`
System information (OS, Python version, etc.).

### `GET /api/v1/system/stats`
System statistics (memory, CPU, plugin count, etc.).

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error description"
}
```

**HTTP Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

---

## Authentication

Most endpoints are open by default (Freedom First philosophy). To enable authentication:

1. Configure API keys in settings
2. Include `Authorization: Bearer <token>` header
3. See [Authentication Guide](AUTHENTICATION.md) for details

---

*Generated from Windows AI v2.0.0 | 65 endpoints across 11 categories*
