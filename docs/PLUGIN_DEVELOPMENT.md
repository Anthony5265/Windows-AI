# Windows AI - Plugin Development Guide

Learn how to create custom plugins to extend Windows AI functionality.

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Plugin Architecture](#plugin-architecture)
4. [Plugin API Reference](#plugin-api-reference)
5. [Best Practices](#best-practices)
6. [Examples](#examples)
7. [Testing](#testing)
8. [Distribution](#distribution)

---

## Introduction

Plugins allow you to extend Windows AI with custom functionality. A plugin can:

- Add new commands to the chat interface
- Integrate with external services (GitHub, Trello, etc.)
- Provide system utilities (backups, monitoring, etc.)
- Automate complex workflows
- Add UI components to the GUI

### What You'll Need

- Python 3.11+ knowledge
- Windows AI installed
- Text editor or IDE
- Basic understanding of async/await

### Plugin Types

| Type | Description | Example |
|------|-------------|---------|
| **Command** | Responds to chat commands | File operations, web search |
| **Service** | Runs in background | System monitoring, auto-backup |
| **Integration** | Connects to external API | GitHub, Slack, Notion |
| **Utility** | Provides helper functions | Password generator, QR codes |
| **UI Extension** | Adds GUI components | Custom dashboards, visualizations |

---

## Quick Start

### Your First Plugin

Let's create a simple "Hello World" plugin.

**Step 1: Create Plugin File**

Create `windows_ai/plugins/custom/hello_plugin.py`:

```python
"""
Hello World Plugin
A simple example plugin for Windows AI
"""

from windows_ai.core.plugin_base import PluginBase
from typing import Dict, Any


class HelloPlugin(PluginBase):
    """Simple hello world plugin"""

    # Plugin metadata
    name = "hello_plugin"
    display_name = "Hello World"
    description = "Says hello to the user"
    version = "1.0.0"
    author = "Your Name"

    # Plugin capabilities
    capabilities = ["chat_command"]

    # Chat commands this plugin responds to
    commands = ["hello", "hi", "greet"]

    async def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main plugin execution method

        Args:
            command: The command that triggered this plugin
            args: Arguments passed to the plugin

        Returns:
            Dict with status and data
        """
        user_name = args.get("user_name", "friend")

        return {
            "status": "success",
            "message": f"Hello, {user_name}! 👋",
            "data": {
                "greeting": f"Hello, {user_name}!",
                "timestamp": self.get_timestamp()
            }
        }

    def get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
```

**Step 2: Register Plugin**

Add to `windows_ai/plugins/custom/__init__.py`:

```python
from .hello_plugin import HelloPlugin

__all__ = ['HelloPlugin']
```

**Step 3: Test Plugin**

Restart Windows AI and try in chat:

```
You: "hello"
AI: "Hello, friend! 👋"

You: "hello user_name=John"
AI: "Hello, John! 👋"
```

Congratulations! You've created your first plugin! 🎉

---

## Plugin Architecture

### Plugin Lifecycle

```
1. Discovery   → Windows AI scans plugins/ directory
2. Loading     → Plugin class imported
3. Registration → Plugin registered with core
4. Initialization → __init__() called
5. Ready       → Plugin ready to execute
6. Execution   → execute() called when triggered
7. Cleanup     → cleanup() called on shutdown
```

### Plugin Base Class

All plugins inherit from `PluginBase`:

```python
from windows_ai.core.plugin_base import PluginBase

class MyPlugin(PluginBase):
    # Required attributes
    name = "my_plugin"              # Unique identifier
    display_name = "My Plugin"       # Human-readable name
    description = "What it does"     # Short description
    version = "1.0.0"               # Semantic version

    # Optional attributes
    author = "Your Name"
    website = "https://example.com"
    license = "MIT"
    capabilities = ["chat_command", "background_service"]
    commands = ["mycommand"]
    dependencies = ["requests>=2.28.0"]

    async def execute(self, command: str, args: dict) -> dict:
        """Main execution method"""
        pass

    async def initialize(self) -> None:
        """Called once when plugin loads"""
        pass

    async def cleanup(self) -> None:
        """Called when plugin unloads"""
        pass
```

### Directory Structure

```
windows_ai/
└── plugins/
    ├── builtin/              # Pre-installed plugins
    │   ├── file_manager_plugin.py
    │   ├── system_monitor_plugin.py
    │   └── ...
    ├── custom/               # Your custom plugins go here
    │   ├── __init__.py
    │   ├── hello_plugin.py
    │   └── my_plugin.py
    └── base.py              # Plugin base class
```

---

## Plugin API Reference

### Core Methods

#### `execute(command: str, args: Dict[str, Any]) -> Dict[str, Any]`

Main entry point for plugin execution.

**Parameters:**
- `command` (str): The command that triggered the plugin
- `args` (dict): Arguments passed by the user or system

**Returns:**
- Dictionary with `status`, `message`, and optionally `data`

**Example:**
```python
async def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if command == "backup":
        source = args.get("source")
        dest = args.get("destination")

        # Perform backup
        result = await self.backup_files(source, dest)

        return {
            "status": "success",
            "message": f"Backed up {result['file_count']} files",
            "data": result
        }
```

#### `initialize() -> None`

Called once when plugin loads. Use for setup:
- Load configuration
- Initialize connections
- Set up resources

**Example:**
```python
async def initialize(self) -> None:
    """Initialize plugin"""
    self.config = await self.load_config()
    self.api_client = MyAPIClient(self.config["api_key"])
    self.logger.info(f"{self.name} initialized")
```

#### `cleanup() -> None`

Called when plugin unloads. Use for teardown:
- Close connections
- Save state
- Release resources

**Example:**
```python
async def cleanup(self) -> None:
    """Cleanup plugin resources"""
    await self.api_client.close()
    await self.save_state()
    self.logger.info(f"{self.name} cleaned up")
```

### Helper Properties

Plugins have access to these built-in helpers:

```python
class MyPlugin(PluginBase):
    async def execute(self, command: str, args: dict) -> dict:
        # Logging
        self.logger.info("Plugin executed")
        self.logger.error("Something went wrong")

        # Configuration
        config = self.config  # Plugin-specific config
        app_config = self.app_config  # Global app config

        # File paths
        plugin_dir = self.plugin_dir  # Plugin's directory
        data_dir = self.data_dir  # %APPDATA%/WindowsAI

        # System info
        os_type = self.os_type  # "windows", "linux", "darwin"
        user_name = self.user_name  # Current Windows username
```

### Event Hooks

Plugins can listen to events:

```python
class MyPlugin(PluginBase):
    # Declare event handlers
    event_handlers = {
        "file_created": "on_file_created",
        "app_startup": "on_startup",
        "chat_message": "on_chat_message"
    }

    async def on_file_created(self, event_data: dict) -> None:
        """Called when a file is created"""
        file_path = event_data["path"]
        self.logger.info(f"File created: {file_path}")

    async def on_startup(self, event_data: dict) -> None:
        """Called when app starts"""
        self.logger.info("App started!")

    async def on_chat_message(self, event_data: dict) -> None:
        """Called on every chat message"""
        message = event_data["message"]
        # Process message...
```

### File Operations

Helper methods for common file operations:

```python
async def execute(self, command: str, args: dict) -> dict:
    # Read file
    content = await self.read_file("C:\\path\\to\\file.txt")

    # Write file
    await self.write_file("C:\\path\\to\\file.txt", "content")

    # List directory
    files = await self.list_directory("C:\\path\\to\\dir")

    # Check if file exists
    exists = await self.file_exists("C:\\path\\to\\file.txt")

    # Get file info
    info = await self.get_file_info("C:\\path\\to\\file.txt")
    # Returns: {size, created, modified, type}
```

### HTTP Requests

Make HTTP requests easily:

```python
async def execute(self, command: str, args: dict) -> dict:
    # GET request
    response = await self.http_get("https://api.example.com/data")

    # POST request
    response = await self.http_post(
        "https://api.example.com/endpoint",
        json={"key": "value"}
    )

    # With headers
    response = await self.http_get(
        "https://api.example.com/data",
        headers={"Authorization": "Bearer token"}
    )
```

### Configuration

Plugins can have configuration files:

**Create `config.yaml`:**
```yaml
# windows_ai/plugins/custom/my_plugin/config.yaml
api_key: "your_api_key_here"
enabled: true
check_interval: 300  # seconds
```

**Load in plugin:**
```python
async def initialize(self) -> None:
    # Load configuration
    self.config = await self.load_config()

    api_key = self.config.get("api_key")
    enabled = self.config.get("enabled", True)
```

### Notifications

Show notifications to user:

```python
async def execute(self, command: str, args: dict) -> dict:
    # Info notification
    await self.notify("Backup complete!", level="info")

    # Warning
    await self.notify("Disk space low", level="warning")

    # Error
    await self.notify("Backup failed", level="error")

    # Success
    await self.notify("Task completed", level="success")
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def execute(self, command: str, args: dict) -> dict:
    try:
        result = await self.perform_operation()

        return {
            "status": "success",
            "message": "Operation completed",
            "data": result
        }

    except FileNotFoundError as e:
        self.logger.error(f"File not found: {e}")
        return {
            "status": "error",
            "message": f"File not found: {e}",
            "error_code": "FILE_NOT_FOUND"
        }

    except Exception as e:
        self.logger.exception("Unexpected error")
        return {
            "status": "error",
            "message": f"Operation failed: {str(e)}",
            "error_code": "UNKNOWN_ERROR"
        }
```

### 2. Async/Await

Use async for I/O operations:

```python
# Good - async I/O
async def read_large_file(self, path: str) -> str:
    async with aiofiles.open(path, 'r') as f:
        content = await f.read()
    return content

# Bad - blocking I/O
def read_large_file(self, path: str) -> str:
    with open(path, 'r') as f:
        content = f.read()  # Blocks event loop!
    return content
```

### 3. Logging

Use logging instead of print:

```python
# Good
self.logger.info("Processing started")
self.logger.debug(f"Args: {args}")
self.logger.error("Operation failed", exc_info=True)

# Bad
print("Processing started")  # Don't use print!
```

### 4. Configuration

Don't hardcode values:

```python
# Good - use configuration
api_key = self.config.get("api_key")
timeout = self.config.get("timeout", 30)

# Bad - hardcoded
api_key = "hardcoded_key_123"  # Never do this!
timeout = 30
```

### 5. Permissions

Request only needed permissions:

```python
class MyPlugin(PluginBase):
    # Request specific permissions
    permissions = [
        "read_files",      # Read file system
        "write_files",     # Write file system
        "network_access",  # Make HTTP requests
        "system_info"      # Access system information
    ]
```

### 6. Documentation

Document your plugin well:

```python
class MyPlugin(PluginBase):
    """
    Detailed plugin description

    This plugin provides X functionality by doing Y.

    Commands:
        - mycommand <arg> : Does something
        - myother <arg>   : Does something else

    Examples:
        "mycommand file=test.txt"
        "myother mode=fast"

    Configuration:
        api_key: Your API key
        enabled: Enable/disable plugin
    """

    async def execute(self, command: str, args: dict) -> dict:
        """
        Execute plugin command

        Args:
            command: Command name (mycommand, myother)
            args: Command arguments
                - file (str): File path
                - mode (str): Operation mode

        Returns:
            Dict with status, message, and data

        Raises:
            ValueError: If arguments invalid
            FileNotFoundError: If file not found
        """
        pass
```

---

## Examples

### Example 1: File Backup Plugin

```python
"""File Backup Plugin - Backup files to destination"""

import shutil
from pathlib import Path
from datetime import datetime
from windows_ai.core.plugin_base import PluginBase


class FileBackupPlugin(PluginBase):
    name = "file_backup"
    display_name = "File Backup"
    description = "Backup files and directories"
    version = "1.0.0"
    capabilities = ["chat_command"]
    commands = ["backup"]

    async def execute(self, command: str, args: dict) -> dict:
        source = args.get("source")
        destination = args.get("destination")

        if not source or not destination:
            return {
                "status": "error",
                "message": "Usage: backup source=<path> destination=<path>"
            }

        try:
            # Create timestamped backup folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            dest_path = Path(destination) / backup_name

            # Copy files
            shutil.copytree(source, dest_path)

            # Count files
            file_count = sum(1 for _ in dest_path.rglob('*') if _.is_file())

            return {
                "status": "success",
                "message": f"Backed up {file_count} files to {dest_path}",
                "data": {
                    "file_count": file_count,
                    "backup_path": str(dest_path),
                    "timestamp": timestamp
                }
            }

        except Exception as e:
            self.logger.exception("Backup failed")
            return {
                "status": "error",
                "message": f"Backup failed: {str(e)}"
            }
```

**Usage:**
```
"backup source=C:\Documents destination=D:\Backups"
```

### Example 2: GitHub Integration Plugin

```python
"""GitHub Integration Plugin"""

import aiohttp
from windows_ai.core.plugin_base import PluginBase


class GitHubPlugin(PluginBase):
    name = "github"
    display_name = "GitHub Integration"
    description = "Interact with GitHub repositories"
    version = "1.0.0"
    capabilities = ["chat_command"]
    commands = ["gh", "github"]
    permissions = ["network_access"]

    async def initialize(self) -> None:
        """Load GitHub token from config"""
        self.token = self.config.get("github_token")
        if not self.token:
            self.logger.warning("No GitHub token configured")

    async def execute(self, command: str, args: dict) -> dict:
        action = args.get("action")

        if action == "list_repos":
            return await self.list_repositories()

        elif action == "create_issue":
            return await self.create_issue(
                repo=args.get("repo"),
                title=args.get("title"),
                body=args.get("body")
            )

        else:
            return {
                "status": "error",
                "message": "Unknown action. Use: list_repos, create_issue"
            }

    async def list_repositories(self) -> dict:
        """List user's GitHub repositories"""
        headers = {"Authorization": f"token {self.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/user/repos",
                headers=headers
            ) as response:
                if response.status == 200:
                    repos = await response.json()
                    repo_names = [r["full_name"] for r in repos]

                    return {
                        "status": "success",
                        "message": f"Found {len(repos)} repositories",
                        "data": {"repositories": repo_names}
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"GitHub API error: {response.status}"
                    }

    async def create_issue(self, repo: str, title: str, body: str) -> dict:
        """Create GitHub issue"""
        headers = {"Authorization": f"token {self.token}"}
        data = {"title": title, "body": body}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.github.com/repos/{repo}/issues",
                headers=headers,
                json=data
            ) as response:
                if response.status == 201:
                    issue = await response.json()
                    return {
                        "status": "success",
                        "message": f"Created issue #{issue['number']}",
                        "data": {"issue_url": issue["html_url"]}
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to create issue: {response.status}"
                    }
```

**Usage:**
```
"github action=list_repos"
"github action=create_issue repo=user/repo title='Bug report' body='Description'"
```

### Example 3: System Monitor Plugin (Background Service)

```python
"""System Monitor Plugin - Monitor CPU/RAM in background"""

import psutil
import asyncio
from windows_ai.core.plugin_base import PluginBase


class SystemMonitorPlugin(PluginBase):
    name = "system_monitor"
    display_name = "System Monitor"
    description = "Monitor system resources"
    version = "1.0.0"
    capabilities = ["background_service", "chat_command"]
    commands = ["sysinfo", "stats"]

    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.stats = {}

    async def initialize(self) -> None:
        """Start background monitoring"""
        self.monitoring = True
        asyncio.create_task(self.monitor_loop())

    async def cleanup(self) -> None:
        """Stop monitoring"""
        self.monitoring = False

    async def monitor_loop(self) -> None:
        """Background monitoring loop"""
        while self.monitoring:
            try:
                # Collect stats
                self.stats = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "ram_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                }

                # Alert if high usage
                if self.stats["cpu_percent"] > 90:
                    await self.notify("High CPU usage!", level="warning")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Monitor error: {e}")

    async def execute(self, command: str, args: dict) -> dict:
        """Return current stats"""
        return {
            "status": "success",
            "message": "System stats",
            "data": self.stats
        }
```

---

## Testing

### Unit Tests

Create tests in `tests/plugins/test_my_plugin.py`:

```python
import pytest
from windows_ai.plugins.custom.my_plugin import MyPlugin


@pytest.mark.asyncio
async def test_plugin_execute():
    """Test plugin execution"""
    plugin = MyPlugin()
    await plugin.initialize()

    result = await plugin.execute(
        command="mycommand",
        args={"param": "value"}
    )

    assert result["status"] == "success"
    assert "data" in result

    await plugin.cleanup()


@pytest.mark.asyncio
async def test_plugin_error_handling():
    """Test error handling"""
    plugin = MyPlugin()

    result = await plugin.execute(
        command="invalid",
        args={}
    )

    assert result["status"] == "error"
```

### Integration Tests

Test with actual Windows AI instance:

```python
@pytest.mark.integration
async def test_plugin_in_app():
    """Test plugin integrated with app"""
    # Start Windows AI
    app = await start_app()

    # Load plugin
    plugin = await app.load_plugin("my_plugin")

    # Execute command
    result = await app.execute_command("mycommand param=value")

    assert result["status"] == "success"

    await app.stop()
```

---

## Distribution

### Package Structure

```
my_plugin/
├── __init__.py
├── my_plugin.py
├── config.yaml
├── README.md
├── LICENSE
├── requirements.txt
└── tests/
    └── test_my_plugin.py
```

### Create ZIP Package

```bash
# Create plugin package
zip -r my_plugin.zip my_plugin/

# Or use Python
python -m zipfile -c my_plugin.zip my_plugin/
```

### Publish to Marketplace

1. Create GitHub repository
2. Add plugin code
3. Tag release (e.g., `v1.0.0`)
4. Submit to Windows AI marketplace
5. Users can install via: Plugins → Browse Marketplace

### Plugin Metadata

Create `plugin.json`:

```json
{
  "name": "my_plugin",
  "display_name": "My Awesome Plugin",
  "description": "Does something useful",
  "version": "1.0.0",
  "author": "Your Name",
  "website": "https://github.com/user/my-plugin",
  "license": "MIT",
  "keywords": ["utility", "automation"],
  "requirements": ["requests>=2.28.0"],
  "min_app_version": "0.5.0"
}
```

---

## Resources

- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Example Plugins**: `windows_ai/plugins/builtin/`
- **Plugin Base Class**: `windows_ai/core/plugin_base.py`
- **Community Plugins**: https://github.com/topics/windows-ai-plugin

---

*Last updated: 2025-01-10 | Windows AI v0.5.0*
