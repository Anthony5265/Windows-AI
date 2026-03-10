import pytest
import time
from windows_ai.plugin_manager import PluginManager
from windows_ai.config import Config

class TestPerformance:
    def test_plugin_discovery_speed(self):
        pm = PluginManager()
        start = time.time()
        plugins = pm.discover_plugins()
        elapsed = time.time() - start
        assert elapsed < 5.0  # Should complete within 5 seconds
        
    def test_config_load_speed(self):
        start = time.time()
        config = Config()
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should load within 1 second
        
    def test_api_response_time(self):
        from windows_ai.api.server import app
        with app.test_client() as client:
            start = time.time()
            response = client.get('/api/health')
            elapsed = time.time() - start
            assert elapsed < 0.5  # Response within 500ms
