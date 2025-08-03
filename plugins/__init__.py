"""Plugin package exposing the plugin manager and catalog loader."""

from .manager import Plugin, PluginManager, load_catalog

__all__ = ["Plugin", "PluginManager", "load_catalog"]

