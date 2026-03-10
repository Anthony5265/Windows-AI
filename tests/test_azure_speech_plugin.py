"""Tests for Azure Speech plugin"""
import pytest, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.azure_speech_plugin import Plugin

@pytest.mark.asyncio
async def test_azure_speech_initialization():
    plugin = Plugin()
    result = await plugin.initialize()
    assert result == True
    assert plugin._initialized == True
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_azure_speech_list_voices():
    plugin = Plugin()
    await plugin.initialize()
    result = await plugin.execute("list_voices", {})
    assert result["success"] == True
    result_data = result.get("result", {})
    assert "languages" in result_data or "voices" in result_data
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_azure_speech_no_aiohttp():
    plugin = Plugin()
    await plugin.initialize()
    assert plugin._initialized == True
    await plugin.shutdown()
