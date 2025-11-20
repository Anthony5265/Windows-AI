"""
ExLlama Plugin
Optimized LLaMA inference with GPTQ quantization
"""

from typing import Dict, Any, Optional, List
import os


class ExLlamaPlugin:
    """Plugin for ExLlama/ExLlamaV2 optimized inference"""

    name = "exllama"
    version = "1.0.0"
    description = "Integration with ExLlama for optimized GPTQ model inference"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:5000"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the ExLlama plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("EXLLAMA_HOST", "http://localhost:5000")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing ExLlama plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an ExLlama action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate":
                return self._generate(params)
            elif action == "chat":
                return self._chat(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 200)
        temperature = params.get("temperature", 0.7)

        response = self.client.post(
            f"{self.base_url}/api/v1/generate",
            json={
                "prompt": prompt,
                "max_new_tokens": max_tokens,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])

        # Format messages into prompt
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        return self._generate({"prompt": prompt})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
