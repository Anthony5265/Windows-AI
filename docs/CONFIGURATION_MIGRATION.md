# Configuration Migration Guide

## Overview

This guide helps migrate from scattered configuration classes to the unified configuration system.

## What Changed

### Before (17+ scattered config classes)
```python
# In multiple files across the codebase
from windows_ai.frameworks.unified_llm import LLMConfig
from windows_ai.embeddings import EmbeddingConfig
from windows_ai.plugin_validator import SandboxConfig
# ... 14 more imports

# Configuration scattered everywhere
llm_config = LLMConfig(provider="openai", model="gpt-4")
embed_config = EmbeddingConfig(model="text-embedding-3-small")
sandbox_config = SandboxConfig(memory_limit_mb=512)
```

### After (unified system)
```python
# Single import
from windows_ai.config import get_config

# All configuration in one place
config = get_config()
llm = config.llm.provider  # "openai"
model = config.llm.model  # "gpt-4"
embed_model = config.embedding.model  # "text-embedding-3-small"
memory_limit = config.sandbox.memory_limit_mb  # 512
```

## Benefits

1. **Single source of truth** - All configuration in one place
2. **Type safety** - Pydantic validation catches errors early
3. **Environment variables** - Easy deployment configuration
4. **No magic strings** - IDE autocomplete works everywhere
5. **Hot reload** - Change config without restart (development)
6. **Nested access** - Clean dot notation: `config.server.port`

## Migration Steps

### Step 1: Install Dependencies

```bash
pip install pydantic pydantic-settings
```

### Step 2: Update Imports

**Old:**
```python
from windows_ai.frameworks.unified_llm import LLMConfig
from windows_ai.embeddings import EmbeddingConfig
from windows_ai.hotkeys import HotkeyConfig
```

**New:**
```python
from windows_ai.config import get_config
```

### Step 3: Replace Direct Instantiation

**Old:**
```python
llm_config = LLMConfig(
    provider="openai",
    model="gpt-4",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)
```

**New:**
```python
config = get_config()
# Configuration loaded automatically from:
# 1. Default values
# 2. config.json (if exists)
# 3. Environment variables (WINDOWSAI_*)

# Access values
provider = config.llm.provider
model = config.llm.model
temperature = config.llm.temperature
```

### Step 4: Update Function Signatures

**Old:**
```python
def initialize_llm(config: LLMConfig) -> UnifiedLLMProvider:
    return UnifiedLLMProvider(
        provider=config.provider,
        model=config.model,
        api_key=config.api_key
    )
```

**New:**
```python
from windows_ai.config import get_config, LLMProviderConfig

def initialize_llm(llm_config: Optional[LLMProviderConfig] = None) -> UnifiedLLMProvider:
    if llm_config is None:
        llm_config = get_config().llm
    
    return UnifiedLLMProvider(
        provider=llm_config.provider,
        model=llm_config.model,
        api_key=llm_config.api_key
    )
```

### Step 5: Environment Variables

**Old (various approaches):**
```python
api_key = os.getenv("OPENAI_API_KEY")
server_port = int(os.getenv("PORT", "8765"))
```

**New (automatic with prefix):**
```bash
# .env file or environment
WINDOWSAI_LLM__API_KEY=sk-...
WINDOWSAI_LLM__PROVIDER=openai
WINDOWSAI_LLM__MODEL=gpt-4
WINDOWSAI_SERVER__PORT=8765
```

```python
# No code changes needed - automatically loaded
config = get_config()
print(config.llm.api_key)  # sk-...
print(config.server.port)  # 8765
```

## File-by-File Migration

### 1. windows_ai/frameworks/unified_llm.py

**Current:**
```python
class LLMConfig:
    def __init__(self, provider: str, model: str, **kwargs):
        self.provider = provider
        self.model = model
        # ...
```

**Migration:**
```python
from windows_ai.config import get_config, LLMProviderConfig

class UnifiedLLMProvider:
    def __init__(self, config: Optional[LLMProviderConfig] = None):
        if config is None:
            config = get_config().llm
        
        self.provider = config.provider
        self.model = config.model
        # ...
```

### 2. windows_ai/embeddings.py

**Current:**
```python
class EmbeddingConfig:
    def __init__(self, provider="openai", model="text-embedding-3-small"):
        self.provider = provider
        self.model = model
```

**Migration:**
```python
from windows_ai.config import get_config

class EmbeddingManager:
    def __init__(self):
        self.config = get_config().embedding
        self.provider = self.config.provider
        self.model = self.config.model
```

### 3. windows_ai/plugin_validator.py

**Current:**
```python
class SandboxConfig:
    def __init__(self, memory_limit_mb=512, cpu_limit_percent=50):
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
```

**Migration:**
```python
from windows_ai.config import get_config

class PluginValidator:
    def __init__(self):
        self.config = get_config().sandbox
        self.memory_limit = self.config.memory_limit_mb
        self.cpu_limit = self.config.cpu_limit_percent
```

## Configuration File Format

**data/config.json:**
```json
{
  "app_name": "Windows AI",
  "version": "2.0.0-alpha",
  "environment": "production",
  "server": {
    "host": "0.0.0.0",
    "port": 8765,
    "cors_origins": ["https://app.example.com"]
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "plugins": {
    "plugins_dir": "windows_ai/plugins",
    "auto_discover": true,
    "sandbox_enabled": true
  },
  "security": {
    "api_keys": ["your-api-key-here"],
    "rate_limit_enabled": true
  }
}
```

## Testing Your Migration

### 1. Basic Test

```python
from windows_ai.config import get_config

config = get_config()
print(f"Server: {config.server.host}:{config.server.port}")
print(f"LLM: {config.llm.provider} ({config.llm.model})")
print(f"Plugins: {config.plugins.plugins_dir}")
```

### 2. Validation Test

```python
from windows_ai.config import validate_config

errors = validate_config()
if errors:
    print("Configuration errors:")
    for component, error_list in errors.items():
        print(f"  {component}: {error_list}")
else:
    print("Configuration valid!")
```

### 3. Environment Variable Test

```bash
export WINDOWSAI_SERVER__PORT=9000
export WINDOWSAI_LLM__MODEL=gpt-4-turbo
```

```python
from windows_ai.config import get_config

config = get_config()
assert config.server.port == 9000
assert config.llm.model == "gpt-4-turbo"
```

## Common Patterns

### Pattern 1: Default + Override

```python
from windows_ai.config import get_config

def process_with_llm(custom_temperature: Optional[float] = None):
    config = get_config()
    temperature = custom_temperature or config.llm.temperature
    # Use temperature...
```

### Pattern 2: Component Configuration

```python
from windows_ai.config import get_config

class MyComponent:
    def __init__(self):
        config = get_config()
        self.server_config = config.server
        self.plugin_config = config.plugins
    
    def start(self):
        # Use self.server_config...
        pass
```

### Pattern 3: Nested Access

```python
from windows_ai.config import get_config

config = get_config()
# Dot notation
port = config.server.port

# Or helper method
port = config.get_nested('server.port', default=8765)
```

## Backward Compatibility

To maintain backward compatibility during migration:

```python
# windows_ai/frameworks/unified_llm.py (legacy support)

from windows_ai.config import get_config, LLMProviderConfig

# Old interface (deprecated)
class LLMConfig:
    """Deprecated: Use LLMProviderConfig from windows_ai.config"""
    def __init__(self, **kwargs):
        import warnings
        warnings.warn(
            "LLMConfig is deprecated. Use get_config().llm instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._config = LLMProviderConfig(**kwargs)
    
    def __getattr__(self, name):
        return getattr(self._config, name)
```

## Rollout Strategy

### Phase 1: Add Unified Config (Week 1)
- ✅ Create `windows_ai/config/unified_config.py`
- ✅ Create `windows_ai/config/__init__.py`
- ✅ Create migration guide
- ✅ Add tests for configuration system

### Phase 2: Core Modules (Week 2)
- Migrate `windows_ai/main.py` ConfigManager
- Migrate `windows_ai/frameworks/unified_llm.py`
- Migrate `windows_ai/embeddings.py`
- Update tests

### Phase 3: Plugin System (Week 3)
- Migrate `windows_ai/core/plugin_lifecycle.py`
- Migrate `windows_ai/plugin_validator.py`
- Update all Tier 1 plugins (65 plugins)
- Update tests

### Phase 4: Remaining Components (Week 4)
- Migrate all remaining config classes
- Remove deprecated code
- Update all documentation
- Full test suite validation

## Need Help?

If you encounter issues during migration:

1. **Check the examples** in `windows_ai/config/unified_config.py`
2. **Run validation** with `validate_config()`
3. **Check environment variables** with `os.environ`
4. **Review this guide** for your specific use case

## Quick Reference

### Import
```python
from windows_ai.config import get_config
```

### Access Configuration
```python
config = get_config()
value = config.component.setting
```

### Save Configuration
```python
from windows_ai.config import save_config
config = get_config()
config.server.port = 9000
save_config()
```

### Reload Configuration
```python
from windows_ai.config import reload_config
config = reload_config()  # Reloads from file
```

### Validate Configuration
```python
from windows_ai.config import validate_config
errors = validate_config()
```
