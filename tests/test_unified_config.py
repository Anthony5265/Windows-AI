"""
Tests for Unified Configuration System

Tests configuration loading, validation, environment variables,
and nested access patterns.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from windows_ai.config import (
    WindowsAIConfig,
    get_config,
    reload_config,
    save_config,
    validate_config,
    LLMProviderConfig,
    ServerConfig,
    PluginConfig,
)


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "app_name": "Test App",
            "server": {
                "host": "127.0.0.1",
                "port": 9999
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.5
            }
        }
        json.dump(config_data, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def clean_config():
    """Reset global config before each test"""
    import windows_ai.config.unified_config as config_module
    config_module._config = None
    yield
    config_module._config = None


class TestConfigurationLoading:
    """Test configuration loading from various sources"""
    
    def test_default_configuration(self, clean_config):
        """Test loading default configuration"""
        config = WindowsAIConfig()
        
        assert config.app_name == "Windows AI"
        assert config.version == "2.0.0-alpha"
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 8765
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-3.5-turbo"
    
    def test_load_from_file(self, temp_config_file, clean_config):
        """Test loading configuration from file"""
        config = WindowsAIConfig.from_file(temp_config_file)
        
        assert config.app_name == "Test App"
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 9999
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4"
        assert config.llm.temperature == 0.5
    
    def test_save_to_file(self, clean_config):
        """Test saving configuration to file"""
        config = WindowsAIConfig()
        config.server.port = 7000
        config.llm.model = "gpt-4-turbo"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            config.to_file(temp_path)
            
            # Load and verify
            loaded_config = WindowsAIConfig.from_file(temp_path)
            assert loaded_config.server.port == 7000
            assert loaded_config.llm.model == "gpt-4-turbo"
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_environment_variable_override(self, clean_config, monkeypatch):
        """Test environment variable configuration"""
        monkeypatch.setenv("WINDOWSAI_SERVER__PORT", "9000")
        monkeypatch.setenv("WINDOWSAI_LLM__MODEL", "claude-3-opus")
        monkeypatch.setenv("WINDOWSAI_LLM__TEMPERATURE", "0.9")
        
        config = WindowsAIConfig()
        
        assert config.server.port == 9000
        assert config.llm.model == "claude-3-opus"
        assert config.llm.temperature == 0.9


class TestNestedAccess:
    """Test nested configuration access"""
    
    def test_dot_notation_access(self, clean_config):
        """Test accessing nested values with dot notation"""
        config = WindowsAIConfig()
        
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 8765
        assert config.llm.provider == "openai"
        assert config.plugins.auto_discover is True
    
    def test_get_nested_method(self, clean_config):
        """Test get_nested() method"""
        config = WindowsAIConfig()
        
        assert config.get_nested('server.port') == 8765
        assert config.get_nested('llm.provider') == 'openai'
        assert config.get_nested('server.cors_origins') == ["http://localhost:*"]
    
    def test_get_nested_with_default(self, clean_config):
        """Test get_nested() with default value"""
        config = WindowsAIConfig()
        
        assert config.get_nested('nonexistent.key', default=42) == 42
        assert config.get_nested('server.nonexistent', default='fallback') == 'fallback'
    
    def test_set_nested_method(self, clean_config):
        """Test set_nested() method"""
        config = WindowsAIConfig()
        
        config.set_nested('server.port', 9500)
        assert config.server.port == 9500
        
        config.set_nested('llm.temperature', 0.8)
        assert config.llm.temperature == 0.8


class TestValidation:
    """Test configuration validation"""
    
    def test_valid_configuration(self, clean_config):
        """Test validation of valid configuration"""
        config = WindowsAIConfig()
        config.llm.provider = "openai"
        config.llm.api_key = "sk-test-key"
        
        # Reset global config for validation
        import windows_ai.config.unified_config as config_module
        config_module._config = config
        
        errors = validate_config()
        assert len(errors) == 0
    
    def test_missing_api_key(self, clean_config):
        """Test validation catches missing API key"""
        config = WindowsAIConfig()
        config.llm.provider = "openai"
        config.llm.api_key = None
        
        import windows_ai.config.unified_config as config_module
        config_module._config = config
        
        errors = validate_config()
        assert 'llm' in errors
        assert any('API key required' in err for err in errors['llm'])
    
    def test_invalid_log_level(self, clean_config):
        """Test validation of log level"""
        with pytest.raises(ValueError, match="Invalid log level"):
            config = WindowsAIConfig()
            config.logging.level = "INVALID"
    
    def test_temperature_range_validation(self, clean_config):
        """Test temperature must be within valid range"""
        with pytest.raises(ValueError):
            LLMProviderConfig(provider="openai", model="gpt-4", temperature=3.0)
        
        with pytest.raises(ValueError):
            LLMProviderConfig(provider="openai", model="gpt-4", temperature=-0.1)
    
    def test_positive_integers(self, clean_config):
        """Test positive integer constraints"""
        with pytest.raises(ValueError):
            ServerConfig(port=-1)
        
        with pytest.raises(ValueError):
            LLMProviderConfig(provider="openai", model="gpt-4", max_tokens=0)


class TestGlobalConfiguration:
    """Test global configuration instance management"""
    
    def test_get_config_singleton(self, clean_config):
        """Test get_config() returns singleton"""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_reload_config(self, temp_config_file, clean_config):
        """Test reload_config() reloads from file"""
        # First load with default
        config1 = get_config()
        assert config1.app_name == "Windows AI"
        
        # Reload from file
        config2 = reload_config(temp_config_file)
        assert config2.app_name == "Test App"
        assert config2.server.port == 9999
    
    def test_save_and_reload(self, clean_config):
        """Test save and reload cycle"""
        config = get_config()
        config.server.port = 8888
        config.llm.model = "test-model"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Save
            config.to_file(temp_path)
            
            # Reload
            reloaded = reload_config(temp_path)
            
            assert reloaded.server.port == 8888
            assert reloaded.llm.model == "test-model"
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestComponentConfigurations:
    """Test individual component configurations"""
    
    def test_server_config(self, clean_config):
        """Test ServerConfig"""
        server = ServerConfig(
            host="0.0.0.0",
            port=8080,
            cors_origins=["https://example.com"]
        )
        
        assert server.host == "0.0.0.0"
        assert server.port == 8080
        assert "https://example.com" in server.cors_origins
    
    def test_llm_provider_config(self, clean_config):
        """Test LLMProviderConfig"""
        llm = LLMProviderConfig(
            provider="anthropic",
            model="claude-3-opus",
            api_key="sk-test",
            temperature=0.7,
            max_tokens=4000
        )
        
        assert llm.provider == "anthropic"
        assert llm.model == "claude-3-opus"
        assert llm.api_key == "sk-test"
        assert llm.temperature == 0.7
        assert llm.max_tokens == 4000
    
    def test_plugin_config(self, clean_config):
        """Test PluginConfig"""
        plugins = PluginConfig(
            plugins_dir=Path("custom/plugins"),
            auto_discover=False,
            enabled_plugins=["plugin1", "plugin2"],
            sandbox_enabled=True
        )
        
        assert plugins.plugins_dir == Path("custom/plugins")
        assert plugins.auto_discover is False
        assert "plugin1" in plugins.enabled_plugins
        assert plugins.sandbox_enabled is True


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_nonexistent_config_file(self, clean_config):
        """Test loading from nonexistent file returns defaults"""
        config = WindowsAIConfig.from_file("nonexistent.json")
        
        assert config.app_name == "Windows AI"
        assert config.server.port == 8765
    
    def test_invalid_json_file(self, clean_config):
        """Test loading from invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                WindowsAIConfig.from_file(temp_path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_partial_configuration(self, clean_config):
        """Test partial configuration fills in defaults"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"server": {"port": 9000}}, f)
            temp_path = Path(f.name)
        
        try:
            config = WindowsAIConfig.from_file(temp_path)
            
            # Specified value
            assert config.server.port == 9000
            
            # Default values
            assert config.server.host == "127.0.0.1"
            assert config.llm.provider == "openai"
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_custom_settings_dict(self, clean_config):
        """Test custom settings dictionary"""
        config = WindowsAIConfig()
        config.custom["my_setting"] = "value"
        config.custom["nested"] = {"key": "value"}
        
        assert config.custom["my_setting"] == "value"
        assert config.custom["nested"]["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
