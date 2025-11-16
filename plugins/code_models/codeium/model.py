"""
Codeium Code Model Integration

Codeium is a free AI-powered code acceleration toolkit supporting 70+ languages
with autocomplete, chat, and search capabilities.
"""

import os
import json
import uuid
import requests
from typing import List, Dict, Optional, Any


class Codeium:
    """
    Codeium - Free AI-powered code assistant

    Uses Codeium's API for code completion, chat, and code search.
    Free for individual developers with optional team features.

    Supported languages: 70+ including Python, JavaScript, TypeScript, Java, Go, and more
    Features: autocomplete, chat, search, refactor, generate-tests
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Codeium client

        Args:
            api_key: Codeium API key (or set CODEIUM_API_KEY)
            **kwargs: Additional configuration options
                - api_base: API endpoint (default: https://server.codeium.com)
                - manager_dir: Extension manager directory
        """
        self.api_key = api_key or os.getenv("CODEIUM_API_KEY")
        self.api_base = kwargs.get("api_base", "https://server.codeium.com")
        self.provider = "codeium"
        self.session_id = str(uuid.uuid4())

        # Extensive language support
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'go', 'rust',
            'cpp', 'c', 'csharp', 'php', 'ruby', 'swift', 'kotlin',
            'scala', 'r', 'shell', 'sql', 'html', 'css', 'yaml', 'json'
        ]

        self.features = [
            'autocomplete', 'chat', 'search', 'refactor',
            'generate-tests', 'explain', 'fix-bugs'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - cursor_position: Cursor position
                - max_completions: Maximum completions (default: 10)
                - suffix: Code after cursor

        Returns:
            Dict with completions and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required",
                "completions": [],
                "provider": "codeium"
            }

        try:
            cursor_position = kwargs.get("cursor_position", len(code))
            max_completions = kwargs.get("max_completions", 10)
            suffix = kwargs.get("suffix", "")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "metadata": {
                    "ide_name": "windows-ai",
                    "ide_version": "1.0.0",
                    "extension_version": "1.0.0",
                    "api_key": self.api_key,
                    "session_id": self.session_id,
                    "request_id": str(uuid.uuid4())
                },
                "editor_options": {
                    "tab_size": 4,
                    "insert_spaces": True
                },
                "document": {
                    "absolute_path": f"file.{self._get_extension(language)}",
                    "relative_path": f"file.{self._get_extension(language)}",
                    "text": code + suffix,
                    "cursor_offset": cursor_position,
                    "editor_language": language,
                    "language": self._map_language(language)
                },
                "other_documents": [],
                "multiline_config": {
                    "mode": "auto"
                }
            }

            response = requests.post(
                f"{self.api_base}/exa.language_server_pb.LanguageServerService/GetCompletions",
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                for item in result.get("completionItems", []):
                    completion_parts = item.get("completionParts", [])
                    text = "".join([part.get("text", "") for part in completion_parts])

                    completions.append({
                        "text": text,
                        "type": item.get("completion", {}).get("completionType", ""),
                        "suffix_text": item.get("suffix", {}).get("text", "")
                    })

                return {
                    "completions": completions[:max_completions],
                    "language": language,
                    "provider": "codeium"
                }

            return {
                "error": f"API request failed: {response.status_code}",
                "completions": [],
                "provider": "codeium"
            }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "codeium"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code with Codeium

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options

        Returns:
            Dict with response and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required",
                "response": "",
                "provider": "codeium"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Convert messages to Codeium format
            chat_messages = []
            for msg in messages:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

            payload = {
                "metadata": {
                    "api_key": self.api_key,
                    "session_id": self.session_id,
                    "request_id": str(uuid.uuid4())
                },
                "messages": chat_messages
            }

            response = requests.post(
                f"{self.api_base}/exa.chat_web_server_pb.ChatWebServerService/GetChatMessage",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("message", {}).get("content", ""),
                    "provider": "codeium"
                }

            return {
                "error": f"Chat request failed: {response.status_code}",
                "response": "",
                "provider": "codeium"
            }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "codeium"
            }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation string
        """
        messages = [
            {"role": "user", "content": f"Explain this {language} code:\n\n```{language}\n{code}\n```"}
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to explain: {result.get('error', 'Unknown error')}")

    def suggest_fix(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code

        Args:
            code: Code with bug
            error: Error message
            language: Programming language

        Returns:
            Dict with suggested fixes
        """
        messages = [
            {
                "role": "user",
                "content": f"Fix this {language} code with error:\n\nCode:\n```{language}\n{code}\n```\n\nError: {error}"
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "codeium"
        }

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options

        Returns:
            Generated documentation string
        """
        messages = [
            {
                "role": "user",
                "content": f"Generate documentation for this {language} code:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", "Failed to generate documentation")

    def is_available(self) -> bool:
        """
        Check if Codeium service is available

        Returns:
            True if service is accessible
        """
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.get(
                f"{self.api_base}/heartbeat",
                headers=headers,
                timeout=5
            )

            return response.status_code == 200

        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Codeium",
            "provider": "codeium",
            "version": "1.0.0",
            "supported_languages": self.supported_languages,
            "total_languages": "70+",
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_key",
            "pricing": "Free for individuals"
        }

    def _map_language(self, language: str) -> int:
        """Map language string to Codeium language ID"""
        language_map = {
            'python': 1,
            'javascript': 2,
            'typescript': 3,
            'java': 4,
            'go': 5,
            'rust': 6,
            'cpp': 7,
            'c': 8,
            'csharp': 9,
            'php': 10
        }
        return language_map.get(language.lower(), 0)

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'go': 'go', 'rust': 'rs', 'cpp': 'cpp',
            'c': 'c', 'csharp': 'cs', 'php': 'php', 'ruby': 'rb'
        }
        return extensions.get(language, 'txt')


# Example usage and testing
if __name__ == "__main__":
    # Initialize Codeium
    codeium = Codeium()

    # Get info
    info = codeium.get_info()
    print("Codeium Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if codeium.is_available():
        print("\nCodeium is available")

        # Test completion
        code = "def calculate_sum(a, b):\n    "
        result = codeium.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nCodeium is not available. Set CODEIUM_API_KEY environment variable.")
