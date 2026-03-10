"""CLI runner for Azure Speech plugin"""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.azure_speech_plugin import Plugin

async def main():
    plugin = Plugin()
    init = await plugin.initialize()
    print(f"Plugin initialized: {init}")
    if not os.getenv("AZURE_SPEECH_KEY"):
        print("Azure Speech key not found. Limited functionality.")
    result = await plugin.execute("list_voices", {})
    print(f"Voices available: {len(result.get('result', {}).get('voices', []))}")
    await plugin.shutdown()
    print("Plugin shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
