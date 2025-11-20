"""
Writer AI Plugin
Supports Palmyra models for enterprise content generation
"""

from typing import Dict, Any, Optional, List
import os


class WriterPlugin:
    """Plugin for Writer AI (Palmyra models)"""

    name = "writer"
    version = "1.0.0"
    description = "Integration with Writer AI's Palmyra models for enterprise content"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.org_id: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Writer plugin"""
        try:
            import requests

            # Get credentials from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("WRITER_API_KEY")
            )
            self.org_id = (
                config.get("org_id") if config
                else os.getenv("WRITER_ORG_ID")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.writer.com/v1"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Writer plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Writer action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            elif action == "completion":
                return self._completion(params)
            elif action == "generate":
                return self._generate(params)
            elif action == "improve":
                return self._improve(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.org_id:
            headers["Organization-Id"] = self.org_id
        return headers

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])
        model = params.get("model", "palmyra-x")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2000)

        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
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

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        model = params.get("model", "palmyra-x")
        temperature = params.get("temperature", 0.7)

        response = self.client.post(
            f"{self.base_url}/completions",
            headers=self._get_headers(),
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("text", ""),
                "usage": data.get("usage", {})
            }
        return {"success": False, "error": response.text}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using templates"""
        template_id = params.get("template_id", "")
        inputs = params.get("inputs", {})

        response = self.client.post(
            f"{self.base_url}/generate",
            headers=self._get_headers(),
            json={
                "templateId": template_id,
                "inputs": inputs
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "content": data.get("content", "")
            }
        return {"success": False, "error": response.text}

    def _improve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Improve existing text"""
        text = params.get("text", "")
        instructions = params.get("instructions", "Improve this text")

        response = self.client.post(
            f"{self.base_url}/improve",
            headers=self._get_headers(),
            json={
                "text": text,
                "instructions": instructions
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "improved_text": data.get("improvedText", "")
            }
        return {"success": False, "error": response.text}

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
