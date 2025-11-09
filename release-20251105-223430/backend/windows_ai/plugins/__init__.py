"""
Windows AI Plugin System

Extensible plugin architecture for adding custom AI actions, tools, and integrations.
"""

from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
from windows_ai.plugins.loader import PluginLoader
from windows_ai.plugins.registry import PluginRegistry

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginType",
    "PluginLoader",
    "PluginRegistry",
]
