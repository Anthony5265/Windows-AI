"""
Deepgram Plugin
Real-time speech recognition API
"""

from typing import Dict, Any, Optional, List
import os


class DeepgramPlugin:
    """Plugin for Deepgram"""

    name = "deepgram"
    version = "1.0.0"
    description = "Integration with Deepgram for real-time speech recognition"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Deepgram plugin"""
        try:
            import requests

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("DEEPGRAM_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.deepgram.com/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Deepgram plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Deepgram action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "prerecorded":
                return self._prerecorded(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio file"""
        audio_path = params.get("audio_path", "")
        language = params.get("language", "en")

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }

        with open(audio_path, "rb") as audio_file:
            response = self.client.post(
                f"{self.base_url}/listen",
                headers=headers,
                params={"language": language},
                data=audio_file
            )

        if response.status_code == 200:
            data = response.json()
            transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]

            return {
                "success": True,
                "text": transcript
            }

        return {"success": False, "error": response.text}

    def _prerecorded(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe prerecorded audio URL"""
        audio_url = params.get("audio_url", "")

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/listen",
            headers=headers,
            json={"url": audio_url}
        )

        if response.status_code == 200:
            data = response.json()
            transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]

            return {
                "success": True,
                "text": transcript
            }

        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
