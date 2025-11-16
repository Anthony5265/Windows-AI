"""
OpenAI Whisper Plugin
State-of-the-art speech recognition
"""

from typing import Dict, Any, Optional, List
import os


class WhisperPlugin:
    """Plugin for OpenAI Whisper"""

    name = "whisper"
    version = "1.0.0"
    description = "Integration with OpenAI Whisper for speech recognition"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Whisper plugin"""
        try:
            import openai

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("OPENAI_API_KEY")
            )

            if not self.api_key:
                return False

            openai.api_key = self.api_key
            self.client = openai
            self._initialized = True
            return True

        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing Whisper plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Whisper action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "translate":
                return self._translate(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio to text"""
        audio_path = params.get("audio_path", "")
        language = params.get("language", None)

        with open(audio_path, "rb") as audio_file:
            transcript = self.client.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language=language
            )

        return {
            "success": True,
            "text": transcript.text
        }

    def _translate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Translate audio to English"""
        audio_path = params.get("audio_path", "")

        with open(audio_path, "rb") as audio_file:
            translation = self.client.Audio.translate(
                model="whisper-1",
                file=audio_file
            )

        return {
            "success": True,
            "text": translation.text
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
