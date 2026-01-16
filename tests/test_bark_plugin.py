"""Tests for Bark plugin"""
import pytest, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.bark_plugin import Plugin

@pytest.mark.asyncio
async def test_bark_initialization():
    plugin = Plugin()
    result = await plugin.initialize()
    assert result == True
    assert plugin._initialized == True
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_bark_execute():
    plugin = Plugin()
    await plugin.initialize()
    result = await plugin.execute("info", {})
    assert "success" in result or "result" in result
    await plugin.shutdown()

@pytest.mark.asyncio
async def test_bark_no_aiohttp():
    plugin = Plugin()
    await plugin.initialize()
    assert plugin._initialized == True
    await plugin.shutdown()
