"""
WellSaid Labs TTS Plugin
Supports text-to-speech synthesis via WellSaid Labs API
"""

from typing import Dict, Any, Optional, List
import os


class WellSaidPlugin:
    """Plugin for WellSaid Labs text-to-speech services"""

    name = "wellsaid"
    version = "1.0.0"
    description = "Integration with WellSaid Labs for text-to-speech synthesis"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.wellsaidlabs.com/v1"
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the WellSaid plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("WELLSAID_API_KEY")
            )

            if not self.api_key:
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing WellSaid plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WellSaid action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}

        try:
            if action == "tts":
                return self._tts(params)
            elif action == "tts_async":
                return self._tts_async(params)
            elif action == "list_voices":
                return self._list_voices()
            elif action == "get_clip":
                return self._get_clip(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _tts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate speech from text (streaming)"""
        import requests

        text = params.get("text", "")
        speaker_id = params.get("speaker_id", "1")  # Default speaker
        model = params.get("model", "tacotron2")
        format_type = params.get("format", "mp3")  # mp3, wav, etc.

        if not text:
            return {"error": "Text is required"}

        payload = {
            "text": text,
            "speaker_id": speaker_id,
            "model": model,
            "format": format_type
        }

        # Add optional parameters
        if "speed" in params:
            payload["speed"] = params["speed"]
        if "pitch" in params:
            payload["pitch"] = params["pitch"]
        if "volume" in params:
            payload["volume"] = params["volume"]

        response = requests.post(
            f"{self.base_url}/tts/stream",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        # For streaming TTS, return the audio data
        audio_data = response.content

        return {
            "audio_data": audio_data,
            "format": format_type,
            "speaker_id": speaker_id,
            "model": model,
            "text_length": len(text)
        }

    def _tts_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate speech from text asynchronously"""
        import requests

        text = params.get("text", "")
        speaker_id = params.get("speaker_id", "1")
        model = params.get("model", "tacotron2")
        format_type = params.get("format", "mp3")

        if not text:
            return {"error": "Text is required"}

        payload = {
            "text": text,
            "speaker_id": speaker_id,
            "model": model,
            "format": format_type
        }

        # Add optional parameters
        if "speed" in params:
            payload["speed"] = params["speed"]
        if "pitch" in params:
            payload["pitch"] = params["pitch"]
        if "volume" in params:
            payload["volume"] = params["volume"]

        response = requests.post(
            f"{self.base_url}/clips",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        return {
            "clip_id": data.get("id"),
            "status": "processing",
            "speaker_id": speaker_id,
            "model": model,
            "text_length": len(text)
        }

    def _list_voices(self) -> Dict[str, Any]:
        """List available voices/avatars"""
        import requests

        response = requests.get(
            f"{self.base_url}/avatars",
            headers={
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        voices = []
        for avatar in data:
            voices.append({
                "id": avatar.get("id"),
                "name": avatar.get("name"),
                "language": avatar.get("language"),
                "gender": avatar.get("gender"),
                "description": avatar.get("description")
            })

        return {
            "voices": voices,
            "count": len(voices)
        }

    def _get_clip(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a clip or download it"""
        import requests

        clip_id = params.get("clip_id")
        if not clip_id:
            return {"error": "clip_id is required"}

        response = requests.get(
            f"{self.base_url}/clips/{clip_id}",
            headers={
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        result = {
            "clip_id": data.get("id"),
            "status": data.get("status"),
            "speaker_id": data.get("speaker_id"),
            "model": data.get("model"),
            "text": data.get("text"),
            "duration": data.get("duration"),
            "created_at": data.get("created_at")
        }

        # If the clip is ready, include download URL
        if data.get("status") == "complete" and "url" in data:
            result["download_url"] = data["url"]

        return result

    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = WellSaidPlugin
PLUGIN_NAME = "wellsaid"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with WellSaid Labs for text-to-speech synthesis"
PLUGIN_ACTIONS = ["tts", "tts_async", "list_voices", "get_clip"]