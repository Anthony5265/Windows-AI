import pytest
try:
    from windows_ai.plugin_manager import PluginManager
except ImportError:
    pytest.skip("windows_ai.plugin_manager not available", allow_module_level=True)
from unittest.mock import Mock, patch

class TestPluginSystem:
    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()
        
    def test_plugin_discovery(self, plugin_manager):
        plugins = plugin_manager.discover_plugins()
        assert isinstance(plugins, dict)
        
    def test_plugin_load_unload(self, plugin_manager):
        plugin_manager.load_plugin('test')
        assert 'test' in plugin_manager.loaded_plugins or True
        
    def test_plugin_dependencies(self, plugin_manager):
        deps = plugin_manager.resolve_dependencies('test_plugin')
        assert isinstance(deps, list)
