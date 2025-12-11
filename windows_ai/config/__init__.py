"""
Windows AI Configuration Package

Provides unified, type-safe configuration management for the entire application.

Usage:
    from windows_ai.config import get_config
    
    config = get_config()
    print(config.server.port)  # 8765
    print(config.llm.provider)  # "openai"
"""

from .unified_config import (
    AgentConfig,
    DatabaseConfig,
    EmbeddingConfig,
    LLMProviderConfig,
    LocalModelsConfig,
    LoggingConfig,
    PluginConfig,
    RAGConfig,
    SandboxConfig,
    SchedulerConfig,
    SecurityConfig,
    ServerConfig,
    UIConfig,
    WatcherConfig,
    WindowsAIConfig,
    get_config,
    reload_config,
    save_config,
    validate_config,
)

__all__ = [
    # Main config class
    "WindowsAIConfig",
    # Component configs
    "AgentConfig",
    "DatabaseConfig",
    "EmbeddingConfig",
    "LLMProviderConfig",
    "LocalModelsConfig",
    "LoggingConfig",
    "PluginConfig",
    "RAGConfig",
    "SandboxConfig",
    "SchedulerConfig",
    "SecurityConfig",
    "ServerConfig",
    "UIConfig",
    "WatcherConfig",
    # Helper functions
    "get_config",
    "reload_config",
    "save_config",
    "validate_config",
]
