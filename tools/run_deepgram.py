"""CLI runner for Deepgram plugin testing"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from windows_ai.plugins.builtin.audio_models.deepgram_plugin import Plugin

async def main():
    """Test Deepgram plugin offline"""
    plugin = Plugin()
    
    success = await plugin.initialize()
    print(f"Plugin initialized: {success}")
    
    plugin._api_key = None
    print("Forced offline mode\n")
    
    # List models
    models = await plugin.execute("list_models", {})
    print(f"Models: {list(models['result']['models'].keys())}")
    
    # List languages
    languages = await plugin.execute("list_languages", {})
    print(f"Languages: {languages['result']['total_languages']} supported\n")
    
    # Transcribe offline
    result = await plugin.execute("transcribe", {
        "audio_url": "https://example.com/test_audio.mp3",
        "model": "nova-2",
        "language": "en"
    })
    print(f"Transcription: {result['result']['text']}")
    print(f"Confidence: {result['result']['confidence']}")
    print(f"Mode: {result['result']['mode']}")
    
    await plugin.shutdown()
    print("\nPlugin shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
