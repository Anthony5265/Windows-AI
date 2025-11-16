"""
Phind Code Model Integration

Phind is an AI-powered search engine and coding assistant optimized for developers.
It provides intelligent code generation, explanations, and debugging assistance.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class Phind:
    """
    Phind - AI search engine and coding assistant for developers

    Phind combines web search with advanced language models to provide context-aware
    code assistance, technical explanations, and debugging help.

    Supported languages: All major programming languages
    Features: code-generation, explain, debug, search, answer-questions
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Phind client

        Args:
            api_key: Phind API key (or set PHIND_API_KEY env var)
            **kwargs: Additional configuration options
                - api_base: Phind API base URL (default: https://api.phind.com/v1)
                - model: Model to use (phind-codellama-34b-v2, phind-70b)
                - temperature: Sampling temperature (default: 0.2)
                - max_tokens: Maximum tokens to generate (default: 256)
                - include_search: Include web search in responses (default: True)
        """
        self.api_key = api_key or os.getenv("PHIND_API_KEY")
        self.api_base = kwargs.get("api_base", "https://api.phind.com/v1")
        self.model = kwargs.get("model", "phind-codellama-34b-v2")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 256)
        self.include_search = kwargs.get("include_search", True)
        self.provider = "phind"

        # Supported programming languages
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown',
            'julia', 'lua', 'perl', 'haskell', 'elixir', 'clojure', 'dart',
            'objective-c', 'solidity', 'elm', 'erlang', 'fsharp', 'racket'
        ]

        self.features = [
            'code-generation', 'explain', 'debug', 'search',
            'answer-questions', 'context-aware', 'web-search'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Phind

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - suffix: Code after cursor
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - include_search: Include web search results
                - context: Additional context about the task

        Returns:
            Dict with completions and metadata
        """
        suffix = kwargs.get("suffix", "")
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        include_search = kwargs.get("include_search", self.include_search)
        context = kwargs.get("context", "")

        try:
            if not self.api_key:
                # Phind has a public web interface, so we can fallback to direct completion
                return self._complete_without_api(code, suffix, language, temperature, max_tokens)

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Build prompt
            prompt = self._build_completion_prompt(code, suffix, language, context)

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Phind, an expert AI coding assistant. Provide concise, accurate code completions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "search": include_search
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completion_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Extract code from response
                completion_text = self._extract_code(completion_text, language)

                return {
                    "completions": [
                        {
                            "text": completion_text,
                            "score": 1.0
                        }
                    ],
                    "language": language,
                    "provider": "phind",
                    "model": self.model,
                    "search_used": include_search
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your Phind API key.",
                    "completions": [],
                    "provider": "phind"
                }
            elif response.status_code == 429:
                return {
                    "error": "Rate limit exceeded. Please try again later.",
                    "completions": [],
                    "provider": "phind"
                }
            else:
                # Fallback to non-API completion
                return self._complete_without_api(code, suffix, language, temperature, max_tokens)

        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout. Phind API may be slow or unavailable.",
                "completions": [],
                "provider": "phind"
            }
        except Exception as e:
            # Fallback to non-API completion
            return self._complete_without_api(code, suffix, language, temperature, max_tokens)

    def _complete_without_api(self, code: str, suffix: str, language: str,
                             temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Provide a helpful response when API is not available"""
        return {
            "error": "Phind API key not provided. Visit https://www.phind.com to use the web interface.",
            "completions": [],
            "provider": "phind",
            "message": "Phind is primarily a web-based tool. For API access, contact Phind for API credentials."
        }

    def _build_completion_prompt(self, code: str, suffix: str, language: str, context: str) -> str:
        """Build completion prompt"""
        prompt = f"Complete this {language} code:\n\n```{language}\n{code}"

        if suffix:
            prompt += f"\n\n// ... code continues with ...\n{suffix[:100]}"

        prompt += "\n```"

        if context:
            prompt += f"\n\nContext: {context}"

        prompt += "\n\nProvide only the code completion, no explanation."

        return prompt

    def _extract_code(self, text: str, language: str) -> str:
        """Extract code from markdown code blocks"""
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

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Phind

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Explanation string
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            prompt = f"Explain in detail what this {language} code does:\n\n```{language}\n{code}\n```"

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Phind, an expert AI coding assistant. Provide clear, detailed code explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
                "search": self.include_search
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
                return f"Visit https://www.phind.com and paste your code for an explanation. API access may be limited."

        except Exception as e:
            return f"Visit https://www.phind.com and paste your code for an explanation."

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Phind

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fix
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            prompt = f"""Debug this {language} code with the following error:

Error: {error}

Code:
```{language}
{code}
```

Provide the corrected code with a detailed explanation of the fix."""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Phind, an expert debugging assistant. Fix bugs and explain solutions clearly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1024,
                "search": True  # Enable search for debugging help
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
                    "provider": "phind",
                    "model": self.model
                }
            else:
                return {
                    "suggestion": "",
                    "error": "Visit https://www.phind.com to debug your code. API access may be limited.",
                    "provider": "phind"
                }

        except Exception as e:
            return {
                "suggestion": "",
                "error": "Visit https://www.phind.com to debug your code.",
                "provider": "phind"
            }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Phind

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - test_framework: Testing framework (pytest, unittest, jest, junit)

        Returns:
            Generated tests string
        """
        framework = kwargs.get("test_framework", self._get_default_test_framework(language))

        try:
            headers = {
                "Content-Type": "application/json"
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            prompt = f"""Generate comprehensive {framework} tests for this {language} code:

```{language}
{code}
```

Requirements:
- Test normal behavior and edge cases
- Include error handling tests
- Use descriptive test names
- Add helpful documentation
- Follow {framework} best practices"""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Phind, an expert test generation assistant. Generate thorough, well-documented tests."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2048,
                "search": self.include_search
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
                return self._extract_code(tests, language)
            else:
                return f"# Visit https://www.phind.com to generate tests. API access may be limited."

        except Exception as e:
            return f"# Visit https://www.phind.com to generate tests."

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
        Check if Phind service is available

        Returns:
            True if service is accessible
        """
        try:
            # Check if API endpoint is accessible
            response = requests.get(
                "https://www.phind.com",
                timeout=10
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
            "name": "Phind",
            "provider": "phind",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": False,
            "auth_type": "optional_api_key",
            "api_base": self.api_base,
            "web_interface": "https://www.phind.com",
            "open_source": False,
            "description": "AI-powered search engine and coding assistant for developers",
            "note": "Primarily web-based. API access may require special arrangement."
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize Phind
    phind = Phind()

    # Get info
    info = phind.get_info()
    print("Phind Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if phind.is_available():
        print("\nPhind service is available")

        # Test completion
        code = "def heap_sort(arr):\n    "
        result = phind.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test explanation
        sample_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        explanation = phind.explain(sample_code, "python")
        print("\nCode explanation:")
        print(explanation)
    else:
        print("\nPhind service check failed.")
        print("Visit https://www.phind.com to use the web interface.")
