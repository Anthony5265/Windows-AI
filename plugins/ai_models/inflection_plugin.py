"""
Inflection AI Plugin
Supports Pi assistant
"""

from typing import Dict, Any, Optional, List
import os


class InflectionPlugin:
    """Plugin for Inflection AI (Pi)"""

    name = "inflection"
    version = "1.0.0"
    description = "Integration with Inflection AI's Pi assistant"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Inflection plugin"""
        try:
            import requests

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("INFLECTION_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.inflection.ai/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Inflection plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Inflection action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "stream_chat":
                return self._stream_chat(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with Pi"""
        messages = params.get("messages", [])
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
                "model": "inflection-2.5",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
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

    def _stream_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream chat completion"""
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": "inflection-2.5",
                "messages": messages,
                "temperature": temperature,
                "stream": True
            },
            stream=True
        )

        if response.status_code == 200:
            return {
                "success": True,
                "stream": response.iter_lines()
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
