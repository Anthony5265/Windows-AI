"""
Deepgram Speech-to-Text Plugin
Supports real-time and file-based transcription via Deepgram API
"""

from typing import Dict, Any, Optional, List
import os


class DeepgramPlugin:
    """Plugin for Deepgram speech-to-text services"""

    name = "deepgram"
    version = "1.0.0"
    description = "Integration with Deepgram for speech-to-text transcription"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Deepgram plugin"""
        try:
            # Try to import deepgram SDK
            from deepgram import Deepgram

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("DEEPGRAM_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = Deepgram(self.api_key)
            self._initialized = True
            return True

        except ImportError:
            print("deepgram package not installed. Install with: pip install deepgram-sdk")
            return False
        except Exception as e:
            print(f"Error initializing Deepgram plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Deepgram action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "stream_transcribe":
                return self._stream_transcribe(params)
            elif action == "list_models":
                return self._list_models()
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio file"""
        audio_url = params.get("audio_url")
        audio_file = params.get("audio_file")
        model = params.get("model", "nova-2")
        language = params.get("language", "en")
        punctuate = params.get("punctuate", True)
        smart_format = params.get("smart_format", True)

        if not audio_url and not audio_file:
            return {"error": "Either audio_url or audio_file must be provided"}

        try:
            # Prepare options
            options = {
                "model": model,
                "language": language,
                "punctuate": punctuate,
                "smart_format": smart_format,
            }

            if audio_url:
                # Transcribe from URL
                source = {"url": audio_url}
            else:
                # Transcribe from file
                with open(audio_file, "rb") as file:
                    source = {"buffer": file.read(), "mimetype": "audio/wav"}

            response = self.client.transcription.sync_prerecorded(source, options)

            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            confidence = response["results"]["channels"][0]["alternatives"][0]["confidence"]
            duration = response["metadata"]["duration"]

            return {
                "transcript": transcript,
                "confidence": confidence,
                "duration": duration,
                "model": model,
                "language": language,
            }

        except FileNotFoundError:
            return {"error": f"Audio file not found: {audio_file}"}
        except Exception as e:
            return {"error": f"Transcription failed: {str(e)}"}

    def _stream_transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Real-time stream transcription (placeholder for WebSocket implementation)"""
        # Note: Real-time streaming would require WebSocket connection
        # This is a placeholder that could be expanded with asyncio and websockets
        return {"error": "Real-time streaming not yet implemented. Use transcribe action for file transcription."}

    def _list_models(self) -> Dict[str, Any]:
        """List available Deepgram models"""
        models = [
            {"id": "nova-2", "description": "Deepgram's most accurate model"},
            {"id": "nova", "description": "High accuracy model"},
            {"id": "enhanced", "description": "Enhanced accuracy model"},
            {"id": "base", "description": "Base model for general use"},
            {"id": "whisper", "description": "OpenAI Whisper integration"},
        ]

        return {
            "models": models,
            "count": len(models)
        }

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = DeepgramPlugin
PLUGIN_NAME = "deepgram"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Deepgram for speech-to-text transcription"
PLUGIN_ACTIONS = ["transcribe", "stream_transcribe", "list_models"]