"""
Baidu AI Plugin
Supports ERNIE Bot and ERNIE 3.5 models
"""

from typing import Dict, Any, Optional, List
import os


class BaiduPlugin:
    """Plugin for Baidu ERNIE models"""

    name = "baidu"
    version = "1.0.0"
    description = "Integration with Baidu ERNIE Bot (ERNIE 3.5, ERNIE-Bot-turbo)"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.secret_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Baidu plugin"""
        try:
            import requests

            # Get credentials from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("BAIDU_API_KEY")
            )
            self.secret_key = (
                config.get("secret_key") if config
                else os.getenv("BAIDU_SECRET_KEY")
            )

            if not self.api_key or not self.secret_key:
                return False

            self.client = requests

            # Get access token
            token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
            response = self.client.post(token_url)

            if response.status_code == 200:
                self.access_token = response.json().get("access_token")
                self._initialized = True
                return True
            return False

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Baidu plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Baidu action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "embed":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with ERNIE Bot"""
        messages = params.get("messages", [])
        model = params.get("model", "ernie-bot-turbo")
        temperature = params.get("temperature", 0.7)

        # Map model names to API endpoints
        model_endpoints = {
            "ernie-bot": "completions",
            "ernie-bot-turbo": "eb-instant",
            "ernie-bot-4": "completions_pro"
        }

        endpoint = model_endpoints.get(model, "eb-instant")

        response = self.client.post(
            f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}?access_token={self.access_token}",
            json={
                "messages": messages,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("result", ""),
                "usage": data.get("usage", {})
            }
        return {"success": False, "error": response.text}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "ernie-bot-turbo")

        # Convert prompt to messages format
        messages = [{"role": "user", "content": prompt}]

        return self._chat({"messages": messages, "model": model})

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")

        response = self.client.post(
            f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1?access_token={self.access_token}",
            json={
                "input": [text]
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "embedding": data.get("data", [{}])[0].get("embedding", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        self.access_token = None
        return True
