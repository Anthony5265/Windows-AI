"""CLI runner for ElevenLabs plugin testing"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from windows_ai.plugins.builtin.audio_models.elevenlabs_plugin import Plugin

async def main():
    """Test ElevenLabs plugin offline"""
    plugin = Plugin()
    
    success = await plugin.initialize()
    print(f"Plugin initialized: {success}")
    
    plugin._api_key = None
    print("Forced offline mode\n")
    
    # List voices
    voices = await plugin.execute("list_voices", {})
    if voices["success"]:
        print(f"Voices: {len(voices['result']['voices'])} available")
    
    # TTS offline
    result = await plugin.execute("text_to_speech", {
        "text": "Hello from ElevenLabs!",
        "voice_id": "21m00Tcm4TlvDq8ikWAM"
    })
    if result["success"]:
        print(f"\nTTS result: {result['result']['note']}")
        print(f"Mode: {result['result'].get('mode', 'N/A')}")
    
    await plugin.shutdown()
    print("\nPlugin shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
