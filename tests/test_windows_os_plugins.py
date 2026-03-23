"""
Unit tests for all 31 windows_os plugins.

Tests that each plugin:
1. Can be imported and instantiated
2. Has correct metadata (id, name, plugin_type)
3. Has required methods (initialize, execute, connect, disconnect, shutdown, get_schema)
4. Initializes successfully
5. Returns proper execute response format
"""
import pytest
import asyncio
import importlib
from pathlib import Path
from typing import Dict, Any


# Discover all windows_os plugin modules
PLUGINS_DIR = Path(__file__).parent.parent / "windows_ai" / "plugins" / "builtin" / "windows_os"
PLUGIN_FILES = sorted([
    f.stem for f in PLUGINS_DIR.glob("*.py")
    if not f.name.startswith("_")
])


def _import_plugin_class(module_name: str):
    """Import the plugin class from a windows_os plugin module."""
    full_module = f"windows_ai.plugins.builtin.windows_os.{module_name}"
    mod = importlib.import_module(full_module)

    # Find the Plugin class
    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if (
            isinstance(obj, type)
            and attr_name.endswith("Plugin")
            and attr_name != "IntegrationPlugin"
            and hasattr(obj, "metadata")
        ):
            return obj
    
    # Fallback: look for module-level 'plugin' attribute
    if hasattr(mod, "plugin"):
        return type(mod.plugin)
    
    raise ImportError(f"No plugin class found in {full_module}")


class TestWindowsOSPluginImports:
    """Test that all windows_os plugins can be imported."""

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_import(self, plugin_name):
        """Plugin module can be imported without errors."""
        full_module = f"windows_ai.plugins.builtin.windows_os.{plugin_name}"
        mod = importlib.import_module(full_module)
        assert mod is not None


class TestWindowsOSPluginMetadata:
    """Test plugin metadata is correctly defined."""

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_metadata(self, plugin_name):
        """Plugin has valid PluginMetadata."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "metadata")
        assert instance.metadata.id is not None
        assert instance.metadata.name is not None
        assert instance.metadata.description is not None
        assert instance.metadata.version is not None
        assert instance.metadata.author is not None

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_plugin_type(self, plugin_name):
        """Plugin has INTEGRATION type."""
        from windows_ai.plugins.base import PluginType
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert instance.metadata.plugin_type == PluginType.INTEGRATION

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_tags(self, plugin_name):
        """Plugin has tags."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert isinstance(instance.metadata.tags, list)
        assert len(instance.metadata.tags) > 0


class TestWindowsOSPluginMethods:
    """Test that all required methods exist."""

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_initialize(self, plugin_name):
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "initialize")
        assert asyncio.iscoroutinefunction(instance.initialize)

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_execute(self, plugin_name):
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "execute")
        assert asyncio.iscoroutinefunction(instance.execute)

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_connect(self, plugin_name):
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "connect")
        assert asyncio.iscoroutinefunction(instance.connect)

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_disconnect(self, plugin_name):
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "disconnect")
        assert asyncio.iscoroutinefunction(instance.disconnect)

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_shutdown(self, plugin_name):
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "shutdown")

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_has_get_schema(self, plugin_name):
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        assert hasattr(instance, "get_schema")
        schema = instance.get_schema()
        assert isinstance(schema, dict)


class TestWindowsOSPluginInitialization:
    """Test plugin initialization."""

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    @pytest.mark.asyncio
    async def test_initialize(self, plugin_name):
        """Plugin initializes without error."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        result = await instance.initialize()
        assert result is True
        assert instance._initialized is True

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, plugin_name):
        """Plugin connect/disconnect cycle works."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        await instance.initialize()
        
        # Connect (may return False if external dep not available, e.g., ADB)
        result = await instance.connect({"api_key": "test"})
        assert isinstance(result, bool)
        
        # Disconnect
        result = await instance.disconnect()
        assert isinstance(result, bool)


class TestWindowsOSPluginExecution:
    """Test plugin execution returns proper format."""

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    @pytest.mark.asyncio
    async def test_execute_status(self, plugin_name):
        """Execute 'status' action returns dict with status key."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        await instance.initialize()
        
        result = await instance.execute(
            action="status",
            parameters={},
        )
        assert isinstance(result, dict)
        assert "status" in result or "success" in result

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, plugin_name):
        """Execute unknown action returns error."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        await instance.initialize()
        
        result = await instance.execute(
            action="nonexistent_action_xyz",
            parameters={},
        )
        assert isinstance(result, dict)
        # Should indicate error
        status = result.get("status", result.get("success", None))
        assert status in ["error", False, "unknown_action"] or "error" in str(result).lower()


class TestWindowsOSPluginSchemas:
    """Test that plugin schemas are properly formed."""

    @pytest.mark.parametrize("plugin_name", PLUGIN_FILES)
    def test_schema_structure(self, plugin_name):
        """Plugin schema has expected structure."""
        cls = _import_plugin_class(plugin_name)
        instance = cls()
        schema = instance.get_schema()
        assert isinstance(schema, dict)
        # Should have at least some keys
        assert len(schema) > 0
