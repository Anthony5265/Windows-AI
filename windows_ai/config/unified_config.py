"""
Unified Configuration System for Windows AI

Consolidates all scattered config classes into a single, type-safe configuration
schema using Pydantic. Eliminates magic strings and provides centralized config
management.

Architecture Decision:
- Single source of truth for all configuration
- Type-safe with Pydantic validation
- Environment variable support with dotenv
- Hierarchical configuration (default → file → env vars)
- Hot reload capability for development
- Supports both JSON and YAML configuration files
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Try to import yaml, but make it optional
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ============================================================================
# Core Application Configuration
# ============================================================================

class ServerConfig(BaseModel):
    """REST API server configuration"""
    host: str = Field(default="127.0.0.1", description="API server bind address")
    port: int = Field(default=8765, description="API server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes (dev only)")
    workers: int = Field(default=1, description="Number of worker processes")
    cors_origins: List[str] = Field(default=["http://localhost:*"], description="Allowed CORS origins")
    api_key_required: bool = Field(default=False, description="Require API key authentication")

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"Port must be positive, got {v}")
        return v


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    url: str = Field(default="sqlite:///data/windows_ai.db", description="Database connection URL")
    echo: bool = Field(default=False, description="Echo SQL statements (debug)")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    file: Optional[Path] = Field(default=None, description="Log file path (None = console only)")
    max_bytes: int = Field(default=10_000_000, description="Max log file size before rotation")
    backup_count: int = Field(default=5, description="Number of backup log files")

    model_config = SettingsConfigDict(validate_assignment=True)

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


# ============================================================================
# AI Model Configuration
# ============================================================================

class LLMProviderConfig(BaseModel):
    """LLM provider configuration"""
    provider: str = Field(default="openai", description="Provider name (openai, anthropic, google, etc.)")
    api_key: Optional[str] = Field(default=None, description="API key for cloud providers")
    api_base: Optional[str] = Field(default=None, description="Custom API base URL")
    model: str = Field(default="gpt-4o-mini", description="Model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens in response")
    timeout: int = Field(default=60, gt=0, description="Request timeout (seconds)")
    stream: bool = Field(default=True, description="Enable streaming responses")
    # Additional fields for flexible config format
    default_provider: Optional[str] = Field(default=None, description="Default provider alias")
    fallback_providers: List[str] = Field(default=[], description="Fallback provider chain")
    default_temperature: Optional[float] = Field(default=None, description="Default temperature alias")
    default_max_tokens: Optional[int] = Field(default=None, description="Default max tokens alias")
    providers: Dict[str, Any] = Field(default={}, description="Provider-specific settings")


class LocalModelsConfig(BaseModel):
    """Local AI models configuration"""
    enabled: bool = Field(default=False, description="Enable local model execution")
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    llama_cpp_path: Optional[Path] = Field(default=None, description="Path to llama.cpp executable")
    models_dir: Path = Field(default=Path("data/models"), description="Directory for model storage")
    gpu_layers: int = Field(default=-1, description="Number of GPU layers (-1 = auto)")


class EmbeddingConfig(BaseModel):
    """Embedding configuration"""
    provider: str = Field(default="openai", description="Embedding provider")
    model: str = Field(default="text-embedding-3-small", description="Embedding model")
    api_key: Optional[str] = Field(default=None, description="API key")
    chunk_size: int = Field(default=512, gt=0, description="Text chunk size for embedding")
    chunk_overlap: int = Field(default=50, ge=0, description="Overlap between chunks")
    dimensions: int = Field(default=1536, gt=0, description="Embedding vector dimensions")


# ============================================================================
# Plugin System Configuration
# ============================================================================

class PluginConfig(BaseModel):
    """Plugin system configuration"""
    plugins_dir: Path = Field(default=Path("windows_ai/plugins"), description="Plugin directory")
    auto_discover: bool = Field(default=True, description="Automatically discover plugins")
    enabled_plugins: List[str] = Field(default=[], description="Explicitly enabled plugins (empty = all)")
    disabled_plugins: List[str] = Field(default=[], description="Explicitly disabled plugins")
    sandbox_enabled: bool = Field(default=True, description="Enable plugin sandboxing")
    timeout: int = Field(default=300, gt=0, description="Plugin execution timeout (seconds)")
    max_concurrent: int = Field(default=10, gt=0, description="Max concurrent plugin executions")


class SandboxConfig(BaseModel):
    """Plugin sandbox configuration"""
    enabled: bool = Field(default=True, description="Enable sandbox isolation")
    memory_limit_mb: int = Field(default=512, gt=0, description="Memory limit per plugin (MB)")
    cpu_limit_percent: int = Field(default=50, gt=0, le=100, description="CPU limit percentage")
    network_access: bool = Field(default=True, description="Allow network access")
    file_system_access: bool = Field(default=False, description="Allow file system access")
    allowed_paths: List[Path] = Field(default=[], description="Allowed file system paths")


# ============================================================================
# Agent System Configuration
# ============================================================================

class AgentConfig(BaseModel):
    """AI agent configuration"""
    max_agents: int = Field(default=50, gt=0, description="Maximum concurrent agents")
    default_timeout: int = Field(default=600, gt=0, description="Default agent timeout (seconds)")
    enable_memory: bool = Field(default=True, description="Enable agent memory")
    memory_backend: str = Field(default="sqlite", description="Memory backend (sqlite, redis)")
    enable_tools: bool = Field(default=True, description="Enable agent tool use")
    max_iterations: int = Field(default=10, gt=0, description="Max agent reasoning iterations")


# ============================================================================
# RAG System Configuration
# ============================================================================

class RAGConfig(BaseModel):
    """RAG (Retrieval Augmented Generation) configuration"""
    enabled: bool = Field(default=True, description="Enable RAG system")
    vector_store: str = Field(default="chroma", description="Vector store backend")
    collection_name: str = Field(default="windows_ai_docs", description="Collection name")
    top_k: int = Field(default=5, gt=0, description="Number of results to retrieve")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    rerank: bool = Field(default=False, description="Enable reranking of results")


# ============================================================================
# UI Configuration
# ============================================================================

class UIConfig(BaseModel):
    """User interface configuration"""
    theme: str = Field(default="dark", description="UI theme (dark, light)")
    language: str = Field(default="en", description="UI language")
    auto_start: bool = Field(default=False, description="Auto-start application")
    minimize_to_tray: bool = Field(default=True, description="Minimize to system tray")
    notifications: bool = Field(default=True, description="Enable desktop notifications")
    hotkey: Optional[str] = Field(default="Ctrl+Alt+A", description="Global hotkey to show UI")


# ============================================================================
# Automation Configuration
# ============================================================================

class WatcherConfig(BaseModel):
    """Folder watcher configuration"""
    enabled: bool = Field(default=False, description="Enable folder watching")
    watched_paths: List[Path] = Field(default=[], description="Paths to watch")
    ignore_patterns: List[str] = Field(default=["*.tmp", "*.log", "__pycache__"], description="Ignore patterns")
    debounce_ms: int = Field(default=1000, gt=0, description="Debounce delay (milliseconds)")


class SchedulerConfig(BaseModel):
    """Task scheduler configuration"""
    enabled: bool = Field(default=False, description="Enable task scheduler")
    timezone: str = Field(default="UTC", description="Scheduler timezone")
    max_concurrent_tasks: int = Field(default=5, gt=0, description="Max concurrent scheduled tasks")


# ============================================================================
# Security Configuration
# ============================================================================

class SecurityConfig(BaseModel):
    """Security configuration"""
    api_keys: List[str] = Field(default=[], description="Valid API keys")
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, gt=0, description="Requests per time window")
    rate_limit_window: int = Field(default=60, gt=0, description="Time window (seconds)")
    content_filtering: bool = Field(default=True, description="Enable content filtering")
    pii_detection: bool = Field(default=True, description="Enable PII detection")


# ============================================================================
# Main Configuration Schema
# ============================================================================

class WindowsAIConfig(BaseSettings):
    """
    Unified Windows AI Configuration
    
    Loads configuration from:
    1. Default values
    2. config.json file
    3. Environment variables (WINDOWSAI_* prefix)
    
    Environment variables override file configuration.
    """
    model_config = SettingsConfigDict(
        env_prefix='WINDOWSAI_',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Application metadata
    app_name: str = Field(default="Windows AI", description="Application name")
    version: str = Field(default="2.0.0-alpha", description="Application version")
    environment: str = Field(default="development", description="Environment (development, production)")
    
    # Component configurations
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    llm: LLMProviderConfig = Field(
        default_factory=lambda: LLMProviderConfig(provider="openai", model="gpt-3.5-turbo")
    )
    local_models: LocalModelsConfig = Field(default_factory=LocalModelsConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    agents: AgentConfig = Field(default_factory=AgentConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    watcher: WatcherConfig = Field(default_factory=WatcherConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Custom settings
    custom: Dict[str, Any] = Field(default={}, description="Custom user settings")

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "WindowsAIConfig":
        """
        Load configuration from JSON or YAML file
        
        File type is determined by extension:
        - .json -> JSON format
        - .yaml, .yml -> YAML format (requires PyYAML)
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            WindowsAIConfig instance
        
        Raises:
            ImportError: If YAML file specified but PyYAML not installed
            FileNotFoundError: If config file doesn't exist
        """
        config_path = Path(config_path)
        if not config_path.exists():
            return cls()
        
        suffix = config_path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError(
                    "PyYAML is required to load YAML configuration files. "
                    "Install it with: pip install pyyaml"
                )
            
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif suffix == '.json':
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file extension: {suffix}. Use .json, .yaml, or .yml")
        
        return cls(**config_data)

    def to_file(self, config_path: Union[str, Path], format: str = 'auto') -> None:
        """
        Save configuration to JSON or YAML file
        
        Args:
            config_path: Path to save configuration
            format: File format ('json', 'yaml', or 'auto' to detect from extension)
        
        Raises:
            ImportError: If YAML format requested but PyYAML not installed
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine format
        if format == 'auto':
            suffix = config_path.suffix.lower()
            if suffix in ['.yaml', '.yml']:
                format = 'yaml'
            else:
                format = 'json'
        
        # Export configuration
        config_data = self.model_dump()
        
        if format == 'yaml':
            if not YAML_AVAILABLE:
                raise ImportError(
                    "PyYAML is required to save YAML configuration files. "
                    "Install it with: pip install pyyaml"
                )
            
            with open(config_path, 'w') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)
        else:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)

    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """
        Get nested configuration value using dot notation
        
        Example: config.get_nested('server.port') -> 8765
        """
        keys = key_path.split('.')
        value = self
        
        for key in keys:
            if isinstance(value, BaseModel):
                value = getattr(value, key, None)
            elif isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            
            if value is None:
                return default
        
        return value

    def set_nested(self, key_path: str, value: Any) -> None:
        """
        Set nested configuration value using dot notation
        
        Example: config.set_nested('server.port', 9000)
        """
        keys = key_path.split('.')
        obj = self
        
        for key in keys[:-1]:
            obj = getattr(obj, key)
        
        setattr(obj, keys[-1], value)


# ============================================================================
# Global Configuration Instance
# ============================================================================

_config: Optional[WindowsAIConfig] = None


def get_config(config_path: Optional[Union[str, Path]] = None) -> WindowsAIConfig:
    """
    Get global configuration instance
    
    Automatically searches for config files in order:
    1. Specified config_path (if provided)
    2. data/config.json
    3. windows_ai/config/default.yaml
    4. Default configuration (no file)
    
    Args:
        config_path: Path to configuration file (optional)
    
    Returns:
        Global WindowsAIConfig instance
    """
    global _config
    
    if _config is None:
        # Search for config file
        search_paths = []
        
        if config_path is not None:
            search_paths.append(Path(config_path))
        
        # Default search locations
        search_paths.extend([
            Path("data/config.json"),
            Path("data/config.yaml"),
            Path("windows_ai/config/default.yaml"),
            Path(__file__).parent / "default.yaml"
        ])
        
        # Find first existing config file
        found_config = None
        for path in search_paths:
            if path.exists():
                found_config = path
                break
        
        if found_config:
            _config = WindowsAIConfig.from_file(found_config)
        else:
            _config = WindowsAIConfig()
    
    return _config


def reload_config(config_path: Optional[Union[str, Path]] = None) -> WindowsAIConfig:
    """
    Reload configuration from file
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Reloaded WindowsAIConfig instance
    """
    global _config
    _config = None
    return get_config(config_path)


def save_config(config_path: Optional[Union[str, Path]] = None) -> None:
    """
    Save current configuration to file
    
    Args:
        config_path: Path to save configuration (default: data/config.json)
    """
    config = get_config()
    
    if config_path is None:
        config_path = Path("data/config.json")
    else:
        config_path = Path(config_path)
    
    config.to_file(config_path)


# ============================================================================
# Configuration Validation
# ============================================================================

def validate_config() -> Dict[str, List[str]]:
    """
    Validate configuration and return any errors
    
    Returns:
        Dictionary of validation errors by component
    """
    config = get_config()
    errors: Dict[str, List[str]] = {}
    
    # Validate API keys for cloud providers
    if config.llm.provider in ['openai', 'anthropic', 'google'] and not config.llm.api_key:
        errors.setdefault('llm', []).append(f"API key required for provider: {config.llm.provider}")
    
    # Validate paths exist
    if config.local_models.enabled and config.local_models.llama_cpp_path:
        if not config.local_models.llama_cpp_path.exists():
            errors.setdefault('local_models', []).append(
                f"llama.cpp path does not exist: {config.local_models.llama_cpp_path}"
            )
    
    # Validate database URL format
    if not config.database.url.startswith(('sqlite:///', 'postgresql://', 'mysql://')):
        errors.setdefault('database', []).append(
            f"Invalid database URL format: {config.database.url}"
        )
    
    return errors


if __name__ == "__main__":
    # Example usage
    config = get_config()
    print(f"Application: {config.app_name} v{config.version}")
    print(f"Server: {config.server.host}:{config.server.port}")
    print(f"LLM Provider: {config.llm.provider} ({config.llm.model})")
    print(f"Plugins directory: {config.plugins.plugins_dir}")
    
    # Validate configuration
    errors = validate_config()
    if errors:
        print("\nConfiguration errors:")
        for component, error_list in errors.items():
            print(f"  {component}:")
            for error in error_list:
                print(f"    - {error}")
