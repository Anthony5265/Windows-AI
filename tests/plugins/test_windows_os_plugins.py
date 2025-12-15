"""
Comprehensive tests for Windows OS plugins
Tests all 30 comprehensive Windows OS plugins
"""
import pytest
import asyncio
from windows_ai.plugins.builtin.windows_os import (
    winrm_integration_plugin,
    windows_store_api_plugin,
    windows_performance_recorder_plugin,
    windows_subsystem_android_plugin,
    windows_search_plugin,
    windows_hello_plugin,
    windows_defender_plugin,
    windows_firewall_plugin,
    bitlocker_automation_plugin,
    diagnostic_data_telemetry_plugin,
    group_policy_automation_plugin,
    event_tracing_windows_plugin,
    bits_integration_plugin,
    windows_error_reporting_plugin,
    direct3d_integration_plugin,
    installer_hooks_plugin,
    cortana_replacement_plugin,
    active_directory_plugin,
    hyper_v_integration_plugin,
    windows_container_management_plugin,
    windows_sandbox_plugin,
    rdp_automation_plugin,
    uwp_app_automation_plugin,
    volume_shadow_copy_plugin,
    appx_manifest_plugin,
    msix_packaging_plugin,
    windows_terminal_plugin,
    windows_update_plugin,
    winget_automation_plugin,
    wsl2_integration_plugin
)

# List of all Windows OS plugin modules
PLUGIN_MODULES = [
    winrm_integration_plugin,
    windows_store_api_plugin,
    windows_performance_recorder_plugin,
    windows_subsystem_android_plugin,
    windows_search_plugin,
    windows_hello_plugin,
    windows_defender_plugin,
    windows_firewall_plugin,
    bitlocker_automation_plugin,
    diagnostic_data_telemetry_plugin,
    group_policy_automation_plugin,
    event_tracing_windows_plugin,
    bits_integration_plugin,
    windows_error_reporting_plugin,
    direct3d_integration_plugin,
    installer_hooks_plugin,
    cortana_replacement_plugin,
    active_directory_plugin,
    hyper_v_integration_plugin,
    windows_container_management_plugin,
    windows_sandbox_plugin,
    rdp_automation_plugin,
    uwp_app_automation_plugin,
    volume_shadow_copy_plugin,
    appx_manifest_plugin,
    msix_packaging_plugin,
    windows_terminal_plugin,
    windows_update_plugin,
    winget_automation_plugin,
    wsl2_integration_plugin
]

@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
def test_plugin_has_plugin_instance(plugin_module):
    """Test that each plugin module exports a plugin instance"""
    assert hasattr(plugin_module, "plugin"), f"{plugin_module.__name__} missing plugin instance"

@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
def test_plugin_has_metadata(plugin_module):
    """Test that each plugin has metadata"""
    plugin = plugin_module.plugin
    assert hasattr(plugin, "metadata"), f"{plugin_module.__name__} plugin missing metadata"
    assert plugin.metadata is not None

@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
def test_plugin_metadata_fields(plugin_module):
    """Test that plugin metadata has required fields"""
    plugin = plugin_module.plugin
    metadata = plugin.metadata
    
    assert hasattr(metadata, "id"), "Metadata missing id"
    assert hasattr(metadata, "name"), "Metadata missing name"
    assert hasattr(metadata, "description"), "Metadata missing description"
    assert hasattr(metadata, "version"), "Metadata missing version"
    assert hasattr(metadata, "author"), "Metadata missing author"
    assert hasattr(metadata, "plugin_type"), "Metadata missing plugin_type"
    assert hasattr(metadata, "tags"), "Metadata missing tags"

@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
def test_plugin_metadata_values(plugin_module):
    """Test that plugin metadata has valid values"""
    plugin = plugin_module.plugin
    metadata = plugin.metadata
    
    assert isinstance(metadata.id, str) and len(metadata.id) > 0, "Invalid plugin id"
    assert isinstance(metadata.name, str) and len(metadata.name) > 0, "Invalid plugin name"
    assert isinstance(metadata.description, str), "Invalid plugin description"
    assert isinstance(metadata.version, str) and len(metadata.version) > 0, "Invalid plugin version"
    assert isinstance(metadata.author, str), "Invalid plugin author"
    assert isinstance(metadata.tags, list), "Plugin tags must be a list"

@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
def test_plugin_has_required_methods(plugin_module):
    """Test that each plugin has required methods"""
    plugin = plugin_module.plugin
    
    assert hasattr(plugin, "initialize"), f"{plugin_module.__name__} missing initialize method"
    assert hasattr(plugin, "execute"), f"{plugin_module.__name__} missing execute method"
    assert hasattr(plugin, "connect"), f"{plugin_module.__name__} missing connect method"
    assert hasattr(plugin, "disconnect"), f"{plugin_module.__name__} missing disconnect method"
    assert hasattr(plugin, "shutdown"), f"{plugin_module.__name__} missing shutdown method"
    assert hasattr(plugin, "get_schema"), f"{plugin_module.__name__} missing get_schema method"

@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
def test_plugin_get_schema_returns_dict(plugin_module):
    """Test that get_schema returns a dictionary"""
    plugin = plugin_module.plugin
    schema = plugin.get_schema()
    
    assert isinstance(schema, dict), "get_schema must return a dict"
    assert "type" in schema, "Schema must have a type field"
    assert "properties" in schema, "Schema must have a properties field"

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
async def test_plugin_initialize(plugin_module):
    """Test that plugin can be initialized"""
    plugin = plugin_module.plugin
    result = await plugin.initialize()
    
    assert isinstance(result, bool), "initialize must return a boolean"

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
async def test_plugin_connect(plugin_module):
    """Test that plugin can connect"""
    plugin = plugin_module.plugin
    await plugin.initialize()
    
    result = await plugin.connect({})
    
    assert isinstance(result, bool), "connect must return a boolean"

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
async def test_plugin_disconnect(plugin_module):
    """Test that plugin can disconnect"""
    plugin = plugin_module.plugin
    await plugin.initialize()
    await plugin.connect({})
    
    result = await plugin.disconnect()
    
    assert isinstance(result, bool), "disconnect must return a boolean"

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
async def test_plugin_shutdown(plugin_module):
    """Test that plugin can shutdown"""
    plugin = plugin_module.plugin
    await plugin.initialize()
    
    # Should not raise an exception
    await plugin.shutdown()

@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.parametrize("plugin_module", PLUGIN_MODULES)
async def test_plugin_execute_requires_connection(plugin_module):
    """Test that execute requires connection"""
    plugin = plugin_module.plugin
    await plugin.initialize()
    
    # Execute without connecting should return error
    result = await plugin.execute("get_status", {})
    
    assert isinstance(result, dict), "execute must return a dict"
    assert "success" in result, "Result must have success field"
    assert result["success"] == False, "execute should fail without connection"
    assert "error" in result, "Result must have error field"

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("plugin_module", [
    windows_search_plugin,
    windows_defender_plugin,
    windows_firewall_plugin,
    windows_update_plugin
])
async def test_critical_plugins_execute(plugin_module):
    """Integration test for critical plugins"""
    plugin = plugin_module.plugin
    await plugin.initialize()
    await plugin.connect({})
    
    # Try get_status action
    result = await plugin.execute("get_status", {})
    
    assert isinstance(result, dict), "Result must be a dict"
    # Note: May fail on non-Windows systems, which is expected
    
    await plugin.shutdown()

@pytest.mark.unit
def test_winrm_plugin_session_management():
    """Test WinRM plugin has session management"""
    plugin = winrm_integration_plugin.plugin
    assert hasattr(plugin, "_sessions"), "WinRM plugin should have _sessions attribute"

@pytest.mark.unit
def test_wpr_plugin_recordings_management():
    """Test Performance Recorder plugin has recordings management"""
    plugin = windows_performance_recorder_plugin.plugin
    assert hasattr(plugin, "_active_recordings"), "WPR plugin should have _active_recordings"

@pytest.mark.unit
def test_wsa_plugin_adb_path():
    """Test WSA plugin has ADB path management"""
    plugin = windows_subsystem_android_plugin.plugin
    assert hasattr(plugin, "_adb_path"), "WSA plugin should have _adb_path"

@pytest.mark.unit
def test_all_plugins_have_connected_flag():
    """Test that all plugins have a connected flag"""
    for plugin_module in PLUGIN_MODULES:
        plugin = plugin_module.plugin
        assert hasattr(plugin, "connected"), f"{plugin_module.__name__} missing connected flag"

@pytest.mark.unit
def test_plugin_count():
    """Test that we have all 30 Windows OS plugins"""
    assert len(PLUGIN_MODULES) == 30, "Should have exactly 30 Windows OS plugins"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_plugin_lifecycle():
    """Test complete plugin lifecycle"""
    plugin = windows_search_plugin.plugin
    
    # Initialize
    init_result = await plugin.initialize()
    assert init_result == True, "Plugin should initialize successfully"
    
    # Connect
    connect_result = await plugin.connect({})
    assert connect_result == True, "Plugin should connect successfully"
    assert plugin.connected == True, "Plugin should be connected"
    
    # Execute (may fail on non-Windows, which is fine)
    execute_result = await plugin.execute("get_status", {})
    assert isinstance(execute_result, dict), "Execute should return a dict"
    
    # Disconnect
    disconnect_result = await plugin.disconnect()
    assert disconnect_result == True, "Plugin should disconnect successfully"
    assert plugin.connected == False, "Plugin should not be connected"
    
    # Shutdown
    await plugin.shutdown()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
