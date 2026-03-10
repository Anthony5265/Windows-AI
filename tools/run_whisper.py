"""
CLI runner for Whisper plugin
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from windows_ai.plugins.builtin.audio_models.whisper_plugin import Plugin

async def main():
    print("Initializing Whisper plugin...")
    plugin = Plugin()
    
    if not await plugin.initialize():
        print("Failed to initialize plugin")
        return 1
    
    # Clear API key to force offline stub mode
    plugin._api_key = None
    
    print("Plugin initialized (offline mode)")
    
    # Connect (no credentials needed for offline mode)
    await plugin.connect()
    print("Connected")
    
    # Get models
    models_result = await plugin.execute("get_models", {})
    if models_result["success"]:
        print(f"Available models: {list(models_result['result']['models'].keys())}")
    
    # Transcribe test
    print("\nTesting transcription (offline stub)...")
    result = await plugin.execute("transcribe", {
        "audio_file": "test_audio.mp3",
        "language": "en"
    })
    
    if result["success"]:
        print(f"Result: {result['result']['text']}")
        print(f"Mode: {result['result'].get('mode', 'unknown')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Shutdown
    await plugin.shutdown()
    print("\nPlugin shutdown complete")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)