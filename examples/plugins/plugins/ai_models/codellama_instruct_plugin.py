"""
CodeLlama Instruct Plugin
Supports instruction-tuned CodeLlama models
"""

from typing import Dict, Any, Optional, List
import os


class CodeLlamaInstructPlugin:
    """Plugin for CodeLlama Instruct models"""

    name = "codellama_instruct"
    version = "1.0.0"
    description = "Integration with CodeLlama Instruct for instruction-based code generation"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CodeLlama Instruct plugin"""
        try:
            import requests

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
            print(f"Error initializing CodeLlama Instruct plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CodeLlama Instruct action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "instruct":
                return self._instruct(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "refactor":
                return self._refactor(params)
            elif action == "document":
                return self._document(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _instruct(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from instruction"""
        instruction = params.get("instruction", "")
        model = params.get("model", "codellama:7b-instruct")
        context = params.get("context", "")

        prompt = instruction
        if context:
            prompt = f"Context:\n{context}\n\nInstruction:\n{instruction}"

        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "code": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat-based interaction"""
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

    def _refactor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code based on instructions"""
        code = params.get("code", "")
        instructions = params.get("instructions", "Improve code quality and readability")
        language = params.get("language", "python")

        instruction = f"Refactor this {language} code following these instructions: {instructions}\n\nOriginal code:\n{code}\n\nRefactored code:"

        return self._instruct({"instruction": instruction})

    def _document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add documentation to code"""
        code = params.get("code", "")
        language = params.get("language", "python")
        style = params.get("style", "docstring")

        instruction = f"Add {style} documentation to this {language} code:\n\n{code}\n\nDocumented code:"

        return self._instruct({"instruction": instruction})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
