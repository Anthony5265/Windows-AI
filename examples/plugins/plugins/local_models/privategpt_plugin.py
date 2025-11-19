"""
PrivateGPT Plugin
Private document QA with local models
"""

from typing import Dict, Any, Optional, List
import os


class PrivateGPTPlugin:
    """Plugin for PrivateGPT document QA"""

    name = "privategpt"
    version = "1.0.0"
    description = "Integration with PrivateGPT for private document QA"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:8001"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the PrivateGPT plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("PRIVATEGPT_HOST", "http://localhost:8001")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing PrivateGPT plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PrivateGPT action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "query":
                return self._query(params)
            elif action == "ingest":
                return self._ingest(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query documents"""
        question = params.get("question", "")

        response = self.client.post(
            f"{self.base_url}/v1/completions",
            json={
                "prompt": question,
                "use_context": True
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "answer": data.get("choices", [{}])[0].get("text", ""),
                "sources": data.get("sources", [])
            }
        return {"success": False, "error": response.text}

    def _ingest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest documents"""
        file_path = params.get("file_path", "")

        with open(file_path, "rb") as f:
            response = self.client.post(
                f"{self.base_url}/v1/ingest",
                files={"file": f}
            )

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Document ingested successfully"
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
