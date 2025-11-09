"""
Plugin Registry

Manages loaded plugins and provides access to them.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from windows_ai.plugins.base import Plugin, PluginType
from windows_ai.plugins.loader import PluginLoader

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for all loaded plugins.
    """

    def __init__(self, plugins_dir: Path):
        """
        Initialize the plugin registry.

        Args:
            plugins_dir: Directory containing plugins
        """
        self.plugins_dir = Path(plugins_dir)
        self.loader = PluginLoader(self.plugins_dir)
        self.plugins: Dict[str, Plugin] = {}
        self._initialized_plugins: set = set()

    async def load_plugins(self):
        """
        Load all plugins from the plugins directory.
        """
        logger.info("Loading plugins...")

        plugins = self.loader.load_all_plugins()

        for plugin in plugins:
            self.plugins[plugin.metadata.id] = plugin

        logger.info(f"Loaded {len(self.plugins)} plugins")

    async def initialize_plugins(self):
        """
        Initialize all enabled plugins.
        """
        logger.info("Initializing plugins...")

        for plugin_id, plugin in self.plugins.items():
            if not plugin.metadata.enabled:
                logger.debug(f"Skipping disabled plugin: {plugin_id}")
                continue

            if plugin_id in self._initialized_plugins:
                logger.debug(f"Plugin already initialized: {plugin_id}")
                continue

            try:
                success = await plugin.initialize()
                if success:
                    self._initialized_plugins.add(plugin_id)
                    logger.info(f"Initialized plugin: {plugin.metadata.name}")
                else:
                    logger.warning(f"Plugin initialization failed: {plugin.metadata.name}")
            except Exception as e:
                logger.error(f"Error initializing plugin {plugin.metadata.name}: {e}")

    async def shutdown_plugins(self):
        """
        Shutdown all initialized plugins.
        """
        logger.info("Shutting down plugins...")

        for plugin_id in list(self._initialized_plugins):
            plugin = self.plugins.get(plugin_id)
            if plugin:
                try:
                    await plugin.shutdown()
                    logger.info(f"Shut down plugin: {plugin.metadata.name}")
                except Exception as e:
                    logger.error(f"Error shutting down plugin {plugin.metadata.name}: {e}")

            self._initialized_plugins.discard(plugin_id)

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """
        Get a plugin by ID.

        Args:
            plugin_id: Plugin ID

        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_id)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """
        Get all plugins of a specific type.

        Args:
            plugin_type: The plugin type to filter by

        Returns:
            List of plugins matching the type
        """
        return [
            plugin for plugin in self.plugins.values()
            if plugin.metadata.plugin_type == plugin_type
        ]

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all registered plugins with their metadata.

        Returns:
            List of plugin metadata dictionaries
        """
        return [
            {
                **plugin.metadata.to_dict(),
                "initialized": plugin.metadata.id in self._initialized_plugins
            }
            for plugin in self.plugins.values()
        ]

    async def execute_plugin(
        self,
        plugin_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a plugin by ID.

        Args:
            plugin_id: Plugin ID
            **kwargs: Arguments to pass to the plugin

        Returns:
            Plugin execution results
        """
        plugin = self.get_plugin(plugin_id)

        if plugin is None:
            return {
                "success": False,
                "error": f"Plugin not found: {plugin_id}"
            }

        if not plugin.metadata.enabled:
            return {
                "success": False,
                "error": f"Plugin is disabled: {plugin_id}"
            }

        if plugin.metadata.id not in self._initialized_plugins:
            # Try to initialize it
            try:
                success = await plugin.initialize()
                if success:
                    self._initialized_plugins.add(plugin.metadata.id)
                else:
                    return {
                        "success": False,
                        "error": f"Plugin initialization failed: {plugin_id}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Plugin initialization error: {str(e)}"
                }

        try:
            result = await plugin.execute(**kwargs)
            return {
                "success": True,
                "plugin_id": plugin_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing plugin {plugin_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin and initialize it.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False

        plugin.metadata.enabled = True

        if plugin_id not in self._initialized_plugins:
            try:
                success = await plugin.initialize()
                if success:
                    self._initialized_plugins.add(plugin_id)
                    logger.info(f"Enabled plugin: {plugin.metadata.name}")
                    return True
            except Exception as e:
                logger.error(f"Error enabling plugin {plugin_id}: {e}")
                return False

        return True

    async def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin and shut it down.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful
        """
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False

        plugin.metadata.enabled = False

        if plugin_id in self._initialized_plugins:
            try:
                await plugin.shutdown()
                self._initialized_plugins.discard(plugin_id)
                logger.info(f"Disabled plugin: {plugin.metadata.name}")
            except Exception as e:
                logger.error(f"Error disabling plugin {plugin_id}: {e}")
                return False

        return True

    async def reload_plugin(self, plugin_id: str) -> bool:
        """
        Reload a plugin from disk.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if successful
        """
        # Shutdown the old plugin
        if plugin_id in self._initialized_plugins:
            plugin = self.get_plugin(plugin_id)
            if plugin:
                await plugin.shutdown()
                self._initialized_plugins.discard(plugin_id)

        # Reload
        new_plugin = self.loader.reload_plugin(plugin_id, list(self.plugins.values()))

        if new_plugin:
            self.plugins[plugin_id] = new_plugin

            # Initialize if it was enabled
            if new_plugin.metadata.enabled:
                success = await new_plugin.initialize()
                if success:
                    self._initialized_plugins.add(plugin_id)

            logger.info(f"Reloaded plugin: {plugin_id}")
            return True

        return False

    def get_plugin_schema(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the parameter schema for a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            JSON schema or None
        """
        plugin = self.get_plugin(plugin_id)
        if plugin:
            return plugin.get_schema()
        return None
