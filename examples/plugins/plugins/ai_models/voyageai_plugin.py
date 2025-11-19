"""
Voyage AI Plugin
High-performance embeddings API
"""

from typing import Dict, Any, Optional, List
import os


class VoyageAIPlugin:
    """Plugin for Voyage AI embeddings"""

    name = "voyageai"
    version = "1.0.0"
    description = "Integration with Voyage AI for high-performance embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Voyage AI plugin"""
        try:
            import requests

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("VOYAGE_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.voyageai.com/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Voyage AI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Voyage AI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "embed":
                return self._embed(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _embed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Embed text(s)"""
        texts = params.get("texts", [])
        model = params.get("model", "voyage-01")

        if isinstance(texts, str):
            texts = [texts]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/embeddings",
            headers=headers,
            json={
                "input": texts,
                "model": model
            }
        )

        if response.status_code == 200:
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]

            return {
                "success": True,
                "embeddings": embeddings,
                "usage": data.get("usage", {})
            }

        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
