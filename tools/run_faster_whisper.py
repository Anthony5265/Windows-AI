import asyncio
import argparse
from windows_ai.plugins.builtin.audio_models.faster_whisper_plugin import plugin as faster_whisper_plugin

async def main():
    parser = argparse.ArgumentParser(description="Run Faster Whisper transcription")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--model", default="base", help="Model variant (tiny|base|small|medium|large)")
    parser.add_argument("--language", default=None, help="Language code (e.g., en)")
    parser.add_argument("--enable-vad", action="store_true", help="Enable voice activity detection")
    args = parser.parse_args()

    await faster_whisper_plugin.initialize()
    await faster_whisper_plugin.connect()
    result = await faster_whisper_plugin.execute("transcribe", {
        "audio_file": args.audio_file,
        "model": args.model,
        "language": args.language,
        "enable_vad": args.enable_vad
    })
    await faster_whisper_plugin.shutdown()

    if result.get("success"):
        print(result["result"]["text"])
    else:
        print("Error:", result.get("error"))

if __name__ == "__main__":
    asyncio.run(main())
