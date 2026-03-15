# Windows AI Plugin Development Guide

This guide covers how to create, test, and distribute plugins for Windows AI.

## Plugin Architecture

Windows AI uses a modular plugin system. All plugins inherit from base classes defined in `windows_ai/plugins/base.py`.

### Plugin Types

| Type | Base Class | Use Case |
|------|-----------|----------|
| `ACTION` | `ActionPlugin` | AI-powered actions (summarize, organize, etc.) |
| `TOOL` | `ToolPlugin` | Reusable tools (web search, file ops, etc.) |
| `INTEGRATION` | `IntegrationPlugin` | External service integrations (GitHub, Notion, etc.) |
| `UI` | Plugin (base) | UI extensions and custom views |
| `AUTOMATION` | `AutomationPlugin` | OS automation with triggers |

### Plugin Lifecycle

```
__init__() → initialize() → execute() ... execute() → shutdown()
                              ↑               |
                              └───────────────┘
```

## Creating a Plugin

### 1. Choose the Right Base Class

```python
from windows_ai.plugins.base import (
    Plugin,              # Base - for simple plugins
    ActionPlugin,        # For AI-powered actions
    ToolPlugin,          # For reusable tools
    IntegrationPlugin,   # For external service integrations
    AutomationPlugin,    # For OS automation
    PluginMetadata,
    PluginType,
)
```

### 2. Define Metadata

```python
metadata = PluginMetadata(
    id="my-plugin",                        # Unique identifier
    name="My Plugin",                      # Display name
    description="Does something useful",   # Short description
    version="1.0.0",                       # Semantic version
    author="Your Name",                    # Author name
    plugin_type=PluginType.TOOL,           # Plugin type
    tags=["utility", "productivity"],      # Searchable tags
    requirements=["requests"],             # Python dependencies
    capabilities=["search", "analyze"],    # What it can do
)
```

### 3. Implement the Plugin

#### Action Plugin Example

```python
from windows_ai.plugins.base import ActionPlugin, PluginMetadata, PluginType

class SummarizePlugin(ActionPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="summarize",
            name="Text Summarizer",
            description="Summarize text using AI",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.ACTION,
            tags=["text", "ai", "summary"],
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def execute(self, text: str = "", **kwargs) -> dict:
        # Your summarization logic here
        return {
            "status": "success",
            "summary": f"Summary of: {text[:100]}...",
        }

    async def shutdown(self):
        pass

    def get_schema(self) -> dict:
        return {
            "name": "summarize",
            "description": "Summarize text",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                },
                "required": ["text"],
            },
        }

# Module-level instance for plugin discovery
plugin = SummarizePlugin()
```

#### Integration Plugin Example

```python
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

class GitHubPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="github-integration",
            name="GitHub",
            description="GitHub API integration",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["github", "git", "dev"],
        )
        super().__init__(metadata)
        self.client = None

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def connect(self, credentials: dict) -> bool:
        """Connect to GitHub with API token."""
        token = credentials.get("api_key")
        if not token:
            return False
        self.client = {"token": token}
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from GitHub."""
        self.client = None
        self.connected = False
        return True

    async def execute(self, action: str, parameters: dict, **kwargs) -> dict:
        actions = {
            "list_repos": self._list_repos,
            "create_issue": self._create_issue,
            "status": self._get_status,
        }
        handler = actions.get(action)
        if not handler:
            return {"status": "error", "message": f"Unknown action: {action}"}
        return await handler(parameters)

    async def _list_repos(self, params: dict) -> dict:
        return {"status": "success", "repos": []}

    async def _create_issue(self, params: dict) -> dict:
        return {"status": "success", "issue_id": 1}

    async def _get_status(self, params: dict) -> dict:
        return {"status": "success", "connected": self.connected}

    async def shutdown(self):
        await self.disconnect()

    def get_schema(self) -> dict:
        return {
            "name": "github",
            "description": "GitHub integration",
            "actions": ["list_repos", "create_issue", "status"],
        }

plugin = GitHubPlugin()
```

#### Tool Plugin Example

```python
from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

class WebSearchPlugin(ToolPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="web-search",
            name="Web Search",
            description="Search the web",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.TOOL,
            tags=["search", "web"],
        )
        super().__init__(metadata)

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def execute(self, query: str = "", **kwargs) -> dict:
        return {"status": "success", "results": []}

    async def shutdown(self):
        pass

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
        }

plugin = WebSearchPlugin()
```

## Plugin Discovery

The plugin manager discovers plugins by scanning plugin directories for Python files.
Each plugin file must have a **module-level `plugin` attribute** that is an instance of a plugin class:

```python
# At the bottom of your plugin file:
plugin = MyPlugin()
```

## Plugin Directory Structure

Place your plugins in the appropriate category directory:

```
windows_ai/plugins/builtin/
├── windows/          # Windows-specific plugins
├── windows_os/       # Windows OS management
├── audio_models/     # Audio AI models
├── vision_models/    # Vision AI models
├── code_models/      # Code AI models
├── productivity/     # Productivity tools
├── dev/              # Developer tools
├── web/              # Web-related plugins
└── ...               # 27 categories total
```

Or install to user plugin directory: `~/.windows_ai/plugins/`

## PluginMetadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | ✅ | Unique plugin identifier |
| `name` | str | ✅ | Human-readable name |
| `description` | str | ✅ | Short description |
| `version` | str | ✅ | Semantic version (e.g., "1.0.0") |
| `author` | str | ✅ | Author name |
| `plugin_type` | PluginType | ✅ | ACTION, TOOL, INTEGRATION, UI, AUTOMATION |
| `enabled` | bool | ❌ | Default: True |
| `icon` | str | ❌ | Icon name or URL |
| `tags` | List[str] | ❌ | Searchable tags |
| `requirements` | List[str] | ❌ | Python package dependencies |
| `capabilities` | List[str] | ❌ | Plugin capabilities |

## Testing Your Plugin

```python
import pytest
from my_plugin import MyPlugin

@pytest.mark.asyncio
async def test_plugin_init():
    plugin = MyPlugin()
    result = await plugin.initialize()
    assert result is True

@pytest.mark.asyncio
async def test_plugin_execute():
    plugin = MyPlugin()
    await plugin.initialize()
    result = await plugin.execute(param="value")
    assert result["status"] == "success"

def test_plugin_schema():
    plugin = MyPlugin()
    schema = plugin.get_schema()
    assert "name" in schema
```

## API Integration

Plugins are automatically available through the REST API:

```bash
# List all plugins
GET /plugins

# Get plugin details
GET /plugins/{plugin_id}

# Execute a plugin
POST /api/v1/plugins/{plugin_id}/execute
{
    "action": "status",
    "parameters": {}
}

# Connect an integration plugin
POST /api/v1/plugins/{plugin_id}/connect
{
    "api_key": "your-key"
}
```

## Best Practices

1. **Always provide a `plugin` instance** at module level for discovery
2. **Handle errors gracefully** - return error dicts instead of raising exceptions
3. **Use async/await** for I/O operations
4. **Include proper metadata** with meaningful tags and description
5. **Implement `get_schema()`** for AI tool calling compatibility
6. **Write tests** for all plugin functionality
7. **Log important events** using the `logging` module
8. **Clean up resources** in `shutdown()` method

## Publishing Plugins

Plugins can be shared through the Windows AI marketplace:

1. Create your plugin following the patterns above
2. Test thoroughly with `pytest`
3. Submit via the marketplace API: `POST /api/marketplace/install`
4. Community plugins are reviewed before publication

---

*See also: [Plugin Index](../plugins/PLUGIN_INDEX.md) | [API Reference](../api/REST_API.md)*
