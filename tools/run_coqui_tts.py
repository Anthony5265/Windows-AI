"""CLI runner for Coqui TTS plugin"""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.coqui_tts_plugin import Plugin

async def main():
    plugin = Plugin()
    init = await plugin.initialize()
    print(f"Plugin initialized: {init}")
    result = await plugin.execute("list_models", {})
    print(f"Models: {result.get('success', False)}")
    await plugin.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
