"""
KoboldAI Plugin
Browser-based AI writing tool
"""

from typing import Dict, Any, Optional, List
import os


class KoboldAIPlugin:
    """Plugin for KoboldAI local models"""

    name = "koboldai"
    version = "1.0.0"
    description = "Integration with KoboldAI for creative writing and roleplay"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:5000"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the KoboldAI plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("KOBOLDAI_HOST", "http://localhost:5000")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing KoboldAI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a KoboldAI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate":
                return self._generate(params)
            elif action == "check":
                return self._check(params)
            elif action == "model_info":
                return self._model_info()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        prompt = params.get("prompt", "")
        max_length = params.get("max_length", 80)
        temperature = params.get("temperature", 0.5)

        response = self.client.post(
            f"{self.base_url}/api/v1/generate",
            json={
                "prompt": prompt,
                "max_length": max_length,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("results", [{}])[0].get("text", "")
            }
        return {"success": False, "error": response.text}

    def _check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check generation status"""
        response = self.client.get(f"{self.base_url}/api/v1/generate/check")

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "status": data
            }
        return {"success": False, "error": response.text}

    def _model_info(self) -> Dict[str, Any]:
        """Get loaded model info"""
        response = self.client.get(f"{self.base_url}/api/v1/model")

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "model": data.get("result", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
