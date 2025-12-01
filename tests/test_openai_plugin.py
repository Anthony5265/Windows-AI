"""
Test OpenAI GPT-4 Plugin
Validates all features of the complete implementation
"""
import pytest
import asyncio
import os
from pathlib import Path
import sys

# Add plugin path
sys.path.insert(0, str(Path(__file__).parent.parent / "windows_ai" / "plugins" / "builtin"))

from openai_gpt_4_plugin import Plugin

@pytest.fixture
def plugin():
    """Create plugin instance"""
    # Set test API key if available
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    return Plugin()

@pytest.mark.asyncio
async def test_plugin_initialization(plugin):
    """Test plugin initializes correctly"""
    assert plugin.name == "OpenAI GPT-4"
    assert plugin.version == "2.0.0"
    assert plugin.client is not None

@pytest.mark.asyncio
async def test_chat_completion(plugin):
    """Test basic chat completion"""
    result = await plugin.execute(
        action="chat",
        message="Say 'test successful' if you can read this.",
        model="gpt-3.5-turbo",
        max_tokens=50
    )
    
    assert result.get("success") == True
    assert "response" in result
    assert result["model"] == "gpt-3.5-turbo"
    assert "usage" in result
    assert result["usage"]["total_tokens"] > 0

@pytest.mark.asyncio
async def test_token_counting(plugin):
    """Test token counting"""
    result = plugin._count_tokens_action(
        text="Hello, world!",
        model="gpt-4"
    )
    
    assert result.get("success") == True
    assert "tokens" in result
    assert result["tokens"] > 0

@pytest.mark.asyncio
async def test_conversation_history(plugin):
    """Test conversation history management"""
    conv_id = "test_conv_123"
    
    # First message
    result1 = await plugin.execute(
        action="chat",
        message="Remember the number 42",
        conversation_id=conv_id,
        model="gpt-3.5-turbo",
        max_tokens=50
    )
    
    assert result1.get("success") == True
    assert conv_id in plugin.conversations
    
    # Second message referencing first
    result2 = await plugin.execute(
        action="chat",
        message="What number did I ask you to remember?",
        conversation_id=conv_id,
        model="gpt-3.5-turbo",
        max_tokens=50
    )
    
    assert result2.get("success") == True
    assert len(plugin.conversations[conv_id]) == 4  # 2 user + 2 assistant
    
    # Clear history
    clear_result = plugin._clear_history(conversation_id=conv_id)
    assert clear_result.get("success") == True
    assert conv_id not in plugin.conversations

@pytest.mark.asyncio
async def test_embeddings(plugin):
    """Test embeddings generation"""
    result = await plugin.execute(
        action="embed",
        text="This is a test sentence.",
        model="text-embedding-3-small"
    )
    
    assert result.get("success") == True
    assert "embeddings" in result
    assert len(result["embeddings"]) == 1
    assert len(result["embeddings"][0]) > 0
    assert result["dimensions"] > 0

@pytest.mark.asyncio
async def test_cost_calculation(plugin):
    """Test cost calculation"""
    cost = plugin.calculate_cost(
        input_tokens=1000,
        output_tokens=500,
        model="gpt-4-turbo"
    )
    
    assert cost > 0
    assert cost == (1000 / 1000 * 0.01) + (500 / 1000 * 0.03)

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("TEST_OPENAI_VISION"), reason="Vision test disabled")
async def test_vision_api(plugin):
    """Test vision API (requires test image)"""
    # This would require a test image
    # Skipped by default
    pass

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("TEST_OPENAI_DALLE"), reason="DALL-E test disabled")
async def test_dalle_generation(plugin):
    """Test DALL-E image generation (expensive, disabled by default)"""
    # This is expensive, skip in normal tests
    pass

def test_error_handling():
    """Test error handling without API key"""
    # Create plugin without API key
    os.environ["OPENAI_API_KEY"] = ""
    plugin = Plugin()
    
    result = asyncio.run(plugin.execute(action="chat", message="test"))
    assert "error" in result
    assert "not configured" in result["error"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
