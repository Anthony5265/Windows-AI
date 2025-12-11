# Windows AI - Unified Configuration System

**Complete configuration management for the Windows AI platform**

## 📋 Overview

The unified configuration system provides a centralized, type-safe approach to managing all Windows AI settings. Built on Pydantic, it consolidates 17+ scattered config classes into a single source of truth.

### Key Features

- ✅ **Single Source of Truth** - One configuration system for the entire platform
- ✅ **Type Safety** - Pydantic validation ensures correctness
- ✅ **Multiple Formats** - Supports both JSON and YAML configuration files
- ✅ **Environment Variables** - Override any setting via `WINDOWSAI_*` env vars
- ✅ **Hierarchical Loading** - Defaults → File → Environment variables
- ✅ **Auto-Discovery** - Automatically searches standard locations for config files
- ✅ **Hot Reload** - Reload configuration without restarting
- ✅ **Dot Notation** - Access nested values with `config.get_nested('server.port')`

## 🚀 Quick Start

### Basic Usage

```python
from windows_ai.config.unified_config import get_config

# Load configuration (auto-searches for config files)
config = get_config()

# Access configuration values
print(f"Server running on {config.server.host}:{config.server.port}")
print(f"Using LLM provider: {config.llm.provider}")

# Use nested access
api_title = config.get_nested('api.title', 'Windows AI API')

# Modify configuration
config.server.port = 8080
config.set_nested('llm.temperature', 0.8)

# Save changes
config.to_file('data/config.yaml', format='yaml')
```

### Loading from Specific File

```python
from windows_ai.config.unified_config import WindowsAIConfig

# Load from JSON
config = WindowsAIConfig.from_file('my_config.json')

# Load from YAML
config = WindowsAIConfig.from_file('my_config.yaml')

# Auto-detect format from extension
config = WindowsAIConfig.from_file('config.yml')  # Loads as YAML
```

### Environment Variables

Override any configuration value using environment variables with the `WINDOWSAI_` prefix:

```bash
# Set server port
export WINDOWSAI_SERVER__PORT=8080

# Set LLM provider
export WINDOWSAI_LLM__PROVIDER=anthropic

# Set API key
export WINDOWSAI_LLM__API_KEY=sk-ant-xxxxx

# Nested values use double underscore
export WINDOWSAI_LOCAL_MODELS__LLAMA_CPP_PATH=/path/to/llama.cpp
```

## 📖 Configuration Structure

The configuration is organized into 14 specialized sections:

### 1. Server Configuration (`ServerConfig`)

REST API server settings:

```python
config.server.host          # API server bind address (default: "127.0.0.1")
config.server.port          # API server port (default: 8765)
config.server.reload        # Auto-reload on code changes (default: False)
config.server.workers       # Number of worker processes (default: 1)
config.server.cors_origins  # Allowed CORS origins (default: ["http://localhost:*"])
config.server.api_key_required  # Require API key auth (default: False)
```

### 2. Database Configuration (`DatabaseConfig`)

Database connection settings:

```python
config.database.url     # Database connection URL (default: "sqlite:///data/windows_ai.db")
config.database.echo    # Echo SQL statements for debugging (default: False)
```

### 3. Logging Configuration (`LoggingConfig`)

Application logging settings:

```python
config.logging.level              # Log level (default: "INFO")
config.logging.format             # Log format string
config.logging.file_path          # Log file path (default: Path("data/logs/windows_ai.log"))
config.logging.max_file_size_mb   # Max log file size (default: 100)
config.logging.backup_count       # Number of backup logs (default: 5)
```

### 4. LLM Provider Configuration (`LLMProviderConfig`)

Language model provider settings:

```python
config.llm.provider        # LLM provider (default: "litellm")
config.llm.api_key         # API key for cloud providers
config.llm.model           # Model name (default: "gpt-4")
config.llm.temperature     # Sampling temperature (default: 0.7)
config.llm.max_tokens      # Maximum tokens (default: 2000)
config.llm.timeout         # Request timeout in seconds (default: 60)
```

### 5. Local Models Configuration (`LocalModelsConfig`)

Local AI model settings:

```python
config.local_models.enabled           # Enable local models (default: True)
config.local_models.llama_cpp_path    # Path to llama.cpp binary
config.local_models.models_dir        # Model storage directory
config.local_models.default_model     # Default local model
config.local_models.context_length    # Max context length (default: 4096)
config.local_models.gpu_layers        # GPU layers to use (default: 0)
```

### 6. Embedding Configuration (`EmbeddingConfig`)

Text embedding settings:

```python
config.embedding.provider      # Embedding provider (default: "openai")
config.embedding.model         # Embedding model (default: "text-embedding-ada-002")
config.embedding.dimensions    # Embedding dimensions (default: 1536)
config.embedding.batch_size    # Batch processing size (default: 100)
```

### 7. Plugin Configuration (`PluginConfig`)

Plugin system settings:

```python
config.plugins.enabled               # Enable plugin system (default: True)
config.plugins.auto_load             # Auto-load plugins on startup (default: True)
config.plugins.plugin_directories    # Plugin search paths
config.plugins.disabled_plugins      # List of disabled plugin IDs
config.plugins.max_execution_time    # Max plugin execution time (default: 300)
```

### 8. Sandbox Configuration (`SandboxConfig`)

Security sandbox settings:

```python
config.sandbox.enabled            # Enable sandbox (default: True)
config.sandbox.level              # Sandbox level: "none", "minimal", "standard", "strict", "maximum"
config.sandbox.max_memory_mb      # Max memory usage (default: 512)
config.sandbox.max_cpu_percent    # Max CPU usage (default: 80)
config.sandbox.timeout_seconds    # Execution timeout (default: 300)
config.sandbox.allowed_paths      # Whitelisted file paths
config.sandbox.blocked_paths      # Blacklisted file paths
```

### 9. Agent Configuration (`AgentConfig`)

Multi-agent system settings:

```python
config.agents.enabled              # Enable agent system (default: True)
config.agents.max_concurrent       # Max concurrent agents (default: 10)
config.agents.default_timeout      # Default agent timeout (default: 300)
config.agents.auto_cleanup         # Auto-cleanup finished agents (default: True)
```

### 10. RAG Pipeline Configuration (`RAGConfig`)

Retrieval-Augmented Generation settings:

```python
config.rag.enabled               # Enable RAG pipeline (default: True)
config.rag.chunk_size            # Document chunk size (default: 512)
config.rag.chunk_overlap         # Chunk overlap tokens (default: 50)
config.rag.top_k                 # Top-K retrieval results (default: 5)
config.rag.similarity_threshold  # Min similarity score (default: 0.7)
```

### 11. UI Configuration (`UIConfig`)

User interface settings:

```python
config.ui.theme              # UI theme: "light", "dark", "system" (default: "system")
config.ui.language           # UI language (default: "en")
config.ui.font_size          # Font size in pixels (default: 14)
config.ui.show_advanced      # Show advanced features (default: False)
```

### 12. Watcher Configuration (`WatcherConfig`)

File system watcher settings:

```python
config.watcher.enabled          # Enable file watcher (default: True)
config.watcher.watch_paths      # Paths to watch
config.watcher.ignore_patterns  # Patterns to ignore
config.watcher.debounce_ms      # Event debounce time (default: 1000)
```

### 13. Scheduler Configuration (`SchedulerConfig`)

Task scheduler settings:

```python
config.scheduler.enabled           # Enable scheduler (default: True)
config.scheduler.max_concurrent    # Max concurrent scheduled tasks (default: 5)
config.scheduler.default_timezone  # Default timezone (default: "UTC")
```

### 14. Security Configuration (`SecurityConfig`)

Application security settings:

```python
config.security.api_keys_enabled    # Enable API key auth (default: False)
config.security.rate_limiting       # Enable rate limiting (default: True)
config.security.max_requests_per_minute  # Rate limit (default: 60)
config.security.allowed_ips         # IP whitelist
config.security.blocked_ips         # IP blacklist
```

## 📁 Configuration Files

### Default Configuration Location

The configuration system automatically searches these locations (in order):

1. **Specified path** - If provided to `get_config(config_path="...")`
2. `data/config.json` - User JSON configuration
3. `data/config.yaml` - User YAML configuration
4. `windows_ai/config/default.yaml` - Default YAML configuration
5. **Defaults** - Built-in default values if no file found

### JSON Configuration Example

```json
{
  "version": "2.0.0",
  "server": {
    "host": "127.0.0.1",
    "port": 8765,
    "workers": 4,
    "cors_origins": ["http://localhost:3000"]
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "database": {
    "url": "postgresql://user:pass@localhost/windows_ai"
  },
  "plugins": {
    "enabled": true,
    "auto_load": true,
    "disabled_plugins": ["legacy-plugin-id"]
  }
}
```

### YAML Configuration Example

```yaml
version: "2.0.0"

server:
  host: "127.0.0.1"
  port: 8765
  workers: 4
  cors_origins:
    - "http://localhost:3000"
    - "http://127.0.0.1:3000"

llm:
  provider: "anthropic"
  model: "claude-3-opus"
  temperature: 0.7
  max_tokens: 4000

database:
  url: "postgresql://user:pass@localhost/windows_ai"
  echo: false

plugins:
  enabled: true
  auto_load: true
  disabled_plugins:
    - "legacy-plugin-id"
```

## 🔧 Advanced Usage

### Nested Value Access

Use dot notation to access deeply nested configuration values:

```python
# Get nested value with default
title = config.get_nested('api.title', 'Windows AI API')

# Set nested value
config.set_nested('server.cors_origins', ['http://example.com'])

# Access deeply nested values
max_memory = config.get_nested('sandbox.max_memory_mb', 512)
```

### Hot Reloading

Reload configuration without restarting the application:

```python
from windows_ai.config.unified_config import reload_config

# Reload from default location
config = reload_config()

# Reload from specific file
config = reload_config('data/new_config.yaml')
```

### Saving Configuration

Save current configuration to a file:

```python
from windows_ai.config.unified_config import save_config

# Save to JSON (default)
save_config('data/config.json')

# Save to YAML
config.to_file('data/config.yaml', format='yaml')

# Auto-detect format from extension
config.to_file('data/config.yml')  # Saves as YAML
```

### Validation

Validate configuration and get error details:

```python
from windows_ai.config.unified_config import validate_config

errors = validate_config()

if errors:
    for component, error_list in errors.items():
        print(f"{component}:")
        for error in error_list:
            print(f"  - {error}")
else:
    print("Configuration is valid!")
```

### Manager Integration Pattern

All managers should accept and use WindowsAIConfig:

```python
from windows_ai.config.unified_config import WindowsAIConfig

class MyManager:
    def __init__(self, config: WindowsAIConfig):
        """
        Initialize manager with configuration
        
        Args:
            config: WindowsAIConfig instance
        """
        self.config = config
        self._initialized = False
    
    async def initialize(self):
        """Initialize manager using configuration values"""
        # Access config values
        self.timeout = self.config.llm.timeout
        self.max_tokens = self.config.llm.max_tokens
        
        # Get nested values
        storage_path = self.config.get_nested('storage.data_dir', 'data/')
        
        self._initialized = True
```

### Plugin Integration Pattern

Plugins can access configuration through the orchestrator:

```python
from windows_ai.plugins.base import Plugin

class MyPlugin(Plugin):
    async def execute(self, **kwargs):
        # Access config from orchestrator
        config = kwargs.get('config')
        
        if config:
            # Use config values
            timeout = config.llm.timeout
            model = config.llm.model
        
        # Plugin implementation
        result = await self._do_work()
        
        return {"status": "success", "result": result}
```

## 🔒 Security Considerations

### API Keys

**Never commit API keys to version control!** Use environment variables:

```bash
# Set in environment
export WINDOWSAI_LLM__API_KEY=sk-xxxxx

# Or use .env file (add to .gitignore)
echo "WINDOWSAI_LLM__API_KEY=sk-xxxxx" >> .env
```

### Sensitive Configuration

For sensitive values, prefer environment variables over config files:

- ✅ Use env vars for: API keys, passwords, tokens, secrets
- ✅ Use config files for: Ports, paths, feature flags, timeouts
- ⚠️ Never commit: `.env`, `config.local.yaml`, files with secrets

### Configuration Validation

Always validate configuration on startup:

```python
from windows_ai.config.unified_config import get_config, validate_config

config = get_config()
errors = validate_config()

if errors:
    logger.error("Configuration validation failed:")
    for component, error_list in errors.items():
        for error in error_list:
            logger.error(f"  {component}: {error}")
    raise RuntimeError("Invalid configuration")
```

## 🐛 Troubleshooting

### Configuration Not Loading

```python
# Check which config file is being used
from windows_ai.config.unified_config import get_config
import logging

logging.basicConfig(level=logging.DEBUG)
config = get_config()  # Will log which file it loads
```

### Environment Variables Not Working

Ensure you're using the correct format:

```bash
# ✅ Correct
export WINDOWSAI_SERVER__PORT=8080

# ❌ Wrong (single underscore)
export WINDOWSAI_SERVER_PORT=8080

# ❌ Wrong (missing prefix)
export SERVER__PORT=8080
```

### YAML Files Not Loading

Install PyYAML if not already installed:

```bash
pip install pyyaml
```

Without PyYAML, the system falls back to JSON only:

```python
# Check if YAML is available
from windows_ai.config.unified_config import YAML_AVAILABLE

if YAML_AVAILABLE:
    print("YAML support enabled")
else:
    print("YAML support not available - install PyYAML")
```

### Invalid Configuration Values

Check validation errors:

```python
from windows_ai.config.unified_config import validate_config

errors = validate_config()
print(errors)  # Shows which values are invalid
```

## 📚 Best Practices

1. **Use Environment Variables for Secrets** - Never hardcode API keys
2. **Validate on Startup** - Always validate configuration before running
3. **Document Custom Settings** - Add comments to your config files
4. **Version Your Config** - Keep config files in version control (except secrets)
5. **Use Defaults** - Provide sensible defaults for all values
6. **Test Configuration Changes** - Validate before deploying
7. **Use Type Hints** - Leverage Pydantic's type safety
8. **Organize by Component** - Group related settings together
9. **Hot Reload in Development** - Use `reload_config()` during development
10. **Monitor Configuration** - Log when configuration changes

## 🔗 Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Development guide with configuration patterns
- [default.yaml](default.yaml) - Default configuration values
- [unified_config.py](unified_config.py) - Configuration implementation

## 📝 Migration Guide

### Migrating from Old Config System

If you're migrating from the old scattered config classes:

**Before (Old Pattern):**

```python
# Multiple config imports
from windows_ai.config import Config
from windows_ai.api.server_config import ServerConfig
from windows_ai.agents.agent_config import AgentConfig

# Multiple config objects
app_config = Config()
server_config = ServerConfig()
agent_config = AgentConfig()
```

**After (New Pattern):**

```python
# Single import
from windows_ai.config.unified_config import get_config

# Single config object
config = get_config()

# Access all settings
app_version = config.version
server_port = config.server.port
agent_timeout = config.agents.default_timeout
```

### Configuration File Migration

1. **Identify all configuration sources** in your codebase
2. **Extract values** into a single YAML or JSON file
3. **Update code** to use `get_config()` instead of scattered configs
4. **Test thoroughly** with the new configuration system
5. **Remove old config files** once migration is complete

## 💡 Examples

### Complete Application Setup

```python
from windows_ai.config.unified_config import get_config, validate_config
from windows_ai.core.orchestrator import WindowsAI
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load and validate configuration
config = get_config('config.yaml')
errors = validate_config()

if errors:
    logger.error("Configuration errors found:")
    for component, error_list in errors.items():
        for error in error_list:
            logger.error(f"  {component}: {error}")
    exit(1)

# Initialize Windows AI with configuration
ai = WindowsAI()
await ai.initialize(config=config)

# Use configuration values
logger.info(f"Server starting on {config.server.host}:{config.server.port}")
logger.info(f"Using LLM provider: {config.llm.provider}")

# Start server with config
from windows_ai.api.server import start_server
start_server(
    host=config.server.host,
    port=config.server.port,
    reload=config.server.reload
)
```

### Dynamic Configuration Updates

```python
from windows_ai.config.unified_config import get_config

config = get_config()

# Update configuration dynamically
if high_traffic_mode:
    config.server.workers = 8
    config.llm.timeout = 30
    config.rag.top_k = 10
    
# Save updated configuration
config.to_file('data/config.yaml', format='yaml')

# Reload in other processes
from windows_ai.config.unified_config import reload_config
config = reload_config()
```

---

**For more information, see the [main documentation](../../README.md) or [development guide](../../CLAUDE.md).**
