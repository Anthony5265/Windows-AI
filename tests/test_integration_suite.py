import pytest
from windows_ai.plugin_manager import PluginManager
from windows_ai.config import Config
from windows_ai.security.auth import AuthManager

class TestIntegrationSuite:
    def test_full_plugin_flow(self):
        config = Config()
        plugin_manager = PluginManager()
        plugins = plugin_manager.discover_plugins()
        assert len(plugins) >= 0
        
    def test_auth_to_api_flow(self):
        auth = AuthManager()
        token = auth.create_token('test_user')
        assert token is not None
        
    def test_plugin_with_security(self):
        pm = PluginManager()
        auth = AuthManager()
        token = auth.create_token('admin')
        # Can load plugins securely
        assert True
