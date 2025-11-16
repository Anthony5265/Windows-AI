"""
llama.cpp Plugin
Fast C++ implementation of LLaMA inference
"""

from typing import Dict, Any, Optional, List
import os


class LlamaCppPlugin:
    """Plugin for llama.cpp local inference"""

    name = "llamacpp"
    version = "1.0.0"
    description = "Integration with llama.cpp for fast local inference"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:8080"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the llama.cpp plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("LLAMACPP_HOST", "http://localhost:8080")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing llama.cpp plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a llama.cpp action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "completion":
                return self._completion(params)
            elif action == "tokenize":
                return self._tokenize(params)
            elif action == "detokenize":
                return self._detokenize(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        n_predict = params.get("n_predict", 128)
        temperature = params.get("temperature", 0.8)

        response = self.client.post(
            f"{self.base_url}/completion",
            json={
                "prompt": prompt,
                "n_predict": n_predict,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("content", ""),
                "tokens_predicted": data.get("tokens_predicted", 0)
            }
        return {"success": False, "error": response.text}

    def _tokenize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tokenize text"""
        text = params.get("text", "")

        response = self.client.post(
            f"{self.base_url}/tokenize",
            json={"content": text}
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "tokens": data.get("tokens", [])
            }
        return {"success": False, "error": response.text}

    def _detokenize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detokenize tokens"""
        tokens = params.get("tokens", [])

        response = self.client.post(
            f"{self.base_url}/detokenize",
            json={"tokens": tokens}
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "text": data.get("content", "")
            }
        return {"success": False, "error": response.text}

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")

        response = self.client.post(
            f"{self.base_url}/embedding",
            json={"content": text}
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "embedding": data.get("embedding", [])
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
