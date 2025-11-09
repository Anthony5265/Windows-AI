"""
Plugin Loader

Discovers and loads plugins from the plugins directory.
"""

import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import List, Dict, Any, Type, Optional

from windows_ai.plugins.base import Plugin, PluginMetadata

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Discovers and loads plugins from the filesystem.
    """

    def __init__(self, plugins_dir: Path):
        """
        Initialize the plugin loader.

        Args:
            plugins_dir: Directory containing plugin modules
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def discover_plugins(self) -> List[Path]:
        """
        Discover all plugin files in the plugins directory.

        Returns:
            List of paths to plugin files
        """
        plugin_files = []

        # Look for Python files
        for file in self.plugins_dir.rglob("*.py"):
            # Skip __init__.py and __pycache__
            if file.name.startswith("__"):
                continue

            plugin_files.append(file)

        logger.info(f"Discovered {len(plugin_files)} plugin files")
        return plugin_files

    def load_plugin_module(self, plugin_path: Path) -> Optional[Any]:
        """
        Load a plugin module from a file path.

        Args:
            plugin_path: Path to the plugin Python file

        Returns:
            Loaded module or None if loading failed
        """
        try:
            # Create module name from file path
            module_name = f"windows_ai.plugins.custom.{plugin_path.stem}"

            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec is None or spec.loader is None:
                logger.error(f"Could not load spec for {plugin_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            logger.debug(f"Loaded plugin module: {module_name}")
            return module

        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_path}: {e}")
            return None

    def extract_plugin_classes(self, module: Any) -> List[Type[Plugin]]:
        """
        Extract Plugin classes from a module.

        Args:
            module: Python module to inspect

        Returns:
            List of Plugin class types found in the module
        """
        plugin_classes = []

        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a subclass of Plugin (but not Plugin itself)
            if issubclass(obj, Plugin) and obj is not Plugin:
                # Make sure it's defined in this module, not imported
                if obj.__module__ == module.__name__:
                    plugin_classes.append(obj)

        return plugin_classes

    def instantiate_plugin(self, plugin_class: Type[Plugin]) -> Optional[Plugin]:
        """
        Instantiate a plugin class.

        Args:
            plugin_class: Plugin class to instantiate

        Returns:
            Plugin instance or None if instantiation failed
        """
        try:
            # Check if the class has a get_metadata method
            if hasattr(plugin_class, 'get_metadata'):
                metadata = plugin_class.get_metadata()
            else:
                # Try to create default metadata from class docstring
                metadata = PluginMetadata(
                    id=plugin_class.__name__.lower(),
                    name=plugin_class.__name__,
                    description=plugin_class.__doc__ or "No description",
                    version="0.1.0",
                    author="Unknown",
                    plugin_type="action"
                )

            instance = plugin_class(metadata)
            logger.info(f"Instantiated plugin: {metadata.name}")
            return instance

        except Exception as e:
            logger.error(f"Error instantiating plugin {plugin_class.__name__}: {e}")
            return None

    def load_all_plugins(self) -> List[Plugin]:
        """
        Discover and load all plugins from the plugins directory.

        Returns:
            List of loaded plugin instances
        """
        loaded_plugins = []

        plugin_files = self.discover_plugins()

        for plugin_file in plugin_files:
            # Load the module
            module = self.load_plugin_module(plugin_file)
            if module is None:
                continue

            # Extract plugin classes
            plugin_classes = self.extract_plugin_classes(module)

            # Instantiate each plugin class
            for plugin_class in plugin_classes:
                plugin = self.instantiate_plugin(plugin_class)
                if plugin:
                    loaded_plugins.append(plugin)

        logger.info(f"Loaded {len(loaded_plugins)} plugins successfully")
        return loaded_plugins

    def reload_plugin(self, plugin_id: str, plugins: List[Plugin]) -> Optional[Plugin]:
        """
        Reload a specific plugin.

        Args:
            plugin_id: ID of the plugin to reload
            plugins: List of current plugins

        Returns:
            Reloaded plugin instance or None
        """
        # Find the plugin
        old_plugin = None
        for plugin in plugins:
            if plugin.metadata.id == plugin_id:
                old_plugin = plugin
                break

        if old_plugin is None:
            logger.warning(f"Plugin {plugin_id} not found for reload")
            return None

        # Reload all plugins and find the new instance
        new_plugins = self.load_all_plugins()
        for plugin in new_plugins:
            if plugin.metadata.id == plugin_id:
                logger.info(f"Reloaded plugin: {plugin_id}")
                return plugin

        return None
