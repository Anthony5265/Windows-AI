"""
GitHub Copilot API Plugin
Supports code completion and chat
"""

from typing import Dict, Any, Optional, List
import os


class CopilotPlugin:
    """Plugin for GitHub Copilot"""

    name = "github_copilot"
    version = "1.0.0"
    description = "Integration with GitHub Copilot for code completion and chat"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GitHub Copilot plugin"""
        try:
            import requests

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("GITHUB_TOKEN")
            )

            if not self.api_key:
                return False

            self.client = requests
            self.base_url = "https://api.githubcopilot.com"
            self._initialized = True
            return True

        except ImportError:
            print("requests package not installed. Install with: pip install requests")
            return False
        except Exception as e:
            print(f"Error initializing Copilot plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Copilot action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "complete":
                return self._complete(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "explain":
                return self._explain(params)
            elif action == "fix":
                return self._fix(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code completion"""
        code = params.get("code", "")
        language = params.get("language", "python")
        cursor_position = params.get("cursor_position", len(code))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/v1/completions",
            headers=headers,
            json={
                "prompt": code,
                "language": language,
                "position": cursor_position
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "completions": data.get("choices", [])
            }
        return {"success": False, "error": response.text}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with Copilot"""
        messages = params.get("messages", [])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json={
                "messages": messages,
                "model": "gpt-4"
            }
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", "")
            }
        return {"success": False, "error": response.text}

    def _explain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain code"""
        code = params.get("code", "")
        language = params.get("language", "python")

        messages = [
            {"role": "system", "content": "You are a code explanation assistant."},
            {"role": "user", "content": f"Explain this {language} code:\n\n{code}"}
        ]

        return self._chat({"messages": messages})

    def _fix(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fix code issues"""
        code = params.get("code", "")
        error = params.get("error", "")
        language = params.get("language", "python")

        messages = [
            {"role": "system", "content": "You are a code debugging assistant."},
            {"role": "user", "content": f"Fix this {language} code error:\n\nCode:\n{code}\n\nError:\n{error}"}
        ]

        return self._chat({"messages": messages})

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
