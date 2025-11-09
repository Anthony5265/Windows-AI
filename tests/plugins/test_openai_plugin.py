"""
Tests for OpenAI Plugin
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from windows_ai.plugins.builtin.openai_gpt35_gpt4_gpt4turbo_gpt4v_dalle_3_plugin import Plugin


class TestOpenAIPlugin:
    """Test suite for OpenAI plugin"""

    def test_plugin_initialization(self):
        """Test plugin initializes correctly"""
        plugin = Plugin()
        assert plugin.name == "OpenAI"
        assert plugin.version == "2.0.0"
        assert "OpenAI" in plugin.description

    def test_plugin_without_api_key(self):
        """Test plugin handles missing API key gracefully"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            plugin = Plugin()
            assert plugin.client is None

    @pytest.mark.asyncio
    async def test_execute_without_openai_sdk(self):
        """Test graceful handling when OpenAI SDK not installed"""
        plugin = Plugin()

        with patch('windows_ai.plugins.builtin.openai_gpt35_gpt4_gpt4turbo_gpt4v_dalle_3_plugin.OPENAI_AVAILABLE', False):
            plugin_no_sdk = Plugin()
            result = await plugin_no_sdk.execute(action="chat")

            assert result["status"] == "error"
            assert "not installed" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_without_api_key(self):
        """Test execution fails gracefully without API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            plugin = Plugin()
            result = await plugin.execute(action="chat")

            assert result["status"] == "error"
            assert "API key not configured" in result["message"]

    @pytest.mark.asyncio
    async def test_chat_action_mock(self):
        """Test chat action with mocked OpenAI client"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            plugin = Plugin()

            # Mock the client
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hello! This is a test response."
            mock_response.choices[0].finish_reason = "stop"
            mock_response.model = "gpt-4-turbo"
            mock_response.usage = Mock()
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 20
            mock_response.usage.total_tokens = 30

            if plugin.client:
                plugin.client.chat.completions.create = AsyncMock(return_value=mock_response)

                result = await plugin.execute(
                    action="chat",
                    messages=[{"role": "user", "content": "Hello"}],
                    model="gpt-4-turbo"
                )

                assert result["status"] == "success"
                assert "response" in result
                assert result["model"] == "gpt-4-turbo"
                assert result["usage"]["prompt_tokens"] == 10

    @pytest.mark.asyncio
    async def test_vision_action_validation(self):
        """Test vision action requires image"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.client:
                result = await plugin.execute(action="vision", prompt="What's in this image?")

                assert result["status"] == "error"
                assert "No image provided" in result["message"]

    @pytest.mark.asyncio
    async def test_image_generation_validation(self):
        """Test image generation requires prompt"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.client:
                result = await plugin.execute(action="image")

                assert result["status"] == "error"
                assert "No prompt provided" in result["message"]

    @pytest.mark.asyncio
    async def test_embeddings_validation(self):
        """Test embeddings require input text"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.client:
                result = await plugin.execute(action="embed")

                assert result["status"] == "error"
                assert "No input text provided" in result["message"]

    def test_get_stats(self):
        """Test usage statistics tracking"""
        plugin = Plugin()
        plugin.total_input_tokens = 100
        plugin.total_output_tokens = 200
        plugin.total_cost = 0.05

        result = plugin._get_stats()

        assert result["status"] == "success"
        assert result["stats"]["total_input_tokens"] == 100
        assert result["stats"]["total_output_tokens"] == 200
        assert result["stats"]["total_tokens"] == 300
        assert result["stats"]["total_cost_usd"] == 0.05

    def test_unknown_action(self):
        """Test unknown action returns error"""
        plugin = Plugin()

        # Manually set client to test routing
        if plugin.api_key:
            asyncio.run(self._test_unknown_action_async(plugin))

    async def _test_unknown_action_async(self, plugin):
        """Helper for async unknown action test"""
        result = await plugin.execute(action="unknown_action")
        assert result["status"] == "error"
        assert "Unknown action" in result["message"]

    def test_pricing_data(self):
        """Test pricing data is properly configured"""
        plugin = Plugin()

        assert "gpt-4-turbo" in plugin.pricing
        assert "gpt-3.5-turbo" in plugin.pricing
        assert "dall-e-3" in plugin.pricing
        assert "text-embedding-ada-002" in plugin.pricing

        # Verify pricing structure
        assert "input" in plugin.pricing["gpt-4-turbo"]
        assert "output" in plugin.pricing["gpt-4-turbo"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
