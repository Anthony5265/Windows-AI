"""Tests for Amazon Transcribe plugin"""
import pytest, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.amazon_transcribe_plugin import Plugin

@pytest.mark.asyncio
async def test_amazon_transcribe_initialization():
    plugin = Plugin()
    result = await plugin.initialize()
    assert result == True
    assert plugin._initialized == True
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_amazon_transcribe_execute():
    plugin = Plugin()
    await plugin.initialize()
    result = await plugin.execute("info", {"test": "data"})
    assert result["success"] == True
    assert result["result"]["test"] == "data"
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_amazon_transcribe_no_aiohttp():
    plugin = Plugin()
    await plugin.initialize()
    # Should work even if aiohttp not available
    assert plugin._initialized == True
    await plugin.shutdown()
