"""
Sourcegraph Cody Code Model Integration

Sourcegraph Cody is an AI coding assistant that uses context from your codebase to provide
intelligent code completions, explanations, and more. Uses Anthropic Claude and other models.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class SourcegraphCody:
    """
    Sourcegraph Cody - AI coding assistant with codebase context

    Cody uses advanced LLMs (Claude, GPT-4) with your codebase context for intelligent assistance.
    Provides autocomplete, chat, code explanation, debugging, and test generation.

    Supported languages: All major programming languages
    Features: autocomplete, chat, explain, fix-bugs, generate-tests, code-search
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Sourcegraph Cody client

        Args:
            api_key: Sourcegraph API token (or set SOURCEGRAPH_API_KEY env var)
            **kwargs: Additional configuration options
                - instance_url: Sourcegraph instance URL (default: https://sourcegraph.com)
                - model: Model to use (claude-2, gpt-4, gpt-3.5-turbo)
                - temperature: Sampling temperature (default: 0.2)
                - max_tokens: Maximum tokens to generate (default: 256)
        """
        self.api_key = api_key or os.getenv("SOURCEGRAPH_API_KEY") or os.getenv("SRC_ACCESS_TOKEN")
        self.instance_url = kwargs.get("instance_url", "https://sourcegraph.com")
        self.api_base = f"{self.instance_url}/.api/completions/stream"
        self.model = kwargs.get("model", "anthropic/claude-2")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 256)
        self.provider = "sourcegraph_cody"

        # Supported programming languages (all languages)
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown',
            'julia', 'lua', 'perl', 'haskell', 'elixir', 'clojure', 'dart',
            'objective-c', 'groovy', 'coffeescript', 'erlang', 'fsharp'
        ]

        self.features = [
            'autocomplete', 'chat', 'explain', 'fix-bugs',
            'generate-tests', 'code-search', 'context-aware'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Cody

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - suffix: Code after cursor
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - file_path: Path to file being edited (for context)

        Returns:
            Dict with completions and metadata
        """
        suffix = kwargs.get("suffix", "")
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        file_path = kwargs.get("file_path", f"untitled.{self._get_file_extension(language)}")

        try:
            if not self.api_key:
                return {
                    "error": "Sourcegraph API key required. Set SOURCEGRAPH_API_KEY environment variable.",
                    "completions": [],
                    "provider": "sourcegraph_cody"
                }

            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json"
            }

            # Build completion request
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": self._build_completion_prompt(code, suffix, language, file_path)
                    }
                ],
                "temperature": temperature,
                "maxTokensToSample": max_tokens,
                "topK": 50,
                "topP": 0.95
            }

            # Use non-streaming endpoint for simplicity
            api_endpoint = f"{self.instance_url}/.api/completions/code"

            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completion_text = result.get("completion", "")

                return {
                    "completions": [
                        {
                            "text": completion_text,
                            "score": 1.0
                        }
                    ],
                    "language": language,
                    "provider": "sourcegraph_cody",
                    "model": self.model
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your Sourcegraph API token.",
                    "completions": [],
                    "provider": "sourcegraph_cody"
                }
            elif response.status_code == 404:
                # Fallback to chat completions API
                return self._complete_via_chat(code, suffix, language, temperature, max_tokens)
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "sourcegraph_cody"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout. Sourcegraph instance may be slow or unavailable.",
                "completions": [],
                "provider": "sourcegraph_cody"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "sourcegraph_cody"
            }

    def _complete_via_chat(self, code: str, suffix: str, language: str,
                          temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Fallback to chat completions API"""
        headers = {
            "Authorization": f"token {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"Complete this {language} code:\n\n{code}"
        if suffix:
            prompt += f"\n\n[Code continues with: {suffix[:50]}...]"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "maxTokensToSample": max_tokens
        }

        try:
            response = requests.post(
                f"{self.instance_url}/.api/completions/stream",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                # Parse streaming response
                completion = ""
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            completion += data.get("completion", "")
                        except:
                            continue

                return {
                    "completions": [{"text": completion, "score": 1.0}],
                    "language": language,
                    "provider": "sourcegraph_cody",
                    "model": self.model
                }
        except:
            pass

        return {
            "error": "Failed to complete via chat API",
            "completions": [],
            "provider": "sourcegraph_cody"
        }

    def _build_completion_prompt(self, code: str, suffix: str, language: str, file_path: str) -> str:
        """Build completion prompt with context"""
        prompt = f"File: {file_path}\nLanguage: {language}\n\n"
        prompt += "Complete the following code:\n\n"
        prompt += code

        if suffix:
            prompt += f"\n\n[Code continues with:]\n{suffix}"

        return prompt

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go',
            'rust': 'rs', 'ruby': 'rb', 'php': 'php', 'swift': 'swift'
        }
        return extensions.get(language.lower(), 'txt')

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Cody

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation string
        """
        if not self.api_key:
            return "Error: Sourcegraph API key required. Set SOURCEGRAPH_API_KEY environment variable."

        try:
            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"Explain what this {language} code does in detail:\n\n```{language}\n{code}\n```"

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "maxTokensToSample": 1024
            }

            response = requests.post(
                f"{self.instance_url}/.api/completions/stream",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                explanation = ""
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            explanation += data.get("completion", "")
                        except:
                            continue
                return explanation.strip()
            else:
                return f"Failed to explain code: HTTP {response.status_code}"

        except Exception as e:
            return f"Failed to explain code: {str(e)}"

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Cody

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
                "error": "Sourcegraph API key required. Set SOURCEGRAPH_API_KEY environment variable.",
                "provider": "sourcegraph_cody"
            }

        try:
            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Fix this {language} code that has the following error:

Error: {error}

Code:
```{language}
{code}
```

Provide the corrected code with an explanation of the fix."""

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "maxTokensToSample": 1024
            }

            response = requests.post(
                f"{self.instance_url}/.api/completions/stream",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                suggestion = ""
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            suggestion += data.get("completion", "")
                        except:
                            continue

                return {
                    "suggestion": suggestion.strip(),
                    "provider": "sourcegraph_cody",
                    "model": self.model
                }
            else:
                return {
                    "suggestion": "",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "sourcegraph_cody"
                }

        except Exception as e:
            return {
                "suggestion": "",
                "error": str(e),
                "provider": "sourcegraph_cody"
            }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Cody

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - test_framework: Testing framework (pytest, unittest, jest, junit)

        Returns:
            Generated tests string
        """
        if not self.api_key:
            return "# Error: Sourcegraph API key required. Set SOURCEGRAPH_API_KEY environment variable."

        framework = kwargs.get("test_framework", self._get_default_test_framework(language))

        try:
            headers = {
                "Authorization": f"token {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Generate comprehensive {framework} tests for this {language} code:

```{language}
{code}
```

Include:
- Test cases for normal behavior
- Edge cases
- Error handling tests
- Good test names and documentation"""

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "maxTokensToSample": 2048
            }

            response = requests.post(
                f"{self.instance_url}/.api/completions/stream",
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                tests = ""
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            tests += data.get("completion", "")
                        except:
                            continue
                return tests.strip()
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
            'php': 'phpunit'
        }
        return frameworks.get(language.lower(), 'unit tests')

    def is_available(self) -> bool:
        """
        Check if Sourcegraph Cody service is available

        Returns:
            True if service is accessible
        """
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"token {self.api_key}"
            }

            # Try to access the API endpoint
            response = requests.get(
                f"{self.instance_url}/.api/version",
                headers=headers,
                timeout=10
            )

            return response.status_code in [200, 401, 404]  # 404 is ok, means endpoint exists

        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Sourcegraph Cody",
            "provider": "sourcegraph",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_token",
            "instance_url": self.instance_url,
            "open_source": False,
            "description": "AI coding assistant with codebase context awareness"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize Cody
    cody = SourcegraphCody()

    # Get info
    info = cody.get_info()
    print("Sourcegraph Cody Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if cody.is_available():
        print("\nSourcegraph Cody is available")

        # Test completion
        code = "def calculate_fibonacci(n):\n    "
        result = cody.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nSourcegraph Cody is not available. Check your API token.")
        print("Set SOURCEGRAPH_API_KEY environment variable with your Sourcegraph access token.")
