"""Plugin management package for the Windows AI installer."""

from installer.plugins.manager import Plugin, PluginManager, load_catalog
from installer.plugins.registry import PluginRegistry, discover_plugins

__all__ = [
    "Plugin",
    "PluginManager",
    "load_catalog",
    "PluginRegistry",
    "discover_plugins",
]
