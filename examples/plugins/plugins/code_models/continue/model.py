"""
Continue.dev Code Model Integration

Continue is an open-source autopilot for VS Code and JetBrains that connects to any LLM.
It provides context-aware code completion, chat, and refactoring capabilities.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class Continue:
    """
    Continue - Open-source AI autopilot for your IDE

    Continue integrates with multiple LLM providers (OpenAI, Anthropic, local models)
    to provide intelligent code assistance directly in your editor.

    Supported languages: All programming languages
    Features: autocomplete, chat, refactor, explain, fix-bugs, generate-tests
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Continue client

        Args:
            api_key: API key for the LLM provider (or set CONTINUE_API_KEY env var)
            **kwargs: Additional configuration options
                - server_url: Continue server URL (default: http://localhost:65432)
                - model: Model to use (gpt-4, claude-2, codellama, etc.)
                - provider: LLM provider (openai, anthropic, ollama, together)
                - temperature: Sampling temperature (default: 0.2)
                - max_tokens: Maximum tokens to generate (default: 256)
        """
        self.api_key = api_key or os.getenv("CONTINUE_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.server_url = kwargs.get("server_url", "http://localhost:65432")
        self.model = kwargs.get("model", "gpt-4")
        self.provider = kwargs.get("provider", "openai")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 256)
        self.provider_name = "continue"

        # Supported programming languages (all languages)
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown',
            'julia', 'lua', 'perl', 'haskell', 'elixir', 'clojure', 'dart',
            'objective-c', 'groovy', 'coffeescript', 'erlang', 'fsharp', 'vim'
        ]

        self.features = [
            'autocomplete', 'chat', 'refactor', 'explain',
            'fix-bugs', 'generate-tests', 'context-aware', 'multi-model'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Continue

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
            # Build the completion request for Continue server
            headers = {
                "Content-Type": "application/json"
            }

            # Continue uses a specific completion format
            payload = {
                "prefix": code,
                "suffix": suffix,
                "language": language,
                "filepath": file_path,
                "model": self.model,
                "provider": self.provider,
                "temperature": temperature,
                "maxTokens": max_tokens,
                "apiKey": self.api_key
            }

            # Try Continue server endpoint
            response = requests.post(
                f"{self.server_url}/complete",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completions = result.get("completions", [])

                formatted_completions = []
                for comp in completions:
                    if isinstance(comp, str):
                        formatted_completions.append({
                            "text": comp,
                            "score": 1.0
                        })
                    elif isinstance(comp, dict):
                        formatted_completions.append({
                            "text": comp.get("text", ""),
                            "score": comp.get("score", 1.0)
                        })

                return {
                    "completions": formatted_completions,
                    "language": language,
                    "provider": "continue",
                    "model": self.model
                }
            elif response.status_code == 404:
                # Fallback to direct LLM API call
                return self._complete_via_llm(code, suffix, language, temperature, max_tokens)
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "continue"
                }

        except requests.exceptions.ConnectionError:
            # Continue server not running, fallback to direct LLM
            return self._complete_via_llm(code, suffix, language, temperature, max_tokens)
        except requests.exceptions.Timeout:
            return {
                "error": "Request timeout. Continue server may be slow or unavailable.",
                "completions": [],
                "provider": "continue"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "continue"
            }

    def _complete_via_llm(self, code: str, suffix: str, language: str,
                         temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Fallback to direct LLM API call when Continue server is unavailable"""
        if not self.api_key:
            return {
                "error": "API key required. Set CONTINUE_API_KEY or OPENAI_API_KEY environment variable.",
                "completions": [],
                "provider": "continue"
            }

        try:
            # OpenAI-compatible completion
            if self.provider in ["openai", "azure"]:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                prompt = f"Complete this {language} code:\n\n{code}"
                if suffix:
                    prompt += f"\n\n// Code continues with:\n{suffix}"

                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert code completion assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    completion = result["choices"][0]["message"]["content"]
                    return {
                        "completions": [{"text": completion, "score": 1.0}],
                        "language": language,
                        "provider": "continue",
                        "model": self.model
                    }
        except:
            pass

        return {
            "error": "Failed to complete via LLM API. Ensure Continue server is running or API key is set.",
            "completions": [],
            "provider": "continue"
        }

    def _get_file_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go',
            'rust': 'rs', 'ruby': 'rb', 'php': 'php', 'swift': 'swift',
            'kotlin': 'kt', 'scala': 'scala', 'r': 'r', 'dart': 'dart'
        }
        return extensions.get(language.lower(), 'txt')

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Continue

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

            payload = {
                "message": f"Explain what this {language} code does:\n\n```{language}\n{code}\n```",
                "model": self.model,
                "provider": self.provider,
                "apiKey": self.api_key
            }

            response = requests.post(
                f"{self.server_url}/chat",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            elif response.status_code == 404:
                # Fallback to direct explanation
                return self._explain_via_llm(code, language)
            else:
                return f"Failed to explain code: HTTP {response.status_code}"

        except requests.exceptions.ConnectionError:
            return self._explain_via_llm(code, language)
        except Exception as e:
            return f"Failed to explain code: {str(e)}"

    def _explain_via_llm(self, code: str, language: str) -> str:
        """Fallback explanation via direct LLM API"""
        if not self.api_key or self.provider != "openai":
            return "Error: Continue server not running and no OpenAI API key available."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert code explainer."},
                    {"role": "user", "content": f"Explain this {language} code:\n\n```{language}\n{code}\n```"}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except:
            pass

        return "Error: Could not explain code. Ensure Continue server is running."

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Continue

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

            prompt = f"""Fix this {language} code that has the following error:

Error: {error}

Code:
```{language}
{code}
```

Provide the corrected code with explanation."""

            payload = {
                "message": prompt,
                "model": self.model,
                "provider": self.provider,
                "apiKey": self.api_key
            }

            response = requests.post(
                f"{self.server_url}/chat",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                suggestion = result.get("response", "")
                return {
                    "suggestion": suggestion,
                    "provider": "continue",
                    "model": self.model
                }
            elif response.status_code == 404:
                return self._fix_bug_via_llm(code, error, language)
            else:
                return {
                    "suggestion": "",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "provider": "continue"
                }

        except requests.exceptions.ConnectionError:
            return self._fix_bug_via_llm(code, error, language)
        except Exception as e:
            return {
                "suggestion": "",
                "error": str(e),
                "provider": "continue"
            }

    def _fix_bug_via_llm(self, code: str, error: str, language: str) -> Dict[str, Any]:
        """Fallback bug fix via direct LLM API"""
        if not self.api_key or self.provider != "openai":
            return {
                "suggestion": "",
                "error": "Continue server not running and no OpenAI API key available.",
                "provider": "continue"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Fix this {language} code with error: {error}

```{language}
{code}
```"""

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert debugger."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "suggestion": result["choices"][0]["message"]["content"],
                    "provider": "continue",
                    "model": self.model
                }
        except:
            pass

        return {
            "suggestion": "",
            "error": "Could not fix bug. Ensure Continue server is running.",
            "provider": "continue"
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Continue

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

            prompt = f"""Generate comprehensive {framework} tests for this {language} code:

```{language}
{code}
```

Include test cases for:
- Normal behavior
- Edge cases
- Error handling
- Good test names"""

            payload = {
                "message": prompt,
                "model": self.model,
                "provider": self.provider,
                "apiKey": self.api_key
            }

            response = requests.post(
                f"{self.server_url}/chat",
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            elif response.status_code == 404:
                return self._generate_tests_via_llm(code, language, framework)
            else:
                return f"# Failed to generate tests: HTTP {response.status_code}"

        except requests.exceptions.ConnectionError:
            return self._generate_tests_via_llm(code, language, framework)
        except Exception as e:
            return f"# Failed to generate tests: {str(e)}"

    def _generate_tests_via_llm(self, code: str, language: str, framework: str) -> str:
        """Fallback test generation via direct LLM API"""
        if not self.api_key or self.provider != "openai":
            return "# Error: Continue server not running and no OpenAI API key available."

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"Generate {framework} tests for this {language} code:\n\n```{language}\n{code}\n```"

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert test writer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2048
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except:
            pass

        return "# Error: Could not generate tests. Ensure Continue server is running."

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
            'csharp': 'NUnit'
        }
        return frameworks.get(language.lower(), 'unit tests')

    def is_available(self) -> bool:
        """
        Check if Continue service is available

        Returns:
            True if service is accessible
        """
        try:
            # Check if Continue server is running
            response = requests.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            # Check if we have API key for fallback
            return bool(self.api_key)

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Continue",
            "provider": "continue",
            "model": self.model,
            "llm_provider": self.provider,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_key",
            "server_url": self.server_url,
            "open_source": True,
            "description": "Open-source AI autopilot for VS Code and JetBrains",
            "github": "https://github.com/continuedev/continue"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize Continue
    continue_client = Continue()

    # Get info
    info = continue_client.get_info()
    print("Continue Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if continue_client.is_available():
        print("\nContinue is available")

        # Test completion
        code = "def merge_sort(arr):\n    "
        result = continue_client.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nContinue is not available.")
        print("Either start the Continue server or set CONTINUE_API_KEY/OPENAI_API_KEY environment variable.")
