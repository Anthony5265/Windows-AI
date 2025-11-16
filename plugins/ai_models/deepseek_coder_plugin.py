"""
DeepSeek Coder Plugin
Supports DeepSeek Coder models (1.3B-33B)
"""

from typing import Dict, Any, Optional, List
import os


class DeepSeekCoderPlugin:
    """Plugin for DeepSeek Coder models"""

    name = "deepseek_coder"
    version = "1.0.0"
    description = "Integration with DeepSeek Coder (1.3B-33B) for code generation"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the DeepSeek Coder plugin"""
        try:
            import requests

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("DEEPSEEK_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.deepseek.com/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing DeepSeek Coder plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a DeepSeek Coder action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "complete":
                return self._complete(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "fill":
                return self._fill_in_middle(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "deepseek-coder")
        temperature = params.get("temperature", 0.0)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/completions",
            headers=headers,
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "completion": data.get("choices", [{}])[0].get("text", "")
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat-based code generation"""
        messages = params.get("messages", [])
        model = params.get("model", "deepseek-coder")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": messages
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
        return {"success": False, "error": response.text}

    def _fill_in_middle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in the middle completion"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")

        # DeepSeek Coder FIM format
        prompt = f"<｜fim▁begin｜>{prefix}<｜fim▁hole｜>{suffix}<｜fim▁end｜>"

        return self._complete({"prompt": prompt})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
