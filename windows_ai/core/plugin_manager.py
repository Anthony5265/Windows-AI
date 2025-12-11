"""Plugin Manager for Windows AI

Manages loading, initialization, and execution of all plugins.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import time
import asyncio

from windows_ai.plugins.base import Plugin, IntegrationPlugin, PluginMetadata

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages all plugins in the Windows AI system"""

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.initialized = False
        self.start_time = time.time()

    async def initialize(self):
        """Initialize the plugin manager and load all plugins
        
        Returns:
            True if initialization successful
        """
        if self.initialized:
            logger.warning("Plugin manager already initialized")
            return True

        logger.info("Initializing plugin manager...")

        # Discover and load all builtin plugins
        await self._discover_builtin_plugins()

        self.initialized = True
        self._initialized = True  # Alias for compatibility
        logger.info(f"Plugin manager initialized with {len(self.plugins)} plugins")
        return True

    async def _discover_builtin_plugins(self):
        """Discover and load all builtin plugins"""
        plugins_dir = Path(__file__).parent.parent / "plugins" / "builtin"

        if not plugins_dir.exists():
            logger.warning(f"Builtin plugins directory not found: {plugins_dir}")
            return

        logger.info(f"Discovering plugins in {plugins_dir}")

        # First, scan plugins directly in builtin/ directory
        logger.debug("Scanning root builtin directory for plugins")
        for plugin_file in plugins_dir.glob("*_plugin.py"):
            # Skip template plugins (files under 5KB are likely templates)
            if plugin_file.stat().st_size < 5000:
                logger.debug(f"Skipping template plugin: {plugin_file.name} ({plugin_file.stat().st_size} bytes)")
                continue
            
            try:
                await self._load_plugin_file(plugin_file, "general")
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file.name}: {e}")

        # Then, scan all subdirectories (categories)
        for category_dir in plugins_dir.iterdir():
            if not category_dir.is_dir():
                continue

            if category_dir.name.startswith('_'):
                continue
            
            # Skip 'generated' directory - contains AI-generated low-quality plugins
            if category_dir.name == 'generated':
                logger.debug("Skipping 'generated' directory (contains AI-generated plugins)")
                continue

            logger.debug(f"Scanning category: {category_dir.name}")

            # Load all plugins in this category
            for plugin_file in category_dir.glob("*_plugin.py"):
                # Skip template plugins (files under 5KB are likely templates)
                if plugin_file.stat().st_size < 5000:
                    logger.debug(f"Skipping template plugin: {plugin_file.name} ({plugin_file.stat().st_size} bytes)")
                    continue
                
                try:
                    await self._load_plugin_file(plugin_file, category_dir.name)
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_file.name}: {e}")

    async def _load_plugin_file(self, plugin_path: Path, category: str):
        """Load a single plugin file"""
        plugin_name = plugin_path.stem  # Remove .py extension

        try:
            # Build module path
            # e.g., windows_ai.plugins.builtin.code_models.github_copilot_plugin
            module_name = f"windows_ai.plugins.builtin.{category}.{plugin_name}"

            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Get the plugin instance
                if hasattr(module, 'plugin'):
                    plugin = module.plugin
                    if isinstance(plugin, Plugin):
                        # Initialize the plugin
                        try:
                            await plugin.initialize()
                            plugin_id = plugin.metadata.id
                            self.plugins[plugin_id] = plugin
                            self.plugin_metadata[plugin_id] = plugin.metadata
                            logger.debug(f"Loaded plugin: {plugin_id}")
                        except Exception as e:
                            logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
                    else:
                        logger.warning(f"Plugin {plugin_name} 'plugin' object is not a Plugin")
                else:
                    logger.warning(f"Plugin {plugin_name} has no 'plugin' attribute")

        except Exception as e:
            logger.error(f"Error loading plugin file {plugin_path}: {e}", exc_info=True)

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID"""
        return self.plugins.get(plugin_id)

    def get_all_plugins(self) -> List[Dict[str, Any]]:
        """Get information about all plugins"""
        return [
            {
                'id': metadata.id,
                'name': metadata.name,
                'description': metadata.description,
                'version': metadata.version,
                'author': metadata.author,
                'plugin_type': metadata.plugin_type.value,
                'tags': metadata.tags
            }
            for metadata in self.plugin_metadata.values()
        ]

    def get_plugins_by_category(self, category: str) -> List[Plugin]:
        """Get all plugins in a category"""
        return [
            plugin for plugin in self.plugins.values()
            if category.lower() in [tag.lower() for tag in plugin.metadata.tags]
        ]

    def get_plugins_by_type(self, plugin_type: str) -> List[Plugin]:
        """Get all plugins of a specific type"""
        return [
            plugin for plugin in self.plugins.values()
            if plugin.metadata.plugin_type.value == plugin_type
        ]

    def get_all_supported_models(self) -> List[Dict[str, Any]]:
        """Get all supported models from all loaded plugins"""
        models = []
        for plugin in self.plugins.values():
            try:
                plugin_models = plugin.get_supported_models()
                if plugin_models:
                    models.extend(plugin_models)
            except Exception as e:
                logger.warning(f"Error getting models from plugin {plugin.metadata.id}: {e}")
        return models

    async def execute_plugin(
        self,
        plugin_id: str,
        action: str,
        params: Dict[str, Any],
        timeout: Optional[int] = 30
    ) -> Dict[str, Any]:
        """Execute a plugin action with timeout"""
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        try:
            result = await asyncio.wait_for(
                plugin.execute(action, params),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Plugin execution timed out after {timeout} seconds")
        except Exception as e:
            raise Exception(f"Plugin execution failed: {str(e)}")

    async def shutdown(self):
        """Shutdown all plugins"""
        logger.info("Shutting down plugin manager...")

        for plugin_id, plugin in self.plugins.items():
            try:
                await plugin.shutdown()
                logger.debug(f"Shutdown plugin: {plugin_id}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_id}: {e}")

        self.plugins.clear()
        self.plugin_metadata.clear()
        self.initialized = False

        logger.info("Plugin manager shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin manager statistics"""
        categories = {}
        plugin_types = {}

        for metadata in self.plugin_metadata.values():
            for tag in metadata.tags:
                categories[tag] = categories.get(tag, 0) + 1
            pt = metadata.plugin_type.value
            plugin_types[pt] = plugin_types.get(pt, 0) + 1

        return {
            'total_plugins': len(self.plugins),
            'categories': categories,
            'plugin_types': plugin_types,
            'uptime': time.time() - self.start_time
        }
    
    async def list_plugins(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all plugins, optionally filtered by category
        
        Args:
            category: Optional category filter
        
        Returns:
            List of plugin metadata dictionaries
        """
        if category:
            plugins = self.get_plugins_by_category(category)
            return [p.metadata.to_dict() for p in plugins]
        else:
            return self.get_all_plugins()


# Global singleton instance
_plugin_manager_instance = None

def get_plugin_manager() -> PluginManager:
    """Get global plugin manager instance"""
    global _plugin_manager_instance
    if _plugin_manager_instance is None:
        _plugin_manager_instance = PluginManager()
    return _plugin_manager_instance
