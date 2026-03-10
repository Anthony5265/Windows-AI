"""CLI runner for Amazon Transcribe plugin"""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from windows_ai.plugins.builtin.audio_models.amazon_transcribe_plugin import Plugin

async def main():
    plugin = Plugin()
    init = await plugin.initialize()
    print(f"Plugin initialized: {init}")
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("AWS credentials not found. Limited functionality.")
    result = await plugin.execute("info", {})
    print(f"Execute result: {result}")
    await plugin.shutdown()
    print("Plugin shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
