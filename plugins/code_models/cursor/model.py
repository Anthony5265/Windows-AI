"""
Cursor Code Model Integration

Cursor is an AI-powered code editor built on VS Code with advanced GPT-4 integration.
It provides intelligent code completion, chat, and editing capabilities.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class Cursor:
    """
    Cursor - AI-first code editor

    Cursor uses GPT-4 and other advanced models for intelligent code assistance,
    with deep integration into the editing experience.

    Supported languages: All programming languages
    Features: autocomplete, chat, edit, explain, fix-bugs, generate-tests, cmd-k
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Cursor client

        Args:
            api_key: Cursor API key or OpenAI API key (or set CURSOR_API_KEY env var)
            **kwargs: Additional configuration options
                - model: Model to use (gpt-4, gpt-3.5-turbo, claude-2)
                - temperature: Sampling temperature (default: 0.2)
                - max_tokens: Maximum tokens to generate (default: 256)
                - api_base: Custom API endpoint
        """
        self.api_key = api_key or os.getenv("CURSOR_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = kwargs.get("model", "gpt-4")
        self.api_base = kwargs.get("api_base", "https://api.openai.com/v1")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 256)
        self.provider = "cursor"

        # Supported programming languages (all languages)
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown',
            'julia', 'lua', 'perl', 'haskell', 'elixir', 'clojure', 'dart',
            'objective-c', 'groovy', 'coffeescript', 'erlang', 'fsharp'
        ]

        self.features = [
            'autocomplete', 'chat', 'edit', 'explain',
            'fix-bugs', 'generate-tests', 'cmd-k', 'context-aware'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Cursor

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - suffix: Code after cursor
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - file_path: Path to file being edited (for context)
                - context: Additional context about the codebase

        Returns:
            Dict with completions and metadata
        """
        suffix = kwargs.get("suffix", "")
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        file_path = kwargs.get("file_path", f"untitled.{self._get_file_extension(language)}")
        context = kwargs.get("context", "")

        try:
            if not self.api_key:
                return {
                    "error": "Cursor API key required. Set CURSOR_API_KEY or OPENAI_API_KEY environment variable.",
                    "completions": [],
                    "provider": "cursor"
                }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Build context-aware prompt
            prompt = self._build_completion_prompt(code, suffix, language, file_path, context)

            # Use GPT-4 for high-quality completions
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Cursor, an AI code editor. Provide intelligent, context-aware code completions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.95,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completion_text = result["choices"][0]["message"]["content"]

                # Extract code from markdown if present
                completion_text = self._extract_code(completion_text, language)

                return {
                    "completions": [
                        {
                            "text": completion_text,
                            "score": 1.0
                        }
                    ],
                    "language": language,
                    "provider": "cursor",
                    "model": self.model
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your API key.",
                    "completions": [],
                    "provider": "cursor"
                }
            elif response.status_code == 429:
                return {
                    "error": "Rate limit exceeded. Please try again later.",
                    "completions": [],
                    "provider": "cursor"
                }
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "cursor"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout. API may be slow or unavailable.",
                "completions": [],
                "provider": "cursor"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "cursor"
            }

    def _build_completion_prompt(self, code: str, suffix: str, language: str,
                                 file_path: str, context: str) -> str:
        """Build context-aware completion prompt"""
        prompt = f"Complete the following {language} code"

        if file_path:
            prompt += f" in file {file_path}"

        if context:
            prompt += f"\n\nCodebase context:\n{context}"

        prompt += f"\n\nCode to complete:\n```{language}\n{code}"

        if suffix:
            prompt += f"\n\n// ... code continues with ...\n{suffix[:100]}"

        prompt += "\n```\n\nProvide only the completion, no explanation."

        return prompt

    def _extract_code(self, text: str, language: str) -> str:
        """Extract code from markdown code blocks"""
        # Remove markdown code fences if present
        if "```" in text:
            lines = text.split("\n")
            code_lines = []
            in_code = False

            for line in lines:
                if line.strip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    code_lines.append(line)

            if code_lines:
                return "\n".join(code_lines)

        return text.strip()

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go',
            'rust': 'rs', 'ruby': 'rb', 'php': 'php', 'swift': 'swift',
            'kotlin': 'kt', 'scala': 'scala', 'csharp': 'cs'
        }
        return extensions.get(language.lower(), 'txt')

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Cursor

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation string
        """
        if not self.api_key:
            return "Error: Cursor API key required. Set CURSOR_API_KEY or OPENAI_API_KEY environment variable."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Cursor, an AI code editor. Explain code clearly and concisely."
                    },
                    {
                        "role": "user",
                        "content": f"Explain what this {language} code does:\n\n```{language}\n{code}\n```"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Failed to explain code: HTTP {response.status_code}"

        except Exception as e:
            return f"Failed to explain code: {str(e)}"

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Cursor

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
                "error": "Cursor API key required. Set CURSOR_API_KEY or OPENAI_API_KEY environment variable.",
                "provider": "cursor"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Fix this {language} code that has the following error:

Error: {error}

Code:
```{language}
{code}
```

Provide the corrected code with a brief explanation of the fix."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Cursor, an AI code editor. Fix bugs and explain the solution."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                suggestion = result["choices"][0]["message"]["content"]

                return {
                    "suggestion": suggestion,
                    "provider": "cursor",
                    "model": self.model
                }
            else:
                return {
                    "suggestion": "",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "cursor"
                }

        except Exception as e:
            return {
                "suggestion": "",
                "error": str(e),
                "provider": "cursor"
            }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Cursor

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - test_framework: Testing framework (pytest, unittest, jest, junit)

        Returns:
            Generated tests string
        """
        if not self.api_key:
            return "# Error: Cursor API key required. Set CURSOR_API_KEY or OPENAI_API_KEY environment variable."

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

Requirements:
- Test normal behavior and edge cases
- Include error handling tests
- Use descriptive test names
- Add helpful comments
- Follow {framework} best practices"""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Cursor, an AI code editor. Generate high-quality, comprehensive tests."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2048
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                tests = result["choices"][0]["message"]["content"]
                # Extract code from markdown if present
                return self._extract_code(tests, language)
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
            'swift': 'XCTest'
        }
        return frameworks.get(language.lower(), 'unit tests')

    def is_available(self) -> bool:
        """
        Check if Cursor service is available

        Returns:
            True if service is accessible
        """
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            # Test API connectivity with a minimal request
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10
            )

            return response.status_code in [200, 400]  # 400 is ok, means API is accessible

        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Cursor",
            "provider": "cursor",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_key",
            "api_base": self.api_base,
            "open_source": False,
            "description": "AI-first code editor with GPT-4 integration",
            "website": "https://cursor.sh"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize Cursor
    cursor = Cursor()

    # Get info
    info = cursor.get_info()
    print("Cursor Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if cursor.is_available():
        print("\nCursor is available")

        # Test completion
        code = "def binary_search(arr, target):\n    "
        result = cursor.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nCursor is not available. Check your API key.")
        print("Set CURSOR_API_KEY or OPENAI_API_KEY environment variable.")
