"""Tests for Deepgram plugin"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from windows_ai.plugins.builtin.audio_models.deepgram_plugin import Plugin

@pytest.mark.asyncio
async def test_deepgram_initialization():
    """Test plugin initialization"""
    plugin = Plugin()
    success = await plugin.initialize()
    assert success, "Plugin should initialize"
    assert plugin._initialized, "Plugin should be marked as initialized"
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_deepgram_list_models():
    """Test list_models action"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("list_models", {})
    assert result["success"], "list_models should succeed"
    assert "models" in result["result"], "Should include models"
    assert "nova-2" in result["result"]["models"], "Should support nova-2"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_deepgram_list_languages():
    """Test list_languages action"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("list_languages", {})
    assert result["success"], "list_languages should succeed"
    assert "languages" in result["result"], "Should include languages"
    assert result["result"]["total_languages"] > 0, "Should have languages"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_deepgram_transcribe_offline():
    """Test offline transcription"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None
    
    result = await plugin.execute("transcribe", {
        "audio_url": "https://example.com/test_audio.mp3",
        "model": "nova-2"
    })
    
    assert result["success"], "Offline transcription should succeed"
    assert result["result"]["mode"] == "offline_simulation", "Should be offline mode"
    assert "text" in result["result"], "Should have text field"
    assert result["result"]["confidence"] > 0, "Confidence should be positive"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_deepgram_batch_transcribe_offline():
    """Test batch transcription offline"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None
    
    result = await plugin.execute("batch_transcribe", {
        "audio_urls": [
            "https://example.com/audio1.mp3",
            "https://example.com/audio2.mp3"
        ]
    })
    
    assert result["success"], "Batch transcription should succeed"
    assert result["result"]["total_items"] == 2, "Should process 2 URLs"
    assert result["result"]["successful"] == 2, "Both should succeed"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_deepgram_get_features():
    """Test get_features action"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("get_features", {})
    assert result["success"], "get_features should succeed"
    assert "supported_formats" in result["result"], "Should include formats"
    assert "features" in result["result"], "Should include features"
    
    await plugin.shutdown()
