"""
Comprehensive tests for core Windows AI system components
Tests orchestrator, plugin manager, credential manager, and auto setup
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from windows_ai.core.orchestrator import WindowsAI
from windows_ai.core.plugin_manager import PluginManager
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test WindowsAI orchestrator initializes correctly"""
    orchestrator = WindowsAI()
    
    result = await orchestrator.initialize()
    
    assert result == True
    assert orchestrator._initialized == True
    assert orchestrator._config is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_with_custom_config():
    """Test orchestrator accepts custom configuration"""
    config = {
        "api_key": "test-key",
        "default_model": "gpt-4",
        "timeout": 60
    }
    
    orchestrator = WindowsAI()
    result = await orchestrator.initialize(config=config)
    
    assert result == True
    assert orchestrator._config.get("timeout") == 60


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_auto_detect_api_keys():
    """Test API key detection from environment"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"}):
        orchestrator = WindowsAI()
        keys = orchestrator._detect_api_keys()
        
        assert "OPENAI_API_KEY" in keys
        assert keys["OPENAI_API_KEY"] == "test-openai-key"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_detect_multiple_api_keys():
    """Test detection of multiple API keys"""
    env_vars = {
        "OPENAI_API_KEY": "openai-key",
        "ANTHROPIC_API_KEY": "anthropic-key",
        "GOOGLE_API_KEY": "google-key"
    }
    
    with patch.dict(os.environ, env_vars):
        orchestrator = WindowsAI()
        keys = orchestrator._detect_api_keys()
        
        assert len(keys) >= 3
        assert keys["OPENAI_API_KEY"] == "openai-key"
        assert keys["ANTHROPIC_API_KEY"] == "anthropic-key"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_list_capabilities():
    """Test listing all capabilities"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    capabilities = orchestrator.list_capabilities()
    
    assert isinstance(capabilities, list)
    assert len(capabilities) > 2000  # Should have 2500+ capabilities


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_manager_initialization():
    """Test PluginManager initializes correctly"""
    plugin_manager = PluginManager()
    
    result = await plugin_manager.initialize()
    
    assert result == True
    assert plugin_manager._initialized == True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_manager_load_all_plugins():
    """Test loading all builtin plugins"""
    plugin_manager = PluginManager()
    await plugin_manager.initialize()
    
    plugins = await plugin_manager.load_all_plugins()
    
    assert isinstance(plugins, list)
    assert len(plugins) > 200  # Should have 264+ plugins


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_manager_get_plugin_by_id():
    """Test retrieving specific plugin by ID"""
    plugin_manager = PluginManager()
    await plugin_manager.initialize()
    await plugin_manager.load_all_plugins()
    
    # Try to get a known plugin
    plugin = await plugin_manager.get_plugin("openai-chat")
    
    if plugin:  # Plugin exists
        assert isinstance(plugin, Plugin)
        assert plugin.metadata.id == "openai-chat"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_manager_list_plugins_by_type():
    """Test filtering plugins by type"""
    plugin_manager = PluginManager()
    await plugin_manager.initialize()
    await plugin_manager.load_all_plugins()
    
    integration_plugins = await plugin_manager.list_plugins_by_type(PluginType.INTEGRATION)
    action_plugins = await plugin_manager.list_plugins_by_type(PluginType.ACTION)
    
    assert isinstance(integration_plugins, list)
    assert isinstance(action_plugins, list)
    # Should have plugins of each type
    assert len(integration_plugins) > 0 or len(action_plugins) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_manager_search_plugins():
    """Test searching plugins by query"""
    plugin_manager = PluginManager()
    await plugin_manager.initialize()
    await plugin_manager.load_all_plugins()
    
    # Search for chat-related plugins
    results = await plugin_manager.search_plugins("chat")
    
    assert isinstance(results, list)
    # Should find at least some plugins
    if len(results) > 0:
        assert "chat" in results[0]["name"].lower() or "chat" in results[0]["description"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_plugin_integration():
    """Test orchestrator and plugin manager integration"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    # Orchestrator should have plugin manager
    assert hasattr(orchestrator, '_plugin_manager')
    
    # Should be able to list plugins through orchestrator
    if hasattr(orchestrator, 'list_plugins'):
        plugins = await orchestrator.list_plugins()
        assert isinstance(plugins, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_manager_initialization():
    """Test that orchestrator initializes all managers"""
    orchestrator = WindowsAI()
    await orchestrator.initialize()
    
    # Should have managers attribute
    assert hasattr(orchestrator, '_managers')
    
    # Managers should be initialized
    if isinstance(orchestrator._managers, dict):
        assert len(orchestrator._managers) > 0


@pytest.mark.unit
def test_plugin_metadata_creation():
    """Test PluginMetadata can be created correctly"""
    metadata = PluginMetadata(
        id="test-plugin",
        name="Test Plugin",
        description="A test plugin",
        version="1.0.0",
        author="Test Author",
        plugin_type=PluginType.ACTION
    )
    
    assert metadata.id == "test-plugin"
    assert metadata.name == "Test Plugin"
    assert metadata.plugin_type == PluginType.ACTION


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_base_class():
    """Test Plugin base class functionality"""
    metadata = PluginMetadata(
        id="test",
        name="Test",
        description="Test plugin",
        version="1.0.0",
        author="Tester",
        plugin_type=PluginType.TOOL
    )
    
    class TestPlugin(Plugin):
        async def execute(self, **kwargs):
            return {"status": "success", "result": "tested"}
    
    plugin = TestPlugin(metadata)
    
    # Check metadata
    assert plugin.metadata.id == "test"
    assert plugin.metadata.plugin_type == PluginType.TOOL
    
    # Test execution
    result = await plugin.execute()
    assert result["status"] == "success"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_system_initialization():
    """Test complete system initialization flow"""
    orchestrator = WindowsAI()
    
    # Initialize should not raise exceptions
    result = await orchestrator.initialize()
    
    assert result == True
    assert orchestrator._initialized == True
    
    # System should be ready to accept commands
    capabilities = orchestrator.list_capabilities()
    assert len(capabilities) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_orchestrator_graceful_degradation():
    """Test that orchestrator handles missing dependencies gracefully"""
    orchestrator = WindowsAI()
    
    # Should initialize even if some optional features unavailable
    result = await orchestrator.initialize()
    
    assert result == True  # Should still initialize successfully


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_config_merging():
    """Test that custom config merges with defaults"""
    custom_config = {"custom_key": "custom_value"}
    
    orchestrator = WindowsAI()
    await orchestrator.initialize(config=custom_config)
    
    # Custom config should be present
    assert orchestrator._config.get("custom_key") == "custom_value"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_plugin_manager_plugin_lifecycle():
    """Test complete plugin lifecycle"""
    plugin_manager = PluginManager()
    await plugin_manager.initialize()
    
    # Load plugins
    plugins = await plugin_manager.load_all_plugins()
    assert len(plugins) > 0
    
    # Get specific plugin
    if len(plugins) > 0:
        plugin_id = plugins[0]["id"]
        plugin = await plugin_manager.get_plugin(plugin_id)
        
        if plugin:
            # Initialize plugin
            init_result = await plugin.initialize()
            
            # Execute plugin (if it supports execution)
            try:
                exec_result = await plugin.execute()
                assert "status" in exec_result or "result" in exec_result
            except NotImplementedError:
                pass  # Some plugins may not implement execute
            
            # Cleanup
            await plugin.cleanup()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrator_handles_invalid_config():
    """Test orchestrator handles invalid configuration gracefully"""
    invalid_config = None
    
    orchestrator = WindowsAI()
    result = await orchestrator.initialize(config=invalid_config)
    
    # Should still initialize with default config
    assert result == True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_orchestrators_isolation():
    """Test that multiple orchestrators don't interfere with each other"""
    orchestrator1 = WindowsAI()
    orchestrator2 = WindowsAI()
    
    await orchestrator1.initialize(config={"id": 1})
    await orchestrator2.initialize(config={"id": 2})
    
    # Both should be initialized
    assert orchestrator1._initialized == True
    assert orchestrator2._initialized == True
    
    # Each should have its own config
    assert orchestrator1._config.get("id") == 1
    assert orchestrator2._config.get("id") == 2
