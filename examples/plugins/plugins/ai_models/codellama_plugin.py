"""
CodeLlama Plugin
Supports 7B, 13B, 34B, 70B models for code generation
"""

from typing import Dict, Any, Optional, List
import os


class CodeLlamaPlugin:
    """Plugin for Meta's CodeLlama models"""

    name = "codellama"
    version = "1.0.0"
    description = "Integration with CodeLlama (7B, 13B, 34B, 70B) for code generation"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CodeLlama plugin"""
        try:
            import requests

            # Get base URL from config or use default (Ollama-compatible)
            self.base_url = (
                config.get("base_url") if config
                else os.getenv("CODELLAMA_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing CodeLlama plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CodeLlama action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "complete":
                return self._complete(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "fill":
                return self._fill_in_middle(params)
            elif action == "instruct":
                return self._instruct(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "codellama:7b")
        temperature = params.get("temperature", 0.2)

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
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

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat-based code generation"""
        messages = params.get("messages", [])
        model = params.get("model", "codellama:7b-instruct")

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

    def _fill_in_middle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in the middle (FIM) completion"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        model = params.get("model", "codellama:7b-code")

        # Format for FIM: <PRE> prefix <SUF> suffix <MID>
        prompt = f"<PRE> {prefix} <SUF> {suffix} <MID>"

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

    def _instruct(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Instruction-based code generation"""
        instruction = params.get("instruction", "")
        model = params.get("model", "codellama:7b-instruct")

        messages = [
            {"role": "user", "content": instruction}
        ]

        return self._chat({"messages": messages, "model": model})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
