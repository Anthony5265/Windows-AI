"""
LocalGPT Plugin
Chat with documents using local models
"""

from typing import Dict, Any, Optional, List
import os


class LocalGPTPlugin:
    """Plugin for LocalGPT document chat"""

    name = "localgpt"
    version = "1.0.0"
    description = "Integration with LocalGPT for document-based conversations"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:5111"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LocalGPT plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("LOCALGPT_HOST", "http://localhost:5111")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing LocalGPT plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LocalGPT action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "ask":
                return self._ask(params)
            elif action == "upload":
                return self._upload_document(params)
            elif action == "list_documents":
                return self._list_documents()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _ask(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ask a question about documents"""
        question = params.get("question", "")

        response = self.client.post(
            f"{self.base_url}/api/prompt_route",
            json={"user_prompt": question}
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "answer": data.get("answer", ""),
                "sources": data.get("source_documents", [])
            }
        return {"success": False, "error": response.text}

    def _upload_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a document"""
        file_path = params.get("file_path", "")

        with open(file_path, "rb") as f:
            response = self.client.post(
                f"{self.base_url}/api/save_document",
                files={"document": f}
            )

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Document uploaded successfully"
            }
        return {"success": False, "error": response.text}

    def _list_documents(self) -> Dict[str, Any]:
        """List uploaded documents"""
        response = self.client.get(f"{self.base_url}/api/get_documents")

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "documents": data.get("documents", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
