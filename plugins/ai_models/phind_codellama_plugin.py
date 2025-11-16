"""
Phind CodeLlama Plugin
Supports Phind's fine-tuned CodeLlama models
"""

from typing import Dict, Any, Optional, List
import os


class PhindCodeLlamaPlugin:
    """Plugin for Phind CodeLlama models"""

    name = "phind_codellama"
    version = "1.0.0"
    description = "Integration with Phind's fine-tuned CodeLlama models"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Phind CodeLlama plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("PHIND_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Phind CodeLlama plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Phind CodeLlama action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate":
                return self._generate(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "debug":
                return self._debug(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from instruction"""
        instruction = params.get("instruction", "")
        model = params.get("model", "phind-codellama:latest")

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": instruction,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "code": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with Phind CodeLlama"""
        messages = params.get("messages", [])
        model = params.get("model", "phind-codellama:latest")

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

    def _debug(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Debug code with detailed explanation"""
        code = params.get("code", "")
        error = params.get("error", "")

        instruction = f"Debug this code and explain the issue:\n\nCode:\n{code}\n\nError:\n{error}"

        return self._generate({"instruction": instruction})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
