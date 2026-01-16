"""Tests for AssemblyAI plugin"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from windows_ai.plugins.builtin.audio_models.assemblyai_plugin import Plugin

@pytest.mark.asyncio
async def test_assemblyai_initialization():
    """Test plugin initialization"""
    plugin = Plugin()
    success = await plugin.initialize()
    assert success, "Plugin should initialize"
    assert plugin._initialized, "Plugin should be marked as initialized"
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_assemblyai_list_models():
    """Test list_models action"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("list_models", {})
    assert result["success"], "list_models should succeed"
    assert "audio_formats" in result["result"], "Should include audio formats"
    assert "mp3" in result["result"]["audio_formats"], "Should support mp3"
    assert "supported_languages" in result["result"], "Should include languages"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_assemblyai_transcribe_offline():
    """Test offline transcription"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None  # Force offline mode
    
    result = await plugin.execute("transcribe", {
        "audio_url": "https://example.com/test_audio.mp3",
        "speaker_labels": True,
        "sentiment_analysis": True
    })
    
    assert result["success"], "Offline transcription should succeed"
    assert result["result"]["mode"] == "offline_simulation", "Should be offline mode"
    assert "text" in result["result"], "Should have text field"
    assert result["result"]["status"] == "completed", "Status should be completed"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_assemblyai_batch_transcribe_offline():
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
    assert result["result"]["total_urls"] == 2, "Should process 2 URLs"
    assert result["result"]["successful"] == 2, "Both should succeed in offline mode"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_assemblyai_stream_transcribe():
    """Test stream transcription info"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("stream_transcribe", {})
    assert result["success"], "Stream info should succeed"
    assert "ws_url" in result["result"], "Should have WebSocket URL"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_assemblyai_list_transcripts_no_api_key():
    """Test list_transcripts without API key"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None
    
    result = await plugin.execute("list_transcripts", {"limit": 5})
    assert not result["success"], "Should fail without API key"
    assert result["error_code"] == "NO_API_KEY", "Should have correct error code"
    
    await plugin.shutdown()
