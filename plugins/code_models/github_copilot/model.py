"""
GitHub Copilot Code Model Integration

GitHub Copilot is GitHub's AI-powered code completion tool that provides
intelligent suggestions, explanations, and code generation using OpenAI Codex.
"""

import os
import json
import time
import uuid
import requests
from typing import List, Dict, Optional, Any
from pathlib import Path


class GitHubCopilot:
    """
    GitHub Copilot - AI-powered code assistant

    Uses GitHub's Copilot API for code completion, chat, and code understanding.
    Requires GitHub Copilot subscription and authentication.

    Supported languages: Python, JavaScript, TypeScript, Java, C++, Go, Rust, Ruby, PHP, and 70+ more
    Features: autocomplete, chat, explain, generate-tests, fix-bugs, generate-docs
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize GitHub Copilot client

        Args:
            api_key: GitHub token with Copilot access (or set GITHUB_TOKEN env var)
            **kwargs: Additional configuration options
                - api_base: Custom API endpoint (default: https://api.github.com)
                - model: Model to use (default: copilot-codex)
                - timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_COPILOT_TOKEN")
        self.api_base = kwargs.get("api_base", "https://api.github.com")
        self.copilot_api = "https://copilot-proxy.githubusercontent.com"
        self.model = kwargs.get("model", "copilot-codex")
        self.timeout = kwargs.get("timeout", 30)
        self.provider = "github"
        self.session_id = str(uuid.uuid4())

        # Language support
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown'
        ]

        self.features = [
            'autocomplete', 'chat', 'explain', 'generate-tests',
            'fix-bugs', 'generate-docs', 'refactor'
        ]

        # Token cache for OAuth flow
        self._token_cache = None
        self._token_expiry = 0

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - cursor_position: Position in code (default: end)
                - max_tokens: Maximum tokens to generate (default: 100)
                - temperature: Sampling temperature (default: 0.2)
                - suffix: Code after cursor

        Returns:
            Dict with completions and metadata
        """
        cursor_position = kwargs.get("cursor_position", len(code))
        max_tokens = kwargs.get("max_tokens", 100)
        temperature = kwargs.get("temperature", 0.2)
        suffix = kwargs.get("suffix", "")

        try:
            token = self._get_copilot_token()
            if not token:
                return {
                    "error": "Failed to authenticate with GitHub Copilot",
                    "completions": [],
                    "provider": "github_copilot"
                }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Editor-Version": "vscode/1.80.0",
                "Editor-Plugin-Version": "copilot/1.100.0",
                "User-Agent": "GitHubCopilot/1.100.0"
            }

            payload = {
                "prompt": code,
                "suffix": suffix,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 1,
                "n": kwargs.get("n", 3),
                "stream": False,
                "extra": {
                    "language": language,
                    "next_indent": 0,
                    "trim_by_indentation": True,
                    "prompt_tokens": len(code.split()),
                    "suffix_tokens": len(suffix.split())
                }
            }

            response = requests.post(
                f"{self.copilot_api}/v1/engines/copilot-codex/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                for choice in result.get("choices", []):
                    completions.append({
                        "text": choice.get("text", ""),
                        "score": choice.get("score", 0.0),
                        "mean_prob": choice.get("mean_prob", 0.0)
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "github_copilot",
                    "model": self.model
                }
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "github_copilot"
                }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "github_copilot"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code with Copilot

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options
                - temperature: Sampling temperature (default: 0.5)
                - max_tokens: Maximum response tokens (default: 1000)

        Returns:
            Dict with response and metadata
        """
        try:
            token = self._get_copilot_token()
            if not token:
                return {
                    "error": "Failed to authenticate with GitHub Copilot",
                    "response": "",
                    "provider": "github_copilot"
                }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "GitHubCopilot/1.100.0"
            }

            payload = {
                "messages": messages,
                "model": "gpt-4",
                "temperature": kwargs.get("temperature", 0.5),
                "max_tokens": kwargs.get("max_tokens", 1000),
                "stream": False
            }

            response = requests.post(
                f"{self.copilot_api}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout * 2
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get("choices", [{}])[0].get("message", {})

                return {
                    "response": message.get("content", ""),
                    "role": message.get("role", "assistant"),
                    "provider": "github_copilot",
                    "model": "gpt-4",
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "error": f"Chat request failed: {response.status_code}",
                    "message": response.text,
                    "response": "",
                    "provider": "github_copilot"
                }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "github_copilot"
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
            {
                "role": "system",
                "content": "You are a helpful code assistant. Explain code clearly and concisely."
            },
            {
                "role": "user",
                "content": f"Explain this {language} code:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to explain code: {result.get('error', 'Unknown error')}")

    def suggest_fix(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fixes
        """
        messages = [
            {
                "role": "system",
                "content": "You are an expert programmer. Analyze bugs and suggest fixes."
            },
            {
                "role": "user",
                "content": f"Fix this {language} code that has an error:\n\nCode:\n```{language}\n{code}\n```\n\nError:\n{error}\n\nProvide the fixed code and explanation."
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "github_copilot"
        }

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options
                - style: Documentation style (google, numpy, sphinx, jsdoc)

        Returns:
            Generated documentation string
        """
        style = kwargs.get("style", "google" if language == "python" else "jsdoc")

        messages = [
            {
                "role": "system",
                "content": f"You are a documentation expert. Generate {style}-style documentation."
            },
            {
                "role": "user",
                "content": f"Generate {style} documentation for this {language} code:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate docs: {result.get('error', 'Unknown error')}")

    def is_available(self) -> bool:
        """
        Check if GitHub Copilot service is available

        Returns:
            True if service is accessible
        """
        try:
            token = self._get_copilot_token()
            if not token:
                return False

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "GitHubCopilot/1.100.0"
            }

            response = requests.get(
                f"{self.copilot_api}/v1/engines",
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
            "name": "GitHub Copilot",
            "provider": "github",
            "version": "1.100.0",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "github_token",
            "api_base": self.copilot_api
        }

    def _get_copilot_token(self) -> Optional[str]:
        """
        Get Copilot access token (with caching)

        Returns:
            Access token or None if failed
        """
        # Check cache
        if self._token_cache and time.time() < self._token_expiry:
            return self._token_cache

        if not self.api_key:
            return None

        try:
            # Get Copilot token from GitHub API
            headers = {
                "Authorization": f"token {self.api_key}",
                "Accept": "application/json"
            }

            response = requests.get(
                f"{self.api_base}/copilot_internal/v2/token",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self._token_cache = data.get("token")
                # Cache for 15 minutes (tokens typically valid for 30 min)
                self._token_expiry = time.time() + 900
                return self._token_cache

            return None

        except Exception:
            return None


# Example usage and testing
if __name__ == "__main__":
    # Initialize Copilot
    copilot = GitHubCopilot()

    # Get info
    info = copilot.get_info()
    print("GitHub Copilot Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if copilot.is_available():
        print("\nGitHub Copilot is available")

        # Test completion
        code = "def fibonacci(n):\n    "
        result = copilot.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nGitHub Copilot is not available. Check your authentication.")
        print("Set GITHUB_TOKEN environment variable with a token that has Copilot access.")
