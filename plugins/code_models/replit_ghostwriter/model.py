"""
Replit Ghostwriter Code Model Integration

Ghostwriter is Replit's AI pair programmer that provides code completion, generation,
transformation, and explanation directly in the Replit IDE.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class ReplitGhostwriter:
    """
    Replit Ghostwriter - AI pair programmer for Replit

    Ghostwriter provides intelligent code assistance powered by large language models,
    optimized for the Replit development environment.

    Supported languages: All major programming languages supported by Replit
    Features: autocomplete, complete-code, generate-code, transform-code, explain-code
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Replit Ghostwriter client

        Args:
            api_key: Replit API token (or set REPLIT_API_KEY env var)
            **kwargs: Additional configuration options
                - api_base: Replit API base URL (default: https://ghostwriter.replit.com)
                - model: Model variant (ghostwriter, ghostwriter-chat)
                - temperature: Sampling temperature (default: 0.2)
                - max_tokens: Maximum tokens to generate (default: 256)
        """
        self.api_key = api_key or os.getenv("REPLIT_API_KEY") or os.getenv("REPL_API_KEY")
        self.api_base = kwargs.get("api_base", "https://ghostwriter.replit.com/v1")
        self.model = kwargs.get("model", "ghostwriter")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 256)
        self.provider = "replit_ghostwriter"

        # Supported programming languages
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown',
            'julia', 'lua', 'perl', 'haskell', 'elixir', 'dart', 'solidity',
            'clojure', 'nim', 'crystal', 'fortran', 'cobol', 'assembly'
        ]

        self.features = [
            'autocomplete', 'complete-code', 'generate-code',
            'transform-code', 'explain-code', 'debug-code'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Ghostwriter

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - suffix: Code after cursor
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - file_path: Path to file being edited
                - intent: Completion intent (autocomplete, complete-function, etc.)

        Returns:
            Dict with completions and metadata
        """
        suffix = kwargs.get("suffix", "")
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        file_path = kwargs.get("file_path", f"main.{self._get_file_extension(language)}")
        intent = kwargs.get("intent", "autocomplete")

        try:
            if not self.api_key:
                return {
                    "error": "Replit API key required. Set REPLIT_API_KEY environment variable.",
                    "completions": [],
                    "provider": "replit_ghostwriter"
                }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Replit-User-Id": os.getenv("REPLIT_USER_ID", "api-user")
            }

            # Build Ghostwriter completion request
            payload = {
                "model": self.model,
                "prefix": code,
                "suffix": suffix,
                "language": language,
                "filepath": file_path,
                "intent": intent,
                "temperature": temperature,
                "maxTokens": max_tokens
            }

            response = requests.post(
                f"{self.api_base}/complete",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                # Handle different response formats
                if "completions" in result:
                    for comp in result["completions"]:
                        completions.append({
                            "text": comp.get("text", ""),
                            "score": comp.get("confidence", 1.0)
                        })
                elif "completion" in result:
                    completions.append({
                        "text": result["completion"],
                        "score": 1.0
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "replit_ghostwriter",
                    "model": self.model
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your Replit API token.",
                    "completions": [],
                    "provider": "replit_ghostwriter"
                }
            elif response.status_code == 403:
                return {
                    "error": "Access forbidden. Ensure you have an active Ghostwriter subscription.",
                    "completions": [],
                    "provider": "replit_ghostwriter"
                }
            elif response.status_code == 404:
                # Fallback to chat-based completion
                return self._complete_via_chat(code, suffix, language, temperature, max_tokens)
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "replit_ghostwriter"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout. Ghostwriter API may be slow or unavailable.",
                "completions": [],
                "provider": "replit_ghostwriter"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "replit_ghostwriter"
            }

    def _complete_via_chat(self, code: str, suffix: str, language: str,
                          temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Fallback to chat API for completion"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"Complete this {language} code:\n\n{code}"
        if suffix:
            prompt += f"\n\n// Code continues: {suffix[:50]}..."

        payload = {
            "model": "ghostwriter-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Ghostwriter, Replit's AI coding assistant. Provide concise code completions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "maxTokens": max_tokens
        }

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completion = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "completions": [{"text": completion, "score": 1.0}],
                    "language": language,
                    "provider": "replit_ghostwriter",
                    "model": "ghostwriter-chat"
                }
        except:
            pass

        return {
            "error": "Failed to complete via chat API",
            "completions": [],
            "provider": "replit_ghostwriter"
        }

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go',
            'rust': 'rs', 'ruby': 'rb', 'php': 'php', 'swift': 'swift',
            'kotlin': 'kt', 'scala': 'scala', 'csharp': 'cs', 'dart': 'dart',
            'solidity': 'sol', 'nim': 'nim', 'crystal': 'cr'
        }
        return extensions.get(language.lower(), 'txt')

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Ghostwriter

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation string
        """
        if not self.api_key:
            return "Error: Replit API key required. Set REPLIT_API_KEY environment variable."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "ghostwriter-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Ghostwriter, Replit's AI coding assistant. Explain code clearly."
                    },
                    {
                        "role": "user",
                        "content": f"Explain this {language} code:\n\n```{language}\n{code}\n```"
                    }
                ],
                "temperature": 0.3,
                "maxTokens": 1024
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                return f"Failed to explain code: HTTP {response.status_code}"

        except Exception as e:
            return f"Failed to explain code: {str(e)}"

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Ghostwriter

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fix
        """
        if not self.api_key:
            return {
                "suggestion": "",
                "error": "Replit API key required. Set REPLIT_API_KEY environment variable.",
                "provider": "replit_ghostwriter"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Debug this {language} code with the following error:

Error: {error}

Code:
```{language}
{code}
```

Provide the fixed code with explanation."""

            payload = {
                "model": "ghostwriter-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Ghostwriter, Replit's AI debugging assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "maxTokens": 1024
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                suggestion = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                return {
                    "suggestion": suggestion,
                    "provider": "replit_ghostwriter",
                    "model": "ghostwriter-chat"
                }
            else:
                return {
                    "suggestion": "",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "replit_ghostwriter"
                }

        except Exception as e:
            return {
                "suggestion": "",
                "error": str(e),
                "provider": "replit_ghostwriter"
            }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Ghostwriter

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - test_framework: Testing framework (pytest, unittest, jest, junit)

        Returns:
            Generated tests string
        """
        if not self.api_key:
            return "# Error: Replit API key required. Set REPLIT_API_KEY environment variable."

        framework = kwargs.get("test_framework", self._get_default_test_framework(language))

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Generate comprehensive {framework} tests for this {language} code:

```{language}
{code}
```

Include:
- Test cases for normal behavior
- Edge cases and boundary conditions
- Error handling tests
- Clear test names and documentation"""

            payload = {
                "model": "ghostwriter-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Ghostwriter, Replit's AI test generation assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "maxTokens": 2048
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                tests = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return tests
            else:
                return f"# Failed to generate tests: HTTP {response.status_code}"

        except Exception as e:
            return f"# Failed to generate tests: {str(e)}"

    def _get_default_test_framework(self, language: str) -> str:
        """Get default testing framework for language"""
        frameworks = {
            'python': 'pytest',
            'javascript': 'jest',
            'typescript': 'jest',
            'java': 'junit',
            'go': 'testing',
            'rust': 'cargo test',
            'ruby': 'rspec',
            'php': 'phpunit',
            'csharp': 'NUnit',
            'swift': 'XCTest',
            'kotlin': 'JUnit'
        }
        return frameworks.get(language.lower(), 'unit tests')

    def is_available(self) -> bool:
        """
        Check if Replit Ghostwriter service is available

        Returns:
            True if service is accessible
        """
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            # Test API connectivity
            response = requests.get(
                f"{self.api_base}/health",
                headers=headers,
                timeout=10
            )

            # Also accept 404 as it means the endpoint exists
            return response.status_code in [200, 401, 404]

        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Replit Ghostwriter",
            "provider": "replit",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_token",
            "api_base": self.api_base,
            "subscription_required": True,
            "open_source": False,
            "description": "AI pair programmer for Replit IDE",
            "website": "https://replit.com/ai"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize Ghostwriter
    ghostwriter = ReplitGhostwriter()

    # Get info
    info = ghostwriter.get_info()
    print("Replit Ghostwriter Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if ghostwriter.is_available():
        print("\nReplit Ghostwriter is available")

        # Test completion
        code = "def quicksort(arr):\n    "
        result = ghostwriter.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nReplit Ghostwriter is not available.")
        print("Set REPLIT_API_KEY environment variable with your Replit API token.")
        print("You need an active Ghostwriter subscription to use this service.")
