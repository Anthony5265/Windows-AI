"""CLI runner for Bark plugin"""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.bark_plugin import Plugin

async def main():
    plugin = Plugin()
    init = await plugin.initialize()
    print(f"Plugin initialized: {init}")
    result = await plugin.execute("list_voices", {})
    print(f"Voices: {len(result.get('result', {}).get('voices', []))}")
    await plugin.shutdown()
    print("Plugin shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
