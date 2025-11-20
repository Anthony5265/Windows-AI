"""Tests for cloud plugins"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp


class TestCloudPlugins:
    @pytest.mark.asyncio
    async def test_azure_functions_plugin_init(self):
        """Test Azure Functions plugin initialization"""
        from windows_ai.plugins.builtin.cloud.azure_functions_plugin import AzureFunctionsPlugin

        plugin = AzureFunctionsPlugin()

        assert plugin.metadata.id == "azure_functions"
        assert plugin.metadata.name == "Azure Functions"
        assert not plugin.connected

    @pytest.mark.asyncio
    async def test_azure_functions_plugin_initialize(self):
        """Test plugin initialization"""
        from windows_ai.plugins.builtin.cloud.azure_functions_plugin import AzureFunctionsPlugin

        plugin = AzureFunctionsPlugin()
        result = await plugin.initialize()

        assert result is True
        assert plugin._initialized is True
        assert plugin.session is not None

        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_azure_functions_plugin_connect(self):
        """Test plugin connection"""
        from windows_ai.plugins.builtin.cloud.azure_functions_plugin import AzureFunctionsPlugin

        plugin = AzureFunctionsPlugin()
        await plugin.initialize()

        result = await plugin.connect({"api_key": "test_key"})

        assert result is True
        assert plugin.connected is True
        assert plugin.api_key == "test_key"

        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_azure_functions_plugin_execute_not_connected(self):
        """Test execute when not connected"""
        from windows_ai.plugins.builtin.cloud.azure_functions_plugin import AzureFunctionsPlugin

        plugin = AzureFunctionsPlugin()
        await plugin.initialize()

        result = await plugin.execute("create", {})

        assert result["success"] is False
        assert "Not connected" in result["error"]

        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_azure_functions_plugin_execute_unknown_action(self):
        """Test execute with unknown action"""
        from windows_ai.plugins.builtin.cloud.azure_functions_plugin import AzureFunctionsPlugin

        plugin = AzureFunctionsPlugin()
        await plugin.initialize()
        await plugin.connect({"api_key": "test"})

        result = await plugin.execute("invalid_action", {})

        assert result["success"] is False
        assert "Unknown action" in result["error"]

        await plugin.shutdown()


class TestAWSPlugins:
    @pytest.mark.asyncio
    async def test_aws_lambda_plugin_exists(self):
        """Test that AWS Lambda plugin can be imported"""
        try:
            from windows_ai.plugins.builtin.cloud import aws_lambda_plugin
            assert aws_lambda_plugin is not None
        except ImportError:
            pytest.skip("AWS Lambda plugin not found")


class TestDatabasePlugins:
    def test_postgres_plugin_exists(self):
        """Test that PostgreSQL plugin exists"""
        try:
            from windows_ai.plugins.builtin.databases import postgres_plugin
            assert postgres_plugin is not None
        except ImportError:
            pytest.skip("PostgreSQL plugin not found")
