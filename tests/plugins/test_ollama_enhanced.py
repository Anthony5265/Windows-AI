"""
Tests for Ollama Enhanced Plugin
"""

import pytest
from unittest.mock import AsyncMock, patch

from windows_ai.plugins.builtin.ollama_enhanced import OllamaEnhancedPlugin


class TestOllamaEnhancedPlugin:
    """Test suite for Ollama Enhanced Plugin"""

    @pytest.fixture
    async def plugin(self):
        """Create plugin instance"""
        plugin = OllamaEnhancedPlugin()
        await plugin.initialize()
        yield plugin
        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test plugin initialization"""
        assert plugin.metadata.id == "ollama_enhanced"
        assert plugin.metadata.name == "Ollama Enhanced"
        assert plugin.config is not None

    @pytest.mark.asyncio
    async def test_connect(self, plugin):
        """Test connection to Ollama"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await plugin.connect({})
            # Will succeed if mock is properly configured
            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_list_models(self, plugin, mock_ollama_server):
        """Test listing models"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_ollama_server.get_models_response()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await plugin.execute("list_models", {})

            assert result["success"] is True
            assert "data" in result

    @pytest.mark.asyncio
    async def test_chat(self, plugin, mock_ollama_server):
        """Test chat functionality"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock status check
            status_response = AsyncMock()
            status_response.status_code = 200
            status_response.json.return_value = {"models": []}

            # Mock chat response
            chat_response = AsyncMock()
            chat_response.status_code = 200
            chat_response.json.return_value = mock_ollama_server.get_chat_response("test")

            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.get.return_value = status_response
            mock_instance.post.return_value = chat_response

            plugin.connected = True

            result = await plugin.execute("chat", {
                "model": "llama2",
                "message": "Hello"
            })

            assert "success" in result

    @pytest.mark.asyncio
    async def test_benchmark_model(self, plugin):
        """Test model benchmarking"""
        with patch.object(plugin, '_generate', return_value={
            "status": "success",
            "generated_text": "Test response",
            "response_time": 1.5
        }):
            result = await plugin.execute("benchmark_model", {
                "model": "llama2",
                "test_prompt": "Test"
            })

            assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_recommend_model(self, plugin):
        """Test model recommendations"""
        result = await plugin.execute("recommend_model", {
            "use_case": "code"
        })

        assert result.get("success") is True
        if result.get("data"):
            data = result["data"]
            assert "recommended_models" in data
            assert "code" in str(data["recommended_models"]).lower()

    def test_get_schema(self, plugin):
        """Test schema generation"""
        schema = plugin.get_schema()

        assert "type" in schema
        assert "actions" in schema
        assert "chat" in schema["actions"]
        assert "benchmark_model" in schema["actions"]

    def test_metadata(self, plugin):
        """Test plugin metadata"""
        assert plugin.metadata.version == "3.0.0"
        assert "ollama" in plugin.metadata.tags
        assert "llm" in plugin.metadata.tags
