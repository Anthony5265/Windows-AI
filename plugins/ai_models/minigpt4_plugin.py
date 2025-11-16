"""
MiniGPT-4 Plugin
Lightweight multimodal vision-language model
"""

from typing import Dict, Any, Optional, List
import os


class MiniGPT4Plugin:
    """Plugin for MiniGPT-4"""

    name = "minigpt4"
    version = "1.0.0"
    description = "Integration with MiniGPT-4 for vision-language understanding"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:7860"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the MiniGPT-4 plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("MINIGPT4_HOST", "http://localhost:7860")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing MiniGPT-4 plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a MiniGPT-4 action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat about an image"""
        import base64

        image_path = params.get("image_path", "")
        message = params.get("message", "Describe this image")

        # Encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        response = self.client.post(
            f"{self.base_url}/api/predict",
            json={
                "data": [
                    f"data:image/jpeg;base64,{image_data}",
                    message
                ]
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("data", [""])[0]
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
