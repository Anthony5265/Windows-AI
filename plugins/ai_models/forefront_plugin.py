"""
Forefront AI Plugin
Supports multiple open-source models via Forefront platform
"""

from typing import Dict, Any, Optional, List
import os


class ForefrontPlugin:
    """Plugin for Forefront AI"""

    name = "forefront"
    version = "1.0.0"
    description = "Integration with Forefront AI platform (multiple open-source models)"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Forefront plugin"""
        try:
            import requests

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("FOREFRONT_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.forefront.ai/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Forefront plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Forefront action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "list_models":
                return self._list_models()
            elif action == "create_assistant":
                return self._create_assistant(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "forefront/neural-chat-7b-v3")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "usage": data.get("usage", {})
            }
        return {"success": False, "error": response.text}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "forefront/neural-chat-7b-v3")

        messages = [{"role": "user", "content": prompt}]
        return self._chat({"messages": messages, "model": model})

    def _list_models(self) -> Dict[str, Any]:
        """List available models"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        response = self.client.get(
            f"{self.base_url}/models",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "models": data.get("data", [])
            }
        return {"success": False, "error": response.text}

    def _create_assistant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom assistant"""
        name = params.get("name", "")
        description = params.get("description", "")
        model = params.get("model", "forefront/neural-chat-7b-v3")
        instructions = params.get("instructions", "")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/assistants",
            headers=headers,
            json={
                "name": name,
                "description": description,
                "model": model,
                "instructions": instructions
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "assistant_id": data.get("id", ""),
                "assistant": data
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
