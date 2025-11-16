"""
Alibaba Cloud AI Plugin
Supports Qwen and Tongyi Qianwen models
"""

from typing import Dict, Any, Optional, List
import os


class AlibabaPlugin:
    """Plugin for Alibaba Cloud AI models (Qwen, Tongyi Qianwen)"""

    name = "alibaba"
    version = "1.0.0"
    description = "Integration with Alibaba Cloud AI (Qwen, Tongyi Qianwen models)"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Alibaba Cloud plugin"""
        try:
            import requests

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("ALIBABA_API_KEY")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://dashscope.aliyuncs.com/api/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Alibaba plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Alibaba Cloud action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "embed":
                return self._get_embeddings(params)
            elif action == "multimodal":
                return self._multimodal(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion with Qwen"""
        model = params.get("model", "qwen-turbo")
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/services/aigc/text-generation/generation",
            headers=headers,
            json={
                "model": model,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("output", {}).get("text", ""),
                "usage": data.get("usage", {})
            }
        return {"success": False, "error": response.text}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        model = params.get("model", "qwen-turbo")
        prompt = params.get("prompt", "")
        temperature = params.get("temperature", 0.7)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/services/aigc/text-generation/generation",
            headers=headers,
            json={
                "model": model,
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "temperature": temperature
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("output", {}).get("text", ""),
                "usage": data.get("usage", {})
            }
        return {"success": False, "error": response.text}

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")
        model = params.get("model", "text-embedding-v1")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/services/embeddings/text-embedding/text-embedding",
            headers=headers,
            json={
                "model": model,
                "input": {
                    "texts": [text]
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "embedding": data.get("output", {}).get("embeddings", [])[0]
            }
        return {"success": False, "error": response.text}

    def _multimodal(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Multimodal understanding with Qwen-VL"""
        model = params.get("model", "qwen-vl-plus")
        messages = params.get("messages", [])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/services/aigc/multimodal-generation/generation",
            headers=headers,
            json={
                "model": model,
                "input": {
                    "messages": messages
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
