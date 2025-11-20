"""
Yandex AI Plugin
Supports YaLM 100B model
"""

from typing import Dict, Any, Optional, List
import os


class YandexPlugin:
    """Plugin for Yandex YaLM models"""

    name = "yandex"
    version = "1.0.0"
    description = "Integration with Yandex YaLM 100B language model"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.folder_id: Optional[str] = None
        self.iam_token: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Yandex plugin"""
        try:
            import requests

            # Get credentials from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("YANDEX_API_KEY")
            )
            self.folder_id = (
                config.get("folder_id") if config
                else os.getenv("YANDEX_FOLDER_ID")
            )
            self.iam_token = (
                config.get("iam_token") if config
                else os.getenv("YANDEX_IAM_TOKEN")
            )

            if not self.iam_token or not self.folder_id:
                return False

            self.client = requests
            self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Yandex plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Yandex action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "tokenize":
                return self._tokenize(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with YaLM"""
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.6)
        max_tokens = params.get("max_tokens", 2000)

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/completion",
            headers=headers,
            json={
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": str(max_tokens)
                },
                "messages": messages
            }
        )

        if response.status_code == 200:
            data = response.json()
            alternatives = data.get("result", {}).get("alternatives", [])
            if alternatives:
                return {
                    "success": True,
                    "response": alternatives[0].get("message", {}).get("text", ""),
                    "usage": data.get("result", {}).get("usage", {})
                }
        return {"success": False, "error": response.text}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        temperature = params.get("temperature", 0.6)

        messages = [{"role": "user", "text": prompt}]
        return self._chat({"messages": messages, "temperature": temperature})

    def _tokenize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tokenize text"""
        text = params.get("text", "")

        headers = {
            "Authorization": f"Bearer {self.iam_token}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/tokenize",
            headers=headers,
            json={
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "text": text
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "tokens": data.get("tokens", []),
                "token_count": len(data.get("tokens", []))
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
