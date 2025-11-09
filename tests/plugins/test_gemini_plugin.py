"""
Tests for Google Gemini Plugin
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin import Plugin


class TestGeminiPlugin:
    """Test suite for Google Gemini plugin"""

    def test_plugin_initialization(self):
        """Test plugin initializes correctly"""
        plugin = Plugin()
        assert plugin.name == "Google Gemini"
        assert plugin.version == "2.0.0"
        assert "Gemini" in plugin.description

    def test_plugin_without_api_key(self):
        """Test plugin handles missing API key gracefully"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=True):
            plugin = Plugin()
            assert plugin.configured is False

    @pytest.mark.asyncio
    async def test_execute_without_genai_sdk(self):
        """Test graceful handling when Google GenAI SDK not installed"""
        plugin = Plugin()

        with patch('windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin.GENAI_AVAILABLE', False):
            plugin_no_sdk = Plugin()
            result = await plugin_no_sdk.execute(action="chat")

            assert result["status"] == "error"
            assert "not installed" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_without_api_key(self):
        """Test execution fails gracefully without API key"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=True):
            plugin = Plugin()
            result = await plugin.execute(action="chat")

            assert result["status"] == "error"
            assert "API key not configured" in result["message"]

    @pytest.mark.asyncio
    async def test_chat_action_mock(self):
        """Test chat action with mocked Gemini client"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            with patch('windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin.genai') as mock_genai:
                plugin = Plugin()

                # Mock model and response
                mock_model = Mock()
                mock_chat = Mock()
                mock_response = Mock()
                mock_response.text = "Hello! This is a test response from Gemini."

                # Mock finish reason
                mock_finish_reason = Mock()
                mock_finish_reason.name = "STOP"

                mock_candidate = Mock()
                mock_candidate.finish_reason = mock_finish_reason
                mock_candidate.safety_ratings = []
                mock_response.candidates = [mock_candidate]

                # Mock usage metadata
                mock_usage = Mock()
                mock_usage.prompt_token_count = 10
                mock_usage.candidates_token_count = 20
                mock_usage.total_token_count = 30
                mock_response.usage_metadata = mock_usage

                mock_chat.send_message = Mock(return_value=mock_response)
                mock_model.start_chat = Mock(return_value=mock_chat)
                mock_genai.GenerativeModel = Mock(return_value=mock_model)

                result = await plugin.execute(
                    action="chat",
                    messages=[{"role": "user", "content": "Hello"}],
                    model="gemini-1.5-pro-latest"
                )

                assert result["status"] == "success"
                assert "response" in result
                assert result["model"] == "gemini-1.5-pro-latest"
                assert result["usage"]["prompt_tokens"] == 10
                assert result["usage"]["completion_tokens"] == 20

    @pytest.mark.asyncio
    async def test_chat_with_system_instruction(self):
        """Test chat action with system instruction"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            with patch('windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin.genai') as mock_genai:
                plugin = Plugin()

                mock_model = Mock()
                mock_chat = Mock()
                mock_response = Mock()
                mock_response.text = "I am a helpful assistant."

                mock_finish_reason = Mock()
                mock_finish_reason.name = "STOP"
                mock_candidate = Mock()
                mock_candidate.finish_reason = mock_finish_reason
                mock_candidate.safety_ratings = []
                mock_response.candidates = [mock_candidate]

                mock_usage = Mock()
                mock_usage.prompt_token_count = 15
                mock_usage.candidates_token_count = 25
                mock_usage.total_token_count = 40
                mock_response.usage_metadata = mock_usage

                mock_chat.send_message = Mock(return_value=mock_response)
                mock_model.start_chat = Mock(return_value=mock_chat)
                mock_genai.GenerativeModel = Mock(return_value=mock_model)

                result = await plugin.execute(
                    action="chat",
                    messages=[{"role": "user", "content": "Who are you?"}],
                    system_instruction="You are a helpful assistant.",
                    model="gemini-1.5-pro-latest"
                )

                assert result["status"] == "success"
                assert "response" in result

    @pytest.mark.asyncio
    async def test_vision_action_validation(self):
        """Test vision action requires media"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.configured:
                result = await plugin.execute(
                    action="vision",
                    prompt="What's in this image?",
                    model="gemini-1.5-pro-latest"
                )

                assert result["status"] == "error"
                assert "No media provided" in result["message"]

    @pytest.mark.asyncio
    async def test_vision_with_non_multimodal_model(self):
        """Test vision action rejects non-multimodal models"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.configured:
                result = await plugin.execute(
                    action="vision",
                    image_url="https://example.com/image.jpg",
                    prompt="What's in this image?",
                    model="gemini-1.0-pro"  # Non-multimodal model
                )

                assert result["status"] == "error"
                assert "does not support multimodal" in result["message"]

    @pytest.mark.asyncio
    async def test_count_tokens_validation(self):
        """Test count_tokens requires text"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            plugin = Plugin()

            if plugin.configured:
                result = await plugin.execute(action="count_tokens")

                assert result["status"] == "error"
                assert "No text provided" in result["message"]

    @pytest.mark.asyncio
    async def test_count_tokens_mock(self):
        """Test token counting with mocked Gemini client"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            with patch('windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin.genai') as mock_genai:
                plugin = Plugin()

                mock_model = Mock()
                mock_count_result = Mock()
                mock_count_result.total_tokens = 50
                mock_model.count_tokens = Mock(return_value=mock_count_result)
                mock_genai.GenerativeModel = Mock(return_value=mock_model)

                result = await plugin.execute(
                    action="count_tokens",
                    text="This is a test message",
                    model="gemini-1.5-pro-latest"
                )

                assert result["status"] == "success"
                assert result["token_count"] == 50

    @pytest.mark.asyncio
    async def test_list_models_mock(self):
        """Test listing available models"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            with patch('windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin.genai') as mock_genai:
                plugin = Plugin()

                # Mock model info
                mock_model_info = Mock()
                mock_model_info.name = "gemini-1.5-pro-latest"
                mock_model_info.display_name = "Gemini 1.5 Pro"
                mock_model_info.description = "Most capable Gemini model"
                mock_model_info.input_token_limit = 1000000
                mock_model_info.output_token_limit = 8192
                mock_model_info.supported_generation_methods = ['generateContent']

                mock_genai.list_models = Mock(return_value=[mock_model_info])

                result = await plugin.execute(action="models")

                assert result["status"] == "success"
                assert "models" in result
                assert len(result["models"]) == 1
                assert result["models"][0]["id"] == "gemini-1.5-pro-latest"

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

        # Manually set configured to test routing
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

        assert "gemini-1.5-pro-latest" in plugin.pricing
        assert "gemini-1.5-flash-latest" in plugin.pricing
        assert "gemini-1.0-pro" in plugin.pricing
        assert "gemini-1.0-pro-vision" in plugin.pricing

        # Verify pricing structure
        assert "input" in plugin.pricing["gemini-1.5-pro-latest"]
        assert "output" in plugin.pricing["gemini-1.5-pro-latest"]

    def test_multimodal_models_list(self):
        """Test multimodal models are correctly identified"""
        plugin = Plugin()

        assert "gemini-1.5-pro-latest" in plugin.multimodal_models
        assert "gemini-1.5-flash-latest" in plugin.multimodal_models
        assert "gemini-1.0-pro-vision" in plugin.multimodal_models
        assert "gemini-1.0-pro" not in plugin.multimodal_models

    @pytest.mark.asyncio
    async def test_streaming_response(self):
        """Test streaming response handling"""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
            with patch('windows_ai.plugins.builtin.google_gemini_gemini_pro_gemini_ultra_palm_2_bard_plugin.genai') as mock_genai:
                plugin = Plugin()

                # Mock streaming chunks
                class MockChunk:
                    def __init__(self, text):
                        self.text = text

                mock_model = Mock()
                mock_chat = Mock()
                mock_chat.send_message = Mock(return_value=[
                    MockChunk("Hello "),
                    MockChunk("from "),
                    MockChunk("Gemini!")
                ])
                mock_model.start_chat = Mock(return_value=mock_chat)
                mock_genai.GenerativeModel = Mock(return_value=mock_model)

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
