"""
Tests for Whisper plugin
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from windows_ai.plugins.builtin.audio_models.whisper_plugin import Plugin

@pytest.mark.asyncio
async def test_whisper_initialization():
    """Test plugin initialization"""
    plugin = Plugin()
    assert await plugin.initialize()
    assert plugin._initialized
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_whisper_get_models():
    """Test get_models action"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("get_models", {})
    assert result["success"]
    assert "models" in result["result"]
    assert "whisper-1" in result["result"]["models"]
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_whisper_transcribe_offline():
    """Test transcribe without API key (offline stub)"""
    plugin = Plugin()
    await plugin.initialize()
    
    # Ensure no API key to force stub path
    plugin._api_key = None
    
    result = await plugin.execute("transcribe", {
        "audio_file": "test_audio.mp3",
        "language": "en"
    })
    
    assert result["success"]
    assert "result" in result
    assert "text" in result["result"]
    assert "mode" in result["result"]
    assert result["result"]["mode"] == "offline_simulation"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_whisper_detect_language_offline():
    """Test language detection without API key"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None
    
    result = await plugin.execute("detect_language", {
        "audio_file": "test_audio.mp3"
    })
    
    assert result["success"]
    assert result["result"]["language"] == "en"
    assert "confidence" in result["result"]
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_whisper_translate_offline():
    """Test translation without API key"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None
    
    result = await plugin.execute("translate", {
        "audio_file": "test_audio.mp3"
    })
    
    assert result["success"]
    assert "text" in result["result"]
    assert result["result"]["target_language"] == "en"
    
    await plugin.shutdown()