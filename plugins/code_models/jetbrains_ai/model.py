"""
JetBrains AI Assistant Code Model Integration

JetBrains AI Assistant is an AI-powered coding assistant integrated into JetBrains IDEs,
providing intelligent code completion, refactoring, and code analysis capabilities.
"""

import os
import json
import uuid
import requests
from typing import List, Dict, Optional, Any


class JetBrainsAI:
    """
    JetBrains AI Assistant - AI-powered code assistant for JetBrains IDEs

    Uses JetBrains AI service API for code completion, refactoring, and analysis.
    Available in IntelliJ IDEA, PyCharm, WebStorm, and other JetBrains IDEs.

    Supported languages: Java, Kotlin, Python, JavaScript, TypeScript, Go, PHP, and 40+ more
    Features: autocomplete, chat, explain, refactor, generate-tests, fix-bugs
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize JetBrains AI Assistant client

        Args:
            api_key: JetBrains AI API key (or set JETBRAINS_AI_KEY env var)
            **kwargs: Additional configuration options
                - api_base: Custom API endpoint (default: https://api.jetbrains.com/ai)
                - model: Model to use (default: jetbrains-ai)
                - timeout: Request timeout in seconds (default: 30)
                - organization_id: Organization ID for team subscriptions
        """
        self.api_key = api_key or os.getenv("JETBRAINS_AI_KEY") or os.getenv("JETBRAINS_API_KEY")
        self.api_base = kwargs.get("api_base", "https://api.jetbrains.com/ai")
        self.model = kwargs.get("model", "jetbrains-ai")
        self.timeout = kwargs.get("timeout", 30)
        self.organization_id = kwargs.get("organization_id")
        self.provider = "jetbrains"
        self.session_id = str(uuid.uuid4())

        # Comprehensive language support across JetBrains IDEs
        self.supported_languages = [
            'java', 'kotlin', 'groovy', 'scala', 'python', 'javascript', 'typescript',
            'go', 'rust', 'php', 'ruby', 'cpp', 'c', 'csharp', 'swift', 'objectivec',
            'sql', 'html', 'css', 'xml', 'yaml', 'json', 'markdown', 'shell'
        ]

        self.features = [
            'autocomplete', 'chat', 'explain', 'refactor', 'generate-tests',
            'fix-bugs', 'generate-docs', 'code-review', 'optimize'
        ]

        # IDE-specific capabilities
        self.ide_features = {
            'context_aware': True,
            'project_indexing': True,
            'multi_file_refactoring': True,
            'smart_completion': True
        }

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion suggestions

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - cursor_position: Position in code (default: end)
                - max_completions: Maximum completions (default: 5)
                - suffix: Code after cursor
                - file_path: File path for better context
                - project_context: Project context for better suggestions

        Returns:
            Dict with completions and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required. Set JETBRAINS_AI_KEY environment variable.",
                "completions": [],
                "provider": "jetbrains_ai"
            }

        try:
            cursor_position = kwargs.get("cursor_position", len(code))
            max_completions = kwargs.get("max_completions", 5)
            suffix = kwargs.get("suffix", "")
            file_path = kwargs.get("file_path", f"file.{self._get_extension(language)}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Session-ID": self.session_id,
                "User-Agent": "JetBrains-AI-Client/1.0.0"
            }

            if self.organization_id:
                headers["X-Organization-ID"] = self.organization_id

            payload = {
                "model": self.model,
                "document": {
                    "content": code,
                    "suffix": suffix,
                    "cursor_offset": cursor_position,
                    "language": language,
                    "file_path": file_path
                },
                "parameters": {
                    "max_completions": max_completions,
                    "temperature": kwargs.get("temperature", 0.2),
                    "context_aware": True
                },
                "session_context": {
                    "session_id": self.session_id,
                    "request_id": str(uuid.uuid4())
                }
            }

            # Add project context if provided
            if kwargs.get("project_context"):
                payload["project_context"] = kwargs["project_context"]

            response = requests.post(
                f"{self.api_base}/v1/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                for item in result.get("completions", []):
                    completions.append({
                        "text": item.get("text", ""),
                        "display_text": item.get("display_text", ""),
                        "score": item.get("score", 0.0),
                        "type": item.get("type", "code"),
                        "context": item.get("context", {})
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "jetbrains_ai",
                    "model": self.model,
                    "session_id": self.session_id
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your API key.",
                    "completions": [],
                    "provider": "jetbrains_ai"
                }
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "jetbrains_ai"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timed out",
                "completions": [],
                "provider": "jetbrains_ai"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "jetbrains_ai"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat with JetBrains AI about code

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options
                - temperature: Sampling temperature (default: 0.5)
                - max_tokens: Maximum response tokens (default: 2000)
                - context_files: List of file paths for context

        Returns:
            Dict with response and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required",
                "response": "",
                "provider": "jetbrains_ai"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Session-ID": self.session_id,
                "User-Agent": "JetBrains-AI-Client/1.0.0"
            }

            if self.organization_id:
                headers["X-Organization-ID"] = self.organization_id

            payload = {
                "model": self.model,
                "messages": messages,
                "parameters": {
                    "temperature": kwargs.get("temperature", 0.5),
                    "max_tokens": kwargs.get("max_tokens", 2000)
                },
                "session_context": {
                    "session_id": self.session_id,
                    "request_id": str(uuid.uuid4())
                }
            }

            # Add context files if provided
            if kwargs.get("context_files"):
                payload["context_files"] = kwargs["context_files"]

            response = requests.post(
                f"{self.api_base}/v1/chat",
                headers=headers,
                json=payload,
                timeout=self.timeout * 2
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get("message", {})

                return {
                    "response": message.get("content", ""),
                    "role": message.get("role", "assistant"),
                    "provider": "jetbrains_ai",
                    "model": self.model,
                    "usage": result.get("usage", {}),
                    "suggestions": result.get("suggestions", [])
                }
            else:
                return {
                    "error": f"Chat request failed: {response.status_code}",
                    "message": response.text,
                    "response": "",
                    "provider": "jetbrains_ai"
                }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "jetbrains_ai"
            }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does with JetBrains AI

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Detailed explanation string
        """
        messages = [
            {
                "role": "system",
                "content": "You are JetBrains AI Assistant. Provide clear, concise explanations of code with focus on design patterns and best practices."
            },
            {
                "role": "user",
                "content": f"Explain this {language} code in detail:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to explain code: {result.get('error', 'Unknown error')}")

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using JetBrains AI

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fixes and explanations
        """
        messages = [
            {
                "role": "system",
                "content": "You are JetBrains AI Assistant. Analyze bugs and provide fixes following best practices and language idioms."
            },
            {
                "role": "user",
                "content": f"Fix this {language} code:\n\nCode:\n```{language}\n{code}\n```\n\nError/Issue:\n{error}\n\nProvide the fixed code and explanation of the changes."
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "jetbrains_ai",
            "suggestions": result.get("suggestions", [])
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - framework: Test framework (junit, pytest, jest, etc.)
                - coverage: Target coverage percentage

        Returns:
            Generated test code
        """
        framework = kwargs.get("framework", self._get_default_test_framework(language))
        coverage = kwargs.get("coverage", "high")

        messages = [
            {
                "role": "system",
                "content": f"You are JetBrains AI Assistant. Generate comprehensive {framework} tests with {coverage} coverage."
            },
            {
                "role": "user",
                "content": f"Generate {framework} tests for this {language} code:\n\n```{language}\n{code}\n```\n\nInclude edge cases and error handling."
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate tests: {result.get('error', 'Unknown error')}")

    def refactor(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Suggest code refactoring improvements

        Args:
            code: Code to refactor
            language: Programming language
            **kwargs: Additional options
                - focus: Refactoring focus (performance, readability, maintainability)

        Returns:
            Dict with refactored code and explanation
        """
        focus = kwargs.get("focus", "readability and maintainability")

        messages = [
            {
                "role": "system",
                "content": f"You are JetBrains AI Assistant. Suggest refactoring improvements focused on {focus}."
            },
            {
                "role": "user",
                "content": f"Refactor this {language} code:\n\n```{language}\n{code}\n```\n\nProvide refactored code and explain the improvements."
            }
        ]

        result = self.chat(messages)
        return {
            "refactored_code": result.get("response", ""),
            "error": result.get("error"),
            "provider": "jetbrains_ai"
        }

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options
                - style: Documentation style (javadoc, kdoc, pydoc, jsdoc)

        Returns:
            Generated documentation string
        """
        style = kwargs.get("style", self._get_default_doc_style(language))

        messages = [
            {
                "role": "system",
                "content": f"You are JetBrains AI Assistant. Generate {style}-style documentation."
            },
            {
                "role": "user",
                "content": f"Generate {style} documentation for this {language} code:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate documentation: {result.get('error', 'Unknown error')}")

    def is_available(self) -> bool:
        """
        Check if JetBrains AI service is available

        Returns:
            True if service is accessible and authenticated
        """
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "JetBrains-AI-Client/1.0.0"
            }

            response = requests.get(
                f"{self.api_base}/v1/health",
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
            Dict with comprehensive plugin information
        """
        return {
            "name": "JetBrains AI Assistant",
            "provider": "jetbrains",
            "version": "1.0.0",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "ide_features": self.ide_features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_key",
            "api_base": self.api_base,
            "session_id": self.session_id,
            "ide_support": [
                "IntelliJ IDEA", "PyCharm", "WebStorm", "PhpStorm",
                "GoLand", "RubyMine", "CLion", "Rider", "Android Studio"
            ]
        }

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'java': 'java', 'kotlin': 'kt', 'javascript': 'js',
            'typescript': 'ts', 'go': 'go', 'rust': 'rs', 'php': 'php',
            'ruby': 'rb', 'cpp': 'cpp', 'c': 'c', 'csharp': 'cs',
            'swift': 'swift', 'scala': 'scala', 'groovy': 'groovy'
        }
        return extensions.get(language.lower(), 'txt')

    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            'python': 'pytest', 'java': 'junit', 'kotlin': 'junit',
            'javascript': 'jest', 'typescript': 'jest', 'go': 'testing',
            'rust': 'cargo test', 'php': 'phpunit', 'ruby': 'rspec',
            'csharp': 'xunit', 'swift': 'xctest'
        }
        return frameworks.get(language.lower(), 'unittest')

    def _get_default_doc_style(self, language: str) -> str:
        """Get default documentation style for language"""
        styles = {
            'python': 'google', 'java': 'javadoc', 'kotlin': 'kdoc',
            'javascript': 'jsdoc', 'typescript': 'jsdoc', 'go': 'godoc',
            'rust': 'rustdoc', 'php': 'phpdoc', 'ruby': 'rdoc',
            'csharp': 'xmldoc', 'swift': 'markup'
        }
        return styles.get(language.lower(), 'markdown')


# Example usage and testing
if __name__ == "__main__":
    # Initialize JetBrains AI
    jetbrains_ai = JetBrainsAI()

    # Get info
    info = jetbrains_ai.get_info()
    print("JetBrains AI Assistant Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if jetbrains_ai.is_available():
        print("\nJetBrains AI is available")

        # Test completion
        code = "public class Calculator {\n    public int add("
        result = jetbrains_ai.complete(code, language="java")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test explanation
        code_to_explain = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        explanation = jetbrains_ai.explain(code_to_explain, language="python")
        print("\nCode explanation:")
        print(explanation)
    else:
        print("\nJetBrains AI is not available.")
        print("Set JETBRAINS_AI_KEY environment variable with your API key.")
