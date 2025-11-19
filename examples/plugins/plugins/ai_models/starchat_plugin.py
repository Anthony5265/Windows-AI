"""
StarChat Plugin
Supports StarChat and StarCoder-based chat models
"""

from typing import Dict, Any, Optional, List
import os


class StarChatPlugin:
    """Plugin for StarChat code assistant"""

    name = "starchat"
    version = "1.0.0"
    description = "Integration with StarChat for code-focused conversations"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the StarChat plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("STARCHAT_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing StarChat plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a StarChat action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "code_review":
                return self._code_review(params)
            elif action == "explain":
                return self._explain(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with StarChat"""
        messages = params.get("messages", [])
        model = params.get("model", "starchat:latest")

        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("message", {}).get("content", "")
            }
        return {"success": False, "error": response.text}

    def _code_review(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Review code"""
        code = params.get("code", "")
        language = params.get("language", "python")

        messages = [
            {"role": "system", "content": "You are an expert code reviewer."},
            {"role": "user", "content": f"Review this {language} code:\n\n{code}"}
        ]

        return self._chat({"messages": messages})

    def _explain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain code"""
        code = params.get("code", "")
        language = params.get("language", "python")

        messages = [
            {"role": "system", "content": "You are a code explanation assistant."},
            {"role": "user", "content": f"Explain this {language} code:\n\n{code}"}
        ]

        return self._chat({"messages": messages})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
