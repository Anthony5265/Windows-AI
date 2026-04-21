# Windows AI Python SDK

Official Python SDK for Windows AI application framework.

## Installation

```bash
pip install windows-ai-sdk
```

## Quick Start

```python
from windows_ai import WindowsAI, PluginManager, QueryExecutor

# Initialize Windows AI
ai = WindowsAI(
    api_key="your-api-key",
    base_url="http://localhost:8000/api/v1"
)

# Get plugin manager
plugin_manager = ai.plugins

# List all available plugins
plugins = plugin_manager.list_plugins()
for plugin in plugins:
    print(f"- {plugin.name}: {plugin.description}")

# Execute a query
result = ai.query("What plugins are available?")
print(result)
```

## Core Classes

### WindowsAI

Main client class for interacting with Windows AI.

```python
from windows_ai import WindowsAI

# Initialize client
ai = WindowsAI(
    api_key="your-api-key",
    base_url="http://localhost:8000/api/v1",
    timeout=30,
    verify_ssl=True
)

# Check health
health = ai.health()
print(f"API Status: {health.status}")
print(f"Version: {health.version}")

# Get version
version = ai.version()
print(f"Version: {version}")

# Close connection
ai.close()
```

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `health()` | Get API health status | `HealthStatus` |
| `version()` | Get API version | `str` |
| `query(input_data)` | Execute a query | `QueryResult` |
| `config()` | Get configuration | `Config` |
| `update_config(config)` | Update configuration | `Config` |
| `close()` | Close connection | `None` |

### PluginManager

Manage plugins and their lifecycle.

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")
pm = ai.plugins

# List plugins
plugins = pm.list_plugins()
for plugin in plugins:
    print(f"- {plugin.name}")

# Get plugin by name
plugin = pm.get_plugin("data_cleaner")
print(f"Name: {plugin.name}")
print(f"Version: {plugin.version}")
print(f"Description: {plugin.description}")

# Load plugin
pm.load_plugin("data_cleaner")

# Unload plugin
pm.unload_plugin("data_cleaner")

# Get plugin info
info = pm.get_plugin_info("data_cleaner")
print(info)

# Check if plugin is loaded
is_loaded = pm.is_plugin_loaded("data_cleaner")
print(f"Loaded: {is_loaded}")

# Get dependencies
deps = pm.get_plugin_dependencies("data_cleaner")
for dep in deps:
    print(f"- {dep}")
```

#### Plugin Data Structure

```python
@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    category: str
    dependencies: List[str]
    config_schema: Dict[str, Any]
    enabled: bool
```

### QueryExecutor

Execute queries using plugins.

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")
executor = ai.query_executor

# Execute simple query
result = executor.execute("SELECT * FROM data")
print(result.data)

# Execute with parameters
result = executor.execute(
    "SELECT * FROM data WHERE type = ?",
    params=("active",)
)

# Execute with timeout
result = executor.execute(
    "complex_query",
    timeout=60
)

# Get execution metadata
print(f"Execution Time: {result.execution_time}ms")
print(f"Result Count: {result.count}")
```

### AuthenticationManager

Handle API authentication.

```python
from windows_ai import WindowsAI, AuthenticationManager

# Initialize auth manager
auth = AuthenticationManager(
    base_url="http://localhost:8000/api/v1"
)

# Authenticate with credentials
token = auth.authenticate(
    username="user@example.com",
    password="password"
)

# Use token
ai = WindowsAI(api_key=token)

# Refresh token
new_token = auth.refresh_token(token)

# Validate token
is_valid = auth.validate_token(token)
print(f"Token Valid: {is_valid}")

# Logout
auth.logout(token)
```

### ConfigurationManager

Manage application configuration.

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")
config = ai.config

# Get configuration
current_config = config.get()
print(current_config)

# Get specific setting
log_level = config.get("log_level")
print(f"Log Level: {log_level}")

# Update configuration
config.update({
    "log_level": "DEBUG",
    "cache_enabled": True
})

# Reset to defaults
config.reset()

# Reload from file
config.reload()
```

## Advanced Usage

### Custom Request Headers

```python
from windows_ai import WindowsAI

ai = WindowsAI(
    api_key="your-api-key",
    custom_headers={
        "X-Custom-Header": "value",
        "X-Request-ID": "123"
    }
)
```

### Request/Response Logging

```python
from windows_ai import WindowsAI
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

ai = WindowsAI(
    api_key="your-api-key",
    debug=True
)

# All requests/responses will be logged
```

### Error Handling

```python
from windows_ai import WindowsAI
from windows_ai.exceptions import (
    WindowsAIError,
    AuthenticationError,
    PluginNotFoundError,
    QueryExecutionError,
    APIError
)

ai = WindowsAI(api_key="your-api-key")

try:
    result = ai.query("SELECT * FROM data")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except PluginNotFoundError as e:
    print(f"Plugin not found: {e}")
except QueryExecutionError as e:
    print(f"Query failed: {e}")
except APIError as e:
    print(f"API error: {e}")
except WindowsAIError as e:
    print(f"General error: {e}")
```

### Batch Operations

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")

# Batch load plugins
plugins_to_load = ["plugin1", "plugin2", "plugin3"]
ai.plugins.batch_load(plugins_to_load)

# Batch execute queries
queries = [
    "SELECT * FROM data WHERE type='A'",
    "SELECT * FROM data WHERE type='B'",
    "SELECT * FROM data WHERE type='C'"
]
results = ai.batch_query(queries)
for result in results:
    print(f"Found {result.count} records")
```

### Streaming Results

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")

# Stream large result sets
for row in ai.stream_query("SELECT * FROM large_table"):
    print(f"Processing: {row}")
```

### Async Operations

```python
import asyncio
from windows_ai import WindowsAIAsync

async def main():
    ai = WindowsAIAsync(api_key="your-api-key")
    
    # Execute queries concurrently
    results = await asyncio.gather(
        ai.query("Query 1"),
        ai.query("Query 2"),
        ai.query("Query 3")
    )
    
    for result in results:
        print(result)
    
    await ai.close()

# Run async operations
asyncio.run(main())
```

## Examples

### Data Processing Pipeline

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")

# Load pipeline plugins
ai.plugins.load_plugin("data_cleaner")
ai.plugins.load_plugin("data_enricher")
ai.plugins.load_plugin("data_profiler")

# Execute pipeline
input_data = {"raw_data": [...]}

# Step 1: Clean data
cleaned = ai.query("clean_data", input_data)

# Step 2: Enrich data
enriched = ai.query("enrich_data", cleaned)

# Step 3: Profile data
profile = ai.query("profile_data", enriched)

print(profile)
```

### Security Analysis

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")

# Load security plugins
ai.plugins.load_plugin("intrusion_detection")
ai.plugins.load_plugin("malware_scanner")

# Analyze file
file_path = "/path/to/file"
result = ai.query("scan_file", {"file": file_path})

print(f"Threats Found: {result.threats}")
print(f"Risk Level: {result.risk_level}")
```

### Performance Monitoring

```python
from windows_ai import WindowsAI

ai = WindowsAI(api_key="your-api-key")

# Load monitoring plugins
ai.plugins.load_plugin("cpu_optimizer")
ai.plugins.load_plugin("memory_profiler")

# Get performance metrics
metrics = ai.query("get_metrics", {})

print(f"CPU Usage: {metrics.cpu}%")
print(f"Memory Usage: {metrics.memory}%")
print(f"Active Plugins: {metrics.active_plugins}")
```

## API Reference

### Exceptions

- `WindowsAIError`: Base exception class
- `AuthenticationError`: Authentication failed
- `PluginNotFoundError`: Plugin not found
- `QueryExecutionError`: Query execution failed
- `APIError`: API error
- `ConnectionError`: Connection failed
- `TimeoutError`: Request timeout

### Data Types

```python
@dataclass
class HealthStatus:
    status: str
    version: str
    uptime: float
    timestamp: datetime

@dataclass
class QueryResult:
    data: Any
    execution_time: float
    count: int
    metadata: Dict[str, Any]

@dataclass
class Config:
    settings: Dict[str, Any]
    timestamp: datetime
```

## Configuration

```python
# .env file
WINDOWS_AI_API_KEY=your-api-key
WINDOWS_AI_BASE_URL=http://localhost:8000/api/v1
WINDOWS_AI_TIMEOUT=30
WINDOWS_AI_VERIFY_SSL=true
WINDOWS_AI_DEBUG=false
```

## Environment Variables

- `WINDOWS_AI_API_KEY`: API authentication key
- `WINDOWS_AI_BASE_URL`: Base URL for API
- `WINDOWS_AI_TIMEOUT`: Request timeout in seconds
- `WINDOWS_AI_VERIFY_SSL`: Verify SSL certificates
- `WINDOWS_AI_DEBUG`: Enable debug mode

## Troubleshooting

### Connection Issues

```python
from windows_ai import WindowsAI

try:
    ai = WindowsAI(api_key="your-api-key")
    health = ai.health()
    print(f"Connected: {health.status}")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Authentication Issues

```python
# Check API key
ai = WindowsAI(api_key="your-api-key")
try:
    ai.health()
except AuthenticationError:
    print("Invalid API key")
```

## Support

- [GitHub Issues](https://github.com/Anthony5265/Windows-AI/issues)
- [Documentation Hub](../README.md)
- [API Docs Index](./README.md)
- [Examples Index](../examples/README.md)

## License

MIT License - See [LICENSE](../LICENSE) for details
