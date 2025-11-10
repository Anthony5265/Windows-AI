# Actions API - Complete Reference

**Version:** 1.0.0
**Security Level:** Production-Ready with Comprehensive Hardening
**Base URL:** `http://127.0.0.1:3000`

---

## Table of Contents

1. [Overview](#overview)
2. [Security Model](#security-model)
3. [Authentication](#authentication)
4. [Rate Limiting](#rate-limiting)
5. [API Endpoints](#api-endpoints)
6. [Error Handling](#error-handling)
7. [Code Examples](#code-examples)

---

## Overview

The Actions API provides secure, monitored access to system operations for the Windows-AI assistant. It implements comprehensive security controls including:

- **JWT Authentication** - Token-based authentication for all endpoints
- **Permission-Based Authorization** - Granular permission system
- **Rate Limiting** - 100 requests/minute per client
- **Command Whitelisting** - Only approved commands can be executed
- **Input Validation** - SQL injection, command injection, path traversal prevention
- **Audit Logging** - All operations logged to `logs/security.log`
- **Resource Limits** - Timeouts, buffer limits, process isolation

---

## Security Model

### Permission System

All operations require specific permissions granted via JWT token:

| Permission | Description |
|------------|-------------|
| `file:read` | Read file contents |
| `file:write` | Write/modify files |
| `file:delete` | Delete files and directories |
| `file:execute` | Execute commands |
| `process:list` | List running processes |
| `process:start` | Start new processes |
| `process:kill` | Terminate processes |
| `process:modify` | Modify process priority |
| `system:info` | View system information |
| `system:shutdown` | Shutdown/restart system |
| `system:modify` | Modify system settings |
| `registry:read` | Read Windows registry |
| `registry:write` | Write Windows registry |
| `registry:delete` | Delete registry keys |
| `network:access` | Network operations |
| `admin:*` | Full administrative access |

### Command Whitelist

Only these commands can be executed:

**File Operations:** `ls`, `dir`, `cat`, `type`, `head`, `tail`, `find`, `where`
**System Info:** `echo`, `pwd`, `cd`, `hostname`, `whoami`, `date`, `time`, `systeminfo`, `wmic`, `tasklist`, `ps`
**Network:** `ping`, `ipconfig`, `ifconfig`, `netstat`, `nslookup`
**Process:** `taskkill`, `kill`
**Scripting:** `powershell`, `pwsh`, `python`, `python3`, `node`

### Dangerous Patterns (Blocked)

- Recursive delete: `rm -rf`, `del /s`
- Disk formatting: `format`, `mkfs`
- System shutdown: `shutdown`, `reboot`
- Disk duplication: `dd if=`

---

## Authentication

### Generate Token

```http
POST /auth/token
Content-Type: application/json

{
  "serviceId": "backend-service",
  "permissions": ["file:read", "file:write", "system:info"]
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Use Token

Include token in Authorization header:

```http
GET /api/system/info
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Rate Limiting

- **Global Limit:** 100 requests/minute per client
- **Key:** Client IP or JWT subject (user ID)
- **Headers:** Rate limit info returned in response headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 2025-01-10T12:05:00.000Z
```

---

## API Endpoints

### Health & Status

#### GET /health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "ok": true,
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00.000Z",
  "version": "1.0.0"
}
```

#### GET /status

Detailed API status with system information (authentication required).

**Permissions:** Any authenticated user

**Response:**
```json
{
  "ok": true,
  "result": {
    "api": {
      "version": "1.0.0",
      "uptime": 3600.5
    },
    "system": {
      "platform": "win32",
      "arch": "x64",
      "hostname": "DESKTOP-PC",
      "uptime": 86400,
      "cpu": {
        "model": "Intel(R) Core(TM) i7-9700K",
        "cores": 8,
        "speed": 3600,
        "usage": 45.2
      },
      "memory": {
        "total": 17179869184,
        "free": 8589934592,
        "used": 8589934592,
        "usagePercent": 50.0
      }
    }
  }
}
```

---

### File Operations

#### POST /api/files/read

Read file contents.

**Permissions:** `file:read`

**Request:**
```json
{
  "path": "/path/to/file.txt",
  "encoding": "utf8"  // Optional: utf8, ascii, base64
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "content": "File contents here..."
  }
}
```

**Limits:**
- Maximum file size: 100MB
- Path traversal attempts are blocked

---

#### POST /api/files/write

Write file contents.

**Permissions:** `file:write`

**Request:**
```json
{
  "path": "/path/to/file.txt",
  "content": "New file contents",
  "encoding": "utf8",  // Optional
  "atomic": true  // Optional: atomic write (write to temp, then rename)
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "ok": true,
    "path": "/absolute/path/to/file.txt"
  }
}
```

---

#### POST /api/files/copy

Copy file or directory.

**Permissions:** `file:write`

**Request:**
```json
{
  "source": "/path/to/source.txt",
  "destination": "/path/to/destination.txt",
  "overwrite": false,  // Optional: default false
  "preserveTimestamps": true  // Optional: default false
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "ok": true,
    "destination": "/absolute/path/to/destination.txt"
  }
}
```

---

#### POST /api/files/move

Move/rename file.

**Permissions:** `file:write`

**Request:**
```json
{
  "source": "/path/to/source.txt",
  "destination": "/path/to/destination.txt",
  "overwrite": false  // Optional
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "ok": true,
    "destination": "/absolute/path/to/destination.txt"
  }
}
```

---

#### POST /api/files/delete

Delete file or directory.

**Permissions:** `file:delete`

**Request:**
```json
{
  "path": "/path/to/file-or-directory",
  "recursive": false,  // Required for directories
  "force": false  // Optional
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "ok": true,
    "path": "/absolute/path/to/file"
  }
}
```

---

#### POST /api/files/list

List directory contents.

**Permissions:** `file:read`

**Request:**
```json
{
  "path": "/path/to/directory",
  "recursive": false,  // Optional: recursively list subdirectories
  "includeHidden": false  // Optional: include hidden files
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "files": [
      {
        "path": "/absolute/path/to/file.txt",
        "name": "file.txt",
        "size": 1024,
        "isDirectory": false,
        "isFile": true,
        "isSymlink": false,
        "createdAt": "2025-01-01T00:00:00.000Z",
        "modifiedAt": "2025-01-10T12:00:00.000Z",
        "accessedAt": "2025-01-10T12:00:00.000Z",
        "permissions": "644"
      }
    ]
  }
}
```

---

### Command Execution

#### POST /api/commands/execute

Execute a whitelisted command with arguments.

**Permissions:** `file:execute`

**Request:**
```json
{
  "command": "ls",
  "args": ["-la", "/home/user"],
  "options": {
    "cwd": "/home/user",  // Optional: working directory
    "timeout": 30000,  // Optional: timeout in ms (max: 300000)
    "maxBuffer": 1048576,  // Optional: max stdout buffer (max: 10MB)
    "env": {  // Optional: environment variables
      "MY_VAR": "value"
    }
  }
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "stdout": "total 48\ndrwxr-xr-x 12 user user 4096 Jan 10 12:00 .\n...",
    "stderr": "",
    "exitCode": 0,
    "duration": 150,
    "pid": 12345
  }
}
```

**Security Features:**
- Command must be in whitelist
- No shell metacharacters allowed
- Path traversal prevention
- Timeout enforcement
- Buffer overflow protection
- Process tree cleanup

---

#### POST /api/commands/shell

Execute shell command (admin only).

**Permissions:** `admin:*`

**Request:**
```json
{
  "command": "echo 'Hello World'",
  "options": {
    "timeout": 30000
  }
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "stdout": "Hello World",
    "stderr": "",
    "exitCode": 0,
    "duration": 50
  }
}
```

⚠️ **Warning:** This endpoint bypasses some security restrictions. Use with caution.

---

### System Information

#### GET /api/system/info

Get comprehensive system information.

**Permissions:** `system:info`

**Response:**
```json
{
  "ok": true,
  "result": {
    "platform": "win32",
    "arch": "x64",
    "release": "10.0.22000",
    "hostname": "DESKTOP-PC",
    "uptime": 86400,
    "cpu": {
      "model": "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz",
      "cores": 8,
      "speed": 3600,
      "usage": 45.2
    },
    "memory": {
      "total": 17179869184,
      "free": 8589934592,
      "used": 8589934592,
      "usagePercent": 50.0
    },
    "disk": [
      {
        "total": 1000000000000,
        "free": 500000000000,
        "used": 500000000000,
        "usagePercent": 50.0
      }
    ],
    "network": [
      {
        "interface": "Ethernet",
        "address": "192.168.1.100",
        "netmask": "255.255.255.0",
        "mac": "00:11:22:33:44:55",
        "internal": false
      }
    ]
  }
}
```

---

#### POST /api/system/notification

Display system notification.

**Permissions:** `system:modify`

**Request:**
```json
{
  "title": "Windows AI",
  "message": "Task completed successfully!",
  "icon": "info",  // Optional: info, warning, error
  "sound": true,  // Optional: play sound
  "priority": "normal"  // Optional: low, normal, high, critical
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "ok": true
  }
}
```

---

### Process Management

#### GET /api/processes/list

List all running processes.

**Permissions:** `process:list`

**Response:**
```json
{
  "ok": true,
  "result": {
    "processes": [
      {
        "pid": 1234,
        "name": "chrome.exe",
        "cpu": 15.5,
        "memory": 524288000,
        "command": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
      }
    ]
  }
}
```

---

#### POST /api/processes/start

Start a new process.

**Permissions:** `process:start`

**Request:**
```json
{
  "executable": "notepad.exe",
  "args": ["C:\\file.txt"],
  "options": {
    "cwd": "C:\\Users\\User",
    "detached": false
  }
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "pid": 5678,
    "ok": true
  }
}
```

---

#### POST /api/processes/kill

Terminate a process.

**Permissions:** `process:kill`

**Request:**
```json
{
  "pid": 1234,  // Either pid or name required
  "name": "chrome.exe",  // Either pid or name required
  "signal": "SIGTERM",  // Optional: default SIGTERM
  "force": false  // Optional: force kill
}
```

**Response:**
```json
{
  "ok": true,
  "result": {
    "ok": true
  }
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "ok": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Command contains disallowed characters",
    "details": {
      "command": "ls; rm -rf /",
      "dangerous": ";"
    },
    "suggestions": [
      "Check the request parameters",
      "Ensure all required fields are provided",
      "Verify data types match the expected format"
    ]
  },
  "timestamp": "2025-01-10T12:00:00.000Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input parameters |
| `INVALID_INPUT` | 400 | Malformed request data |
| `MISSING_REQUIRED_FIELD` | 400 | Required field not provided |
| `UNAUTHORIZED` | 401 | Authentication required |
| `INVALID_TOKEN` | 401 | JWT token invalid |
| `TOKEN_EXPIRED` | 401 | JWT token expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `COMMAND_EXECUTION_FAILED` | 500 | Command execution failed |
| `FILE_OPERATION_FAILED` | 500 | File operation failed |
| `PROCESS_OPERATION_FAILED` | 500 | Process operation failed |
| `NETWORK_ERROR` | 500 | Network operation failed |
| `TIMEOUT` | 500 | Operation timed out |

---

## Code Examples

### Node.js/TypeScript

```typescript
import axios from 'axios';

const API_URL = 'http://127.0.0.1:3000';
const TOKEN = 'your-jwt-token-here';

// Read a file
async function readFile(path: string) {
  const response = await axios.post(
    `${API_URL}/api/files/read`,
    { path },
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      }
    }
  );

  return response.data.result.content;
}

// Execute a command
async function executeCommand(command: string, args: string[]) {
  const response = await axios.post(
    `${API_URL}/api/commands/execute`,
    { command, args },
    {
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      }
    }
  );

  return response.data.result;
}

// Usage
const content = await readFile('/path/to/file.txt');
const result = await executeCommand('ls', ['-la', '/home/user']);
```

### Python

```python
import requests

API_URL = 'http://127.0.0.1:3000'
TOKEN = 'your-jwt-token-here'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Read a file
def read_file(path):
    response = requests.post(
        f'{API_URL}/api/files/read',
        json={'path': path},
        headers=headers
    )
    return response.json()['result']['content']

# Execute a command
def execute_command(command, args):
    response = requests.post(
        f'{API_URL}/api/commands/execute',
        json={'command': command, 'args': args},
        headers=headers
    )
    return response.json()['result']

# Usage
content = read_file('/path/to/file.txt')
result = execute_command('ls', ['-la', '/home/user'])
```

---

## Audit Logging

All operations are logged to `logs/security.log` in JSON format:

```json
{
  "timestamp": "2025-01-10T12:00:00.000Z",
  "level": "info",
  "action": "POST /api/files/read",
  "userId": "backend-service",
  "clientIp": "127.0.0.1",
  "request": {
    "method": "POST",
    "path": "/api/files/read",
    "body": {
      "path": "/home/user/file.txt"
    }
  },
  "response": {
    "status": 200,
    "duration": 15
  },
  "metadata": {
    "userAgent": "axios/1.0.0"
  }
}
```

### Log Levels

- **`info`**: Successful operations
- **`warn`**: Failed operations (4xx errors)
- **`error`**: Server errors (5xx errors)
- **`security`**: Authentication/authorization events

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (never in code or version control)
3. **Use minimum required permissions** (principle of least privilege)
4. **Implement proper error handling** in client applications
5. **Monitor audit logs** for security events
6. **Rotate JWT secrets regularly**
7. **Use atomic file operations** for critical writes
8. **Validate all user inputs** before sending to API
9. **Implement exponential backoff** for retries
10. **Test in non-production environment** before deploying

---

## Support & Troubleshooting

### Common Issues

**401 Unauthorized**
- Check if token is included in Authorization header
- Verify token hasn't expired
- Generate a new token if needed

**403 Forbidden**
- Check if user has required permissions
- Verify permission grants in JWT payload

**429 Rate Limit Exceeded**
- Wait for rate limit reset (check X-RateLimit-Reset header)
- Implement exponential backoff

**500 Command Execution Failed**
- Check if command is in whitelist
- Verify command syntax and arguments
- Review audit logs for detailed error information

### Logs

- **Security log:** `logs/security.log`
- **Application log:** Console output (stdout)

---

**Last Updated:** 2025-01-10
**API Version:** 1.0.0
**Documentation Version:** 1.0.0
