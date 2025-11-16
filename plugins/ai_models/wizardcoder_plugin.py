"""
WizardCoder Plugin
Supports WizardCoder models for advanced code generation
"""

from typing import Dict, Any, Optional, List
import os


class WizardCoderPlugin:
    """Plugin for WizardCoder models"""

    name = "wizardcoder"
    version = "1.0.0"
    description = "Integration with WizardCoder for advanced code generation"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: str = "http://localhost:11434"
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the WizardCoder plugin"""
        try:
            import requests

            self.base_url = (
                config.get("base_url") if config
                else os.getenv("WIZARDCODER_HOST", "http://localhost:11434")
            )

            self.client = requests
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing WizardCoder plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a WizardCoder action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate":
                return self._generate(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "optimize":
                return self._optimize(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from instruction"""
        instruction = params.get("instruction", "")
        model = params.get("model", "wizardcoder:latest")

        # Format instruction in WizardCoder style
        prompt = f"Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Response:"

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
                "code": data.get("response", "")
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with WizardCoder"""
        messages = params.get("messages", [])
        model = params.get("model", "wizardcoder:latest")

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

    def _optimize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing code"""
        code = params.get("code", "")
        language = params.get("language", "python")

        instruction = f"Optimize this {language} code for better performance and readability:\n\n{code}"

        return self._generate({"instruction": instruction})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
