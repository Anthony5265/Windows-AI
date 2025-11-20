"""Tests for plugin base classes"""
import pytest
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType


class TestPluginBase:
    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata"""
        metadata = PluginMetadata(
            id="test_plugin",
            name="Test Plugin",
            description="A test plugin",
            version="1.0.0",
            author="Test Author",
            plugin_type=PluginType.INTEGRATION
        )

        assert metadata.id == "test_plugin"
        assert metadata.name == "Test Plugin"
        assert metadata.version == "1.0.0"
        assert metadata.plugin_type == PluginType.INTEGRATION

    def test_plugin_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = PluginMetadata(
            id="test",
            name="Test",
            description="Test",
            version="1.0",
            author="Author",
            plugin_type=PluginType.ACTION
        )

        data = metadata.to_dict()

        assert isinstance(data, dict)
        assert data["id"] == "test"
        assert data["plugin_type"] == "action"


class TestPluginTypes:
    def test_plugin_types_exist(self):
        """Test that all plugin types are defined"""
        assert hasattr(PluginType, "ACTION")
        assert hasattr(PluginType, "TOOL")
        assert hasattr(PluginType, "INTEGRATION")
        assert hasattr(PluginType, "UI")
        assert hasattr(PluginType, "AUTOMATION")
