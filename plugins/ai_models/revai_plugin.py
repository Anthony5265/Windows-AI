"""
Rev.ai Plugin
Professional speech-to-text service
"""

from typing import Dict, Any, Optional, List
import os


class RevAIPlugin:
    """Plugin for Rev.ai"""

    name = "revai"
    version = "1.0.0"
    description = "Integration with Rev.ai for professional speech recognition"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Rev.ai plugin"""
        try:
            import requests

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("REVAI_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.rev.ai/speechtotext/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Rev.ai plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Rev.ai action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "transcribe":
                return self._transcribe(params)
            elif action == "get_transcript":
                return self._get_transcript(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transcribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Submit audio for transcription"""
        audio_url = params.get("audio_url", "")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/jobs",
            headers=headers,
            json={"media_url": audio_url}
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "job_id": data["id"]
            }

        return {"success": False, "error": response.text}

    def _get_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get completed transcript"""
        job_id = params.get("job_id", "")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        response = self.client.get(
            f"{self.base_url}/jobs/{job_id}/transcript",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "transcript": data
            }

        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
