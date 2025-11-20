"""
BakLLaVA Plugin
Mistral-based vision-language model
"""

from typing import Dict, Any, Optional, List
import os


class BakLLaVAPlugin:
    """Plugin for BakLLaVA vision model"""

    name = "bakllava"
    version = "1.0.0"
    description = "Integration with BakLLaVA vision-language model"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the BakLLaVA plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("BAKLLAVA_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing BakLLaVA plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a BakLLaVA action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "analyze":
                return self._analyze_image(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image"""
        import base64

        image_path = params.get("image_path", "")
        prompt = params.get("prompt", "Describe this image")

        # Encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": "bakllava",
                "prompt": prompt,
                "images": [image_data],
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
