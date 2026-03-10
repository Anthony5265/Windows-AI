"""
Comprehensive unit tests for PluginManager

Tests all plugin loading, initialization, execution and management functionality
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from windows_ai.core.plugin_manager import PluginManager, get_plugin_manager
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType


@pytest.fixture
def plugin_manager():
    """Create a fresh plugin manager instance for each test"""
    return PluginManager()


@pytest.fixture
def mock_plugin():
    """Create a mock plugin for testing"""
    metadata = PluginMetadata(
        id="test_plugin",
        name="Test Plugin",
        description="A test plugin",
        version="1.0.0",
        author="Test Author",
        plugin_type=PluginType.INTEGRATION,
        tags=["test", "mock"]
    )

    plugin = Mock(spec=Plugin)
    plugin.metadata = metadata
    plugin.initialize = AsyncMock(return_value=True)
    plugin.execute = AsyncMock(return_value={"status": "success"})
    plugin.shutdown = AsyncMock(return_value=True)
    plugin.get_supported_models = Mock(return_value=[{"id": "test_model", "name": "Test Model"}])

    return plugin


class TestPluginManagerInit:
    """Test PluginManager initialization"""

    def test_init_creates_empty_state(self, plugin_manager):
        """Test that initialization creates empty plugin collections"""
        assert isinstance(plugin_manager.plugins, dict)
        assert len(plugin_manager.plugins) == 0
        assert isinstance(plugin_manager.plugin_metadata, dict)
        assert len(plugin_manager.plugin_metadata) == 0
        assert plugin_manager.initialized is False

    def test_init_sets_start_time(self, plugin_manager):
        """Test that start_time is set on initialization"""
        assert hasattr(plugin_manager, 'start_time')
        assert plugin_manager.start_time > 0

    @pytest.mark.asyncio
    async def test_initialize_sets_initialized_flag(self, plugin_manager):
        """Test that initialize() sets the initialized flag"""
        with patch.object(plugin_manager, '_discover_builtin_plugins', new_callable=AsyncMock):
            result = await plugin_manager.initialize()
            assert result is True
            assert plugin_manager.initialized is True
            assert plugin_manager._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, plugin_manager):
        """Test that calling initialize() multiple times is safe"""
        with patch.object(plugin_manager, '_discover_builtin_plugins', new_callable=AsyncMock) as mock_discover:
            await plugin_manager.initialize()
            await plugin_manager.initialize()
            # Should only discover plugins once
            assert mock_discover.call_count == 1

    @pytest.mark.asyncio
    async def test_initialize_discovers_plugins(self, plugin_manager):
        """Test that initialize() calls plugin discovery"""
        with patch.object(plugin_manager, '_discover_builtin_plugins', new_callable=AsyncMock) as mock_discover:
            await plugin_manager.initialize()
            mock_discover.assert_called_once()


class TestPluginDiscovery:
    """Test plugin discovery functionality"""

    @pytest.mark.asyncio
    async def test_discover_builtin_plugins_handles_missing_directory(self, plugin_manager):
        """Test that discovery handles missing builtin directory gracefully"""
        with patch('pathlib.Path.exists', return_value=False):
            # Should not raise exception
            await plugin_manager._discover_builtin_plugins()
            assert len(plugin_manager.plugins) == 0

    @pytest.mark.asyncio
    async def test_discover_skips_generated_directory(self, plugin_manager):
        """Test that 'generated' directory is skipped"""
        mock_plugins_dir = Mock()
        mock_generated_dir = Mock()
        mock_generated_dir.name = 'generated'
        mock_generated_dir.is_dir.return_value = True

        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.glob.return_value = []
        mock_plugins_dir.iterdir.return_value = [mock_generated_dir]

        with patch.object(Path, '__new__', return_value=mock_plugins_dir):
            with patch.object(plugin_manager, '_load_plugin_file', new_callable=AsyncMock) as mock_load:
                await plugin_manager._discover_builtin_plugins()
                # Should not load any plugins from generated dir
                assert mock_load.call_count == 0

    @pytest.mark.asyncio
    async def test_discover_skips_small_template_files(self, plugin_manager):
        """Test that small template files (< 5KB) are skipped"""
        mock_file = Mock()
        mock_file.stat.return_value.st_size = 3000  # Less than 5KB
        mock_file.name = "template_plugin.py"

        mock_plugins_dir = Mock()
        mock_plugins_dir.exists.return_value = True
        mock_plugins_dir.glob.return_value = [mock_file]
        mock_plugins_dir.iterdir.return_value = []

        with patch('pathlib.Path.__new__', return_value=mock_plugins_dir):
            with patch.object(plugin_manager, '_load_plugin_file', new_callable=AsyncMock) as mock_load:
                await plugin_manager._discover_builtin_plugins()
                assert mock_load.call_count == 0


class TestPluginLoading:
    """Test plugin loading functionality"""

    @pytest.mark.asyncio
    async def test_load_plugin_file_success(self, plugin_manager, mock_plugin):
        """Test successful plugin file loading"""
        mock_module = Mock()
        mock_module.plugin = mock_plugin

        with patch('importlib.util.spec_from_file_location') as mock_spec_from:
            with patch('importlib.util.module_from_spec', return_value=mock_module):
                mock_spec = Mock()
                mock_spec.loader = Mock()
                mock_spec.loader.exec_module = Mock()
                mock_spec_from.return_value = mock_spec

                plugin_path = Path("test_plugin.py")
                await plugin_manager._load_plugin_file(plugin_path, "test_category")

                assert "test_plugin" in plugin_manager.plugins
                assert plugin_manager.plugins["test_plugin"] == mock_plugin
                mock_plugin.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_plugin_file_handles_missing_plugin_attr(self, plugin_manager):
        """Test that files without 'plugin' attribute are skipped"""
        mock_module = Mock(spec=[])  # No 'plugin' attribute

        with patch('importlib.util.spec_from_file_location') as mock_spec_from:
            with patch('importlib.util.module_from_spec', return_value=mock_module):
                mock_spec = Mock()
                mock_spec.loader = Mock()
                mock_spec.loader.exec_module = Mock()
                mock_spec_from.return_value = mock_spec

                plugin_path = Path("invalid_plugin.py")
                await plugin_manager._load_plugin_file(plugin_path, "test_category")

                assert len(plugin_manager.plugins) == 0

    @pytest.mark.asyncio
    async def test_load_plugin_from_path(self, plugin_manager, mock_plugin):
        """Test loading plugin from file path"""
        mock_module = Mock()
        mock_module.plugin = mock_plugin

        with patch('pathlib.Path.exists', return_value=True):
            with patch('importlib.util.spec_from_file_location') as mock_spec_from:
                with patch('importlib.util.module_from_spec', return_value=mock_module):
                    mock_spec = Mock()
                    mock_spec.loader = Mock()
                    mock_spec.loader.exec_module = Mock()
                    mock_spec_from.return_value = mock_spec

                    result = await plugin_manager.load_plugin("test_plugin.py")
                    assert result == mock_plugin

    @pytest.mark.asyncio
    async def test_load_plugin_file_not_found(self, plugin_manager):
        """Test that loading non-existent file raises FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            await plugin_manager.load_plugin("nonexistent.py")

    @pytest.mark.asyncio
    async def test_load_plugin_invalid_extension(self, plugin_manager):
        """Test that loading non-.py file raises ValueError"""
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ValueError, match="must be Python file"):
                await plugin_manager.load_plugin("test.txt")


class TestPluginExecution:
    """Test plugin execution functionality"""

    @pytest.mark.asyncio
    async def test_execute_plugin_success(self, plugin_manager, mock_plugin):
        """Test successful plugin execution"""
        plugin_manager.plugins["test_plugin"] = mock_plugin

        result = await plugin_manager.execute_plugin(
            "test_plugin",
            "test_action",
            {"param": "value"}
        )

        assert result == {"status": "success"}
        mock_plugin.execute.assert_called_once_with("test_action", {"param": "value"})

    @pytest.mark.asyncio
    async def test_execute_plugin_not_found(self, plugin_manager):
        """Test that executing non-existent plugin raises ValueError"""
        with pytest.raises(ValueError, match="not found"):
            await plugin_manager.execute_plugin(
                "nonexistent_plugin",
                "action",
                {}
            )

    @pytest.mark.asyncio
    async def test_execute_plugin_timeout(self, plugin_manager, mock_plugin):
        """Test that plugin execution respects timeout"""
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(10)
            return {"status": "success"}

        mock_plugin.execute = slow_execute
        plugin_manager.plugins["test_plugin"] = mock_plugin

        with pytest.raises(TimeoutError, match="timed out"):
            await plugin_manager.execute_plugin(
                "test_plugin",
                "slow_action",
                {},
                timeout=0.1
            )

    @pytest.mark.asyncio
    async def test_execute_plugin_error_handling(self, plugin_manager, mock_plugin):
        """Test that plugin execution errors are properly wrapped"""
        mock_plugin.execute = AsyncMock(side_effect=RuntimeError("Plugin error"))
        plugin_manager.plugins["test_plugin"] = mock_plugin

        with pytest.raises(Exception, match="Plugin execution failed"):
            await plugin_manager.execute_plugin(
                "test_plugin",
                "failing_action",
                {}
            )


class TestPluginRetrieval:
    """Test plugin retrieval methods"""

    def test_get_plugin_exists(self, plugin_manager, mock_plugin):
        """Test getting an existing plugin"""
        plugin_manager.plugins["test_plugin"] = mock_plugin
        result = plugin_manager.get_plugin("test_plugin")
        assert result == mock_plugin

    def test_get_plugin_not_exists(self, plugin_manager):
        """Test getting a non-existent plugin returns None"""
        result = plugin_manager.get_plugin("nonexistent")
        assert result is None

    def test_get_all_plugins(self, plugin_manager, mock_plugin):
        """Test getting all plugins metadata"""
        plugin_manager.plugin_metadata["test_plugin"] = mock_plugin.metadata

        result = plugin_manager.get_all_plugins()
        assert len(result) == 1
        assert result[0]['id'] == "test_plugin"
        assert result[0]['name'] == "Test Plugin"

    def test_get_plugins_by_category(self, plugin_manager, mock_plugin):
        """Test filtering plugins by category/tag"""
        plugin_manager.plugins["test_plugin"] = mock_plugin

        result = plugin_manager.get_plugins_by_category("test")
        assert len(result) == 1
        assert result[0] == mock_plugin

        result = plugin_manager.get_plugins_by_category("nonexistent")
        assert len(result) == 0

    def test_get_plugins_by_type(self, plugin_manager, mock_plugin):
        """Test filtering plugins by type"""
        plugin_manager.plugins["test_plugin"] = mock_plugin

        result = plugin_manager.get_plugins_by_type("integration")
        assert len(result) == 1
        assert result[0] == mock_plugin

    def test_get_all_supported_models(self, plugin_manager, mock_plugin):
        """Test getting all models from all plugins"""
        plugin_manager.plugins["test_plugin"] = mock_plugin

        result = plugin_manager.get_all_supported_models()
        assert len(result) == 1
        assert result[0]['id'] == "test_model"


class TestPluginShutdown:
    """Test plugin shutdown functionality"""

    @pytest.mark.asyncio
    async def test_shutdown_all_plugins(self, plugin_manager, mock_plugin):
        """Test shutting down all plugins"""
        plugin_manager.plugins["test_plugin"] = mock_plugin
        plugin_manager.plugin_metadata["test_plugin"] = mock_plugin.metadata
        plugin_manager.initialized = True

        await plugin_manager.shutdown()

        mock_plugin.shutdown.assert_called_once()
        assert len(plugin_manager.plugins) == 0
        assert len(plugin_manager.plugin_metadata) == 0
        assert plugin_manager.initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_handles_errors(self, plugin_manager, mock_plugin):
        """Test that shutdown handles individual plugin errors gracefully"""
        mock_plugin.shutdown = AsyncMock(side_effect=RuntimeError("Shutdown error"))
        plugin_manager.plugins["test_plugin"] = mock_plugin

        # Should not raise exception
        await plugin_manager.shutdown()
        assert len(plugin_manager.plugins) == 0


class TestPluginStats:
    """Test plugin statistics and monitoring"""

    def test_get_stats(self, plugin_manager, mock_plugin):
        """Test getting plugin manager statistics"""
        plugin_manager.plugins["test_plugin"] = mock_plugin
        plugin_manager.plugin_metadata["test_plugin"] = mock_plugin.metadata

        stats = plugin_manager.get_stats()

        assert stats['total_plugins'] == 1
        assert 'test' in stats['categories']
        assert stats['categories']['test'] == 1
        assert 'integration' in stats['plugin_types']
        assert stats['plugin_types']['integration'] == 1
        assert 'uptime' in stats
        assert stats['uptime'] >= 0


class TestPluginManagerSingleton:
    """Test singleton pattern for plugin manager"""

    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns the same instance"""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        assert manager1 is manager2


class TestDynamicPluginLoading:
    """Test loading plugins from code"""

    @pytest.mark.asyncio
    async def test_load_plugin_from_code(self, plugin_manager, mock_plugin):
        """Test loading a plugin from Python code string"""
        code = '''
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType

metadata = PluginMetadata(
    id="dynamic_plugin",
    name="Dynamic Plugin",
    description="Loaded from code",
    version="1.0.0",
    author="Test",
    plugin_type=PluginType.UTILITY,
    tags=["dynamic"]
)

class DynamicPlugin(Plugin):
    def __init__(self):
        super().__init__(metadata)

    async def execute(self, action, params):
        return {"status": "success"}

plugin = DynamicPlugin()
'''
        mock_module = Mock()
        mock_module.plugin = mock_plugin

        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = Mock()
            mock_file.name = "temp_plugin.py"
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_temp.return_value = mock_file

            with patch('pathlib.Path.exists', return_value=True):
                with patch('os.remove'):
                    with patch('importlib.util.spec_from_file_location') as mock_spec_from:
                        with patch('importlib.util.module_from_spec', return_value=mock_module):
                            mock_spec = Mock()
                            mock_spec.loader = Mock()
                            mock_spec.loader.exec_module = Mock()
                            mock_spec_from.return_value = mock_spec

                            result = await plugin_manager.load_plugin_from_code(code)
                            assert result == mock_plugin

    @pytest.mark.asyncio
    async def test_load_plugin_from_code_security_check(self, plugin_manager):
        """Test that dangerous imports are blocked in dynamic plugins"""
        dangerous_code = '''
import os
import sys

# Malicious code
os.system("rm -rf /")
'''
        with pytest.raises(ValueError, match="security violation"):
            await plugin_manager.load_plugin_from_code(dangerous_code)


class TestListPlugins:
    """Test listing plugins with filters"""

    @pytest.mark.asyncio
    async def test_list_plugins_no_filter(self, plugin_manager, mock_plugin):
        """Test listing all plugins without filter"""
        plugin_manager.plugin_metadata["test_plugin"] = mock_plugin.metadata

        result = await plugin_manager.list_plugins()
        assert len(result) == 1
        assert result[0]['id'] == "test_plugin"

    @pytest.mark.asyncio
    async def test_list_plugins_with_category_filter(self, plugin_manager, mock_plugin):
        """Test listing plugins filtered by category"""
        plugin_manager.plugins["test_plugin"] = mock_plugin

        # Mock the metadata.to_dict() method
        with patch.object(mock_plugin.metadata, 'to_dict', return_value={'id': 'test_plugin'}):
            result = await plugin_manager.list_plugins(category="test")
            assert len(result) == 1
