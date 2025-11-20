"""
StarCoder Plugin
Supports StarCoder and StarCoder2 models
"""

from typing import Dict, Any, Optional, List
import os


class StarCoderPlugin:
    """Plugin for StarCoder code generation models"""

    name = "starcoder"
    version = "1.0.0"
    description = "Integration with StarCoder/StarCoder2 for code generation"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the StarCoder plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("STARCODER_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing StarCoder plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a StarCoder action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "complete":
                return self._complete(params)
            elif action == "fill":
                return self._fill_in_middle(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "starcoder2:latest")
        temperature = params.get("temperature", 0.2)
        max_tokens = params.get("max_tokens", 256)

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "options": {
                    "num_predict": max_tokens
                },
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "completion": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _fill_in_middle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in the middle completion"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        model = params.get("model", "starcoder2:latest")

        # StarCoder FIM format
        prompt = f"<fim_prefix>{prefix}<fim_suffix>{suffix}<fim_middle>"

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "completion": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
