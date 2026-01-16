# Configuration Consolidation - Windows AI

## Overview

This directory contains the unified configuration system for Windows AI, replacing scattered configuration files across the project.

## Configuration Files

### Current Location (config/)
- `pytest.ini` - Pytest configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `defaults.json` - Default configuration values
- `proxy.yaml` - Proxy settings
- `search.yaml` - Search configuration
- `fix_bot.json` - Automated fix bot configuration
- `pr_fix_bot.json` - PR fix bot configuration
- `project-metadata.json` - Project metadata

### Migration Progress

#### Phase 1: Foundation ✓ COMPLETE
- [x] Create unified_config.py with dataclass-based configuration
- [x] Implement config loading from YAML/JSON
- [x] Support environment variable overrides
- [x] Singleton pattern for global config access
- [x] Dot-notation for nested config access

#### Phase 2: Integration (IN PROGRESS)
- [ ] Update windows_ai/main.py to use unified config
- [ ] Update windows_ai/__main__.py to use unified config
- [ ] Update windows_ai/api/server.py to use unified config
- [ ] Update tests/conftest.py to use unified config

#### Phase 3: Consolidation (PENDING)
- [ ] Merge duplicate configs from different domains
- [ ] Remove config files from legacy locations
- [ ] Update documentation
- [ ] Create migration script for existing deployments

## Usage

### Python Code

```python
from windows_ai.config.unified_config import get_config

# Get global config instance
config = get_config()

# Access values using dot notation
api_title = config.get_nested('api.title', 'Default Title')
server_port = config.get_nested('server.port', 8010)

# Set values
config.set_nested('server.debug', True)

# Save to file
config.save('./config/config.yaml')
```

### Environment Variables

Override configuration using environment variables:

```bash
export WINDOWS_AI_HOST=0.0.0.0
export WINDOWS_AI_PORT=9000
export WINDOWS_AI_DEBUG=true
export WINDOWS_AI_ENV=production
```

### Configuration File

Create a `config.yaml` or `config.json` file:

```yaml
app_name: Windows AI
version: 2.0.0
environment: development

server:
  host: 127.0.0.1
  port: 8010
  debug: false
  workers: 1
  cors_origins:
    - "*"

security:
  encryption_enabled: true
  encryption_algorithm: AES-256-GCM
  api_key_required: false

plugins:
  enabled: true
  auto_load: true
  max_plugins: 1000

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Configuration Structure

### ServerConfig
- `host` (str): Server host address
- `port` (int): Server port
- `debug` (bool): Debug mode
- `reload` (bool): Auto-reload on changes
- `workers` (int): Number of worker processes
- `cors_origins` (list): CORS allowed origins
- `log_level` (str): Log level

### DatabaseConfig
- `type` (str): Database type (sqlite, postgresql, etc.)
- `path` (str): Database file path or connection string
- `echo` (bool): SQL echo logging
- `pool_size` (int): Connection pool size

### SecurityConfig
- `encryption_enabled` (bool): Enable data encryption
- `encryption_algorithm` (str): Encryption algorithm
- `api_key_required` (bool): Require API key for all endpoints
- `jwt_enabled` (bool): Enable JWT authentication
- `sandbox_enabled` (bool): Enable sandbox mode
- `sandbox_policy` (str): Sandbox policy (strict, moderate, permissive)

### PluginConfig
- `enabled` (bool): Enable plugin system
- `auto_load` (bool): Auto-load plugins at startup
- `plugins_dir` (str): Directory containing plugins
- `registry_file` (str): Plugin registry file path
- `max_plugins` (int): Maximum number of plugins

### LoggingConfig
- `level` (str): Logging level
- `format` (str): Log message format
- `file_path` (str): Log file path
- `file_max_bytes` (int): Max log file size
- `file_backup_count` (int): Number of backup files

### APIConfig
- `title` (str): API title
- `description` (str): API description
- `version` (str): API version
- `docs_url` (str): Swagger docs URL
- `redoc_url` (str): ReDoc URL
- `openapi_url` (str): OpenAPI schema URL
- `enable_cors` (bool): Enable CORS

## Migration Guide

### For Existing Code

**Before:**
```python
import yaml

with open('config/default.yaml') as f:
    config = yaml.safe_load(f)

api_title = config.get('api', {}).get('title', 'API')
```

**After:**
```python
from windows_ai.config.unified_config import get_config

config = get_config()
api_title = config.get_nested('api.title', 'API')
```

### For Tests

**Before:**
```python
@pytest.fixture
def config():
    return yaml.safe_load(open('config/default.yaml'))
```

**After:**
```python
@pytest.fixture
def config():
    from windows_ai.config.unified_config import UnifiedConfig, reset_config
    reset_config()  # Ensure fresh config for tests
    return get_config()
```

## File Consolidation Map

See `CONSOLIDATION_MAP.md` for a complete list of all configuration files that have been consolidated or are pending consolidation.

## Testing

Run tests to verify configuration:

```bash
# Run all config-related tests
pytest tests/ -k config -v

# Run specific test
pytest tests/test_quick_wins.py::test_config_files_exist -v
```

## Future Enhancements

- [ ] Config validation schema
- [ ] Config versioning and migration
- [ ] Config hot-reload
- [ ] Config encryption for sensitive values
- [ ] Web UI for configuration management
- [ ] Configuration inheritance (dev, staging, production)
- [ ] Configuration diff and audit logging

## Support

For questions or issues related to configuration:
1. Check this README
2. Review CONSOLIDATION_MAP.md
3. Check unified_config.py docstrings
4. See examples in windows_ai/config/
