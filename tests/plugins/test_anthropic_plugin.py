"""
Tests for Anthropic Claude Plugin
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from windows_ai.plugins.builtin.anthropic_claude_claude_instant_claude_2_claude_3_plugin import Plugin


class TestAnthropicPlugin:
    """Test suite for Anthropic Claude plugin"""

    def test_plugin_initialization(self):
        """Test plugin initializes correctly"""
        plugin = Plugin()
        assert plugin.name == "Anthropic Claude"
        assert plugin.version == "2.0.0"
        assert "Claude" in plugin.description

    def test_plugin_without_api_key(self):
        """Test plugin handles missing API key gracefully"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True):
            plugin = Plugin()
            assert plugin.client is None

    @pytest.mark.asyncio
    async def test_execute_without_anthropic_sdk(self):
        """Test graceful handling when Anthropic SDK not installed"""
        plugin = Plugin()

        with patch('windows_ai.plugins.builtin.anthropic_claude_claude_instant_claude_2_claude_3_plugin.ANTHROPIC_AVAILABLE', False):
            plugin_no_sdk = Plugin()
            result = await plugin_no_sdk.execute(action="chat")

            assert result["status"] == "error"
            assert "not installed" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_without_api_key(self):
        """Test execution fails gracefully without API key"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True):
            plugin = Plugin()
            result = await plugin.execute(action="chat")

            assert result["status"] == "error"
            assert "API key not configured" in result["message"]

    @pytest.mark.asyncio
    async def test_chat_action_mock(self):
        """Test chat action with mocked Anthropic client"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            # Mock the client
            mock_response = Mock()
            mock_response.model = "claude-3-sonnet-20240229"
            mock_response.stop_reason = "end_turn"
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 10
            mock_response.usage.output_tokens = 20

            # Mock content blocks
            mock_text_block = Mock()
            mock_text_block.type = "text"
            mock_text_block.text = "Hello! This is a test response from Claude."
            mock_response.content = [mock_text_block]

            if plugin.client:
                plugin.client.messages.create = AsyncMock(return_value=mock_response)

                result = await plugin.execute(
                    action="chat",
                    messages=[{"role": "user", "content": "Hello"}],
                    model="claude-3-sonnet-20240229"
                )

                assert result["status"] == "success"
                assert "response" in result
                assert result["model"] == "claude-3-sonnet-20240229"
                assert result["usage"]["input_tokens"] == 10
                assert result["usage"]["output_tokens"] == 20

    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self):
        """Test chat action with system prompt (Constitutional AI)"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            mock_response = Mock()
            mock_response.model = "claude-3-opus-20240229"
            mock_response.stop_reason = "end_turn"
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 15
            mock_response.usage.output_tokens = 25

            mock_text_block = Mock()
            mock_text_block.type = "text"
            mock_text_block.text = "I am a helpful assistant."
            mock_response.content = [mock_text_block]

            if plugin.client:
                plugin.client.messages.create = AsyncMock(return_value=mock_response)

                result = await plugin.execute(
                    action="chat",
                    messages=[{"role": "user", "content": "Who are you?"}],
                    system="You are a helpful assistant.",
                    model="claude-3-opus-20240229"
                )

                assert result["status"] == "success"
                assert "response" in result

    @pytest.mark.asyncio
    async def test_vision_action_validation(self):
        """Test vision action requires image"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.client:
                result = await plugin.execute(
                    action="vision",
                    prompt="What's in this image?",
                    model="claude-3-sonnet-20240229"
                )

                assert result["status"] == "error"
                assert "No image provided" in result["message"]

    @pytest.mark.asyncio
    async def test_vision_with_non_vision_model(self):
        """Test vision action rejects non-vision models"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.client:
                result = await plugin.execute(
                    action="vision",
                    image_url="https://example.com/image.jpg",
                    prompt="What's in this image?",
                    model="claude-2.1"  # Non-vision model
                )

                assert result["status"] == "error"
                assert "does not support vision" in result["message"]

    @pytest.mark.asyncio
    async def test_vision_action_mock(self):
        """Test vision action with mocked Anthropic client"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            mock_response = Mock()
            mock_response.model = "claude-3-sonnet-20240229"
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 100
            mock_response.usage.output_tokens = 50

            mock_text_block = Mock()
            mock_text_block.type = "text"
            mock_text_block.text = "This image shows a cat sitting on a couch."
            mock_response.content = [mock_text_block]

            if plugin.client:
                plugin.client.messages.create = AsyncMock(return_value=mock_response)

                result = await plugin.execute(
                    action="vision",
                    image_url="https://example.com/cat.jpg",
                    prompt="What's in this image?",
                    model="claude-3-sonnet-20240229"
                )

                assert result["status"] == "success"
                assert "analysis" in result
                assert result["model"] == "claude-3-sonnet-20240229"
                assert result["usage"]["input_tokens"] == 100

    @pytest.mark.asyncio
    async def test_list_models(self):
        """Test listing available models"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.client:
                result = await plugin.execute(action="models")

                assert result["status"] == "success"
                assert "models" in result
                assert len(result["models"]) == 6
                assert result["count"] == 6

                # Check Claude 3 Opus is in list
                opus_model = next((m for m in result["models"] if m["id"] == "claude-3-opus-20240229"), None)
                assert opus_model is not None
                assert opus_model["supports_vision"] is True

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

        assert "claude-3-opus-20240229" in plugin.pricing
        assert "claude-3-sonnet-20240229" in plugin.pricing
        assert "claude-3-haiku-20240307" in plugin.pricing
        assert "claude-2.1" in plugin.pricing
        assert "claude-2.0" in plugin.pricing
        assert "claude-instant-1.2" in plugin.pricing

        # Verify pricing structure
        assert "input" in plugin.pricing["claude-3-opus-20240229"]
        assert "output" in plugin.pricing["claude-3-opus-20240229"]

    def test_vision_models_list(self):
        """Test vision models are correctly identified"""
        plugin = Plugin()

        assert "claude-3-opus-20240229" in plugin.vision_models
        assert "claude-3-sonnet-20240229" in plugin.vision_models
        assert "claude-3-haiku-20240307" in plugin.vision_models
        assert "claude-2.1" not in plugin.vision_models
        assert "claude-instant-1.2" not in plugin.vision_models

    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Test streaming response handling"""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            plugin = Plugin()

            # Mock streaming response
            class MockStreamEvent:
                def __init__(self, text):
                    self.type = "content_block_delta"
                    self.delta = Mock()
                    self.delta.text = text

            async def mock_stream():
                for chunk in ["Hello ", "from ", "Claude!"]:
                    yield MockStreamEvent(chunk)

            if plugin.client:
                mock_stream_response = mock_stream()
                plugin.client.messages.create = AsyncMock(return_value=mock_stream_response)

                result = await plugin.execute(
                    action="chat",
                    messages=[{"role": "user", "content": "Hello"}],
                    stream=True
                )

                assert result["status"] == "success"
                assert result["streaming"] is True
                assert "response" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
