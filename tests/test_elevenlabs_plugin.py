"""Tests for ElevenLabs plugin"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from windows_ai.plugins.builtin.audio_models.elevenlabs_plugin import Plugin

@pytest.mark.asyncio
async def test_elevenlabs_initialization():
    """Test plugin initialization"""
    plugin = Plugin()
    success = await plugin.initialize()
    assert success, "Plugin should initialize"
    assert plugin._initialized, "Plugin should be marked as initialized"
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_elevenlabs_list_voices():
    """Test list_voices action"""
    plugin = Plugin()
    await plugin.initialize()
    
    result = await plugin.execute("list_voices", {})
    assert result["success"], "list_voices should succeed"
    assert "voices" in result["result"], "Should include voices"
    
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_elevenlabs_tts_offline():
    """Test offline TTS"""
    plugin = Plugin()
    await plugin.initialize()
    plugin._api_key = None
    
    result = await plugin.execute("text_to_speech", {
        "text": "Test speech",
        "voice_id": "21m00Tcm4TlvDq8ikWAM"
    })
    
    assert result["success"], "Offline TTS should succeed"
    assert "note" in result["result"], "Should have note field"
    
    await plugin.shutdown()
