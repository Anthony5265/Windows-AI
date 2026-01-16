"""CLI runner for AssemblyAI plugin testing"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from windows_ai.plugins.builtin.audio_models.assemblyai_plugin import Plugin

async def main():
    """Test AssemblyAI plugin offline"""
    plugin = Plugin()
    
    # Initialize
    success = await plugin.initialize()
    print(f"Plugin initialized: {success}")
    
    # Force offline mode
    plugin._api_key = None
    print("Forced offline mode (no API key)")
    
    # Test list_models
    models = await plugin.execute("list_models", {})
    print(f"\nModels: {models['result']['audio_formats']}")
    
    # Test transcribe (offline)
    result = await plugin.execute("transcribe", {
        "audio_url": "https://example.com/test_audio.mp3",
        "speaker_labels": True,
        "sentiment_analysis": True
    })
    print(f"\nTranscription result: {result['result']['text']}")
    print(f"Mode: {result['result']['mode']}")
    
    # Test list transcripts (should fail without API key)
    list_result = await plugin.execute("list_transcripts", {"limit": 5})
    print(f"\nList transcripts: {list_result.get('error', 'Success')}")
    
    # Shutdown
    await plugin.shutdown()
    print("\nPlugin shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
