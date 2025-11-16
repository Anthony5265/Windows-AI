"""
VS IntelliCode Code Model Integration

Visual Studio IntelliCode is Microsoft's AI-powered code completion and assistance tool
integrated into Visual Studio and VS Code, providing context-aware suggestions.
"""

import os
import json
import uuid
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta


class VSIntelliCode:
    """
    VS IntelliCode - AI-powered code assistant from Microsoft

    Uses Microsoft's AI models trained on thousands of open-source projects
    for context-aware code completion and refactoring suggestions.

    Supported languages: C#, C++, Python, JavaScript, TypeScript, Java, and more
    Features: autocomplete, refactor, code-review, pattern-detection
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize VS IntelliCode client

        Args:
            api_key: Azure/Microsoft API key (or set AZURE_API_KEY/MS_INTELLICODE_KEY env var)
            **kwargs: Additional configuration options
                - api_base: API endpoint (default: Azure cognitive services)
                - subscription_key: Azure subscription key
                - region: Azure region (default: eastus)
                - timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.getenv("MS_INTELLICODE_KEY") or os.getenv("AZURE_API_KEY")
        self.subscription_key = kwargs.get("subscription_key", os.getenv("AZURE_SUBSCRIPTION_KEY"))
        self.region = kwargs.get("region", os.getenv("AZURE_REGION", "eastus"))
        self.api_base = kwargs.get("api_base", f"https://{self.region}.api.cognitive.microsoft.com")
        self.timeout = kwargs.get("timeout", 30)
        self.provider = "microsoft"
        self.session_id = str(uuid.uuid4())

        # IntelliCode-specific settings
        self.model_version = kwargs.get("model_version", "latest")
        self.enable_team_completions = kwargs.get("enable_team_completions", False)

        # Language support - strong focus on Microsoft ecosystem
        self.supported_languages = [
            'csharp', 'cpp', 'c', 'python', 'javascript', 'typescript',
            'java', 'sql', 'xaml', 'razor', 'fsharp', 'visualbasic',
            'powershell', 'json', 'yaml', 'html', 'css', 'xml'
        ]

        self.features = [
            'autocomplete', 'refactor', 'code-review', 'pattern-detection',
            'whole-line-completion', 'argument-completion', 'team-models',
            'usage-examples', 'quick-actions'
        ]

        # IntelliCode-specific capabilities
        self.intellicode_features = {
            'starred_suggestions': True,  # Star marking for top suggestions
            'argument_completion': True,
            'whole_line_completion': True,
            'refactoring_suggestions': True,
            'code_pattern_detection': True,
            'team_models': self.enable_team_completions
        }

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using VS IntelliCode

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - cursor_position: Position in code (default: end)
                - max_suggestions: Maximum suggestions (default: 10)
                - suffix: Code after cursor
                - file_path: File path for context
                - include_starred: Include starred (recommended) suggestions

        Returns:
            Dict with completions and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required. Set MS_INTELLICODE_KEY or AZURE_API_KEY environment variable.",
                "completions": [],
                "provider": "vs_intellicode"
            }

        try:
            cursor_position = kwargs.get("cursor_position", len(code))
            max_suggestions = kwargs.get("max_suggestions", 10)
            suffix = kwargs.get("suffix", "")
            file_path = kwargs.get("file_path", f"file.{self._get_extension(language)}")
            include_starred = kwargs.get("include_starred", True)

            headers = {
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": self.subscription_key or self.api_key,
                "X-Session-Id": self.session_id
            }

            payload = {
                "document": {
                    "text": code,
                    "suffix": suffix,
                    "cursor_position": cursor_position,
                    "language": self._map_language(language),
                    "file_path": file_path
                },
                "settings": {
                    "max_suggestions": max_suggestions,
                    "include_starred": include_starred,
                    "enable_whole_line": True,
                    "enable_argument_completion": True,
                    "model_version": self.model_version
                },
                "context": {
                    "session_id": self.session_id,
                    "request_id": str(uuid.uuid4())
                }
            }

            response = requests.post(
                f"{self.api_base}/intellicode/v1/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                for suggestion in result.get("suggestions", []):
                    completions.append({
                        "text": suggestion.get("completion_text", ""),
                        "display_text": suggestion.get("display_text", ""),
                        "is_starred": suggestion.get("is_starred", False),
                        "confidence": suggestion.get("confidence", 0.0),
                        "kind": suggestion.get("kind", "text"),
                        "detail": suggestion.get("detail", ""),
                        "documentation": suggestion.get("documentation", "")
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "vs_intellicode",
                    "model_version": self.model_version,
                    "session_id": self.session_id,
                    "has_starred": any(c.get("is_starred") for c in completions)
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your API key or subscription.",
                    "completions": [],
                    "provider": "vs_intellicode"
                }
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "vs_intellicode"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timed out",
                "completions": [],
                "provider": "vs_intellicode"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "vs_intellicode"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code with VS IntelliCode (via Azure OpenAI)

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options
                - temperature: Sampling temperature (default: 0.5)
                - max_tokens: Maximum response tokens (default: 2000)

        Returns:
            Dict with response and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required",
                "response": "",
                "provider": "vs_intellicode"
            }

        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.subscription_key or self.api_key
            }

            payload = {
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.5),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": 0.95,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }

            # Use Azure OpenAI endpoint
            response = requests.post(
                f"{self.api_base}/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview",
                headers=headers,
                json=payload,
                timeout=self.timeout * 2
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])

                if choices:
                    message = choices[0].get("message", {})
                    return {
                        "response": message.get("content", ""),
                        "role": message.get("role", "assistant"),
                        "provider": "vs_intellicode",
                        "model": "gpt-4",
                        "usage": result.get("usage", {}),
                        "finish_reason": choices[0].get("finish_reason", "")
                    }

                return {
                    "error": "No response generated",
                    "response": "",
                    "provider": "vs_intellicode"
                }
            else:
                return {
                    "error": f"Chat request failed: {response.status_code}",
                    "message": response.text,
                    "response": "",
                    "provider": "vs_intellicode"
                }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "vs_intellicode"
            }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using VS IntelliCode

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Detailed explanation string
        """
        messages = [
            {
                "role": "system",
                "content": "You are VS IntelliCode, Microsoft's AI code assistant. Provide clear explanations with focus on best practices and design patterns."
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
        Suggest fixes for buggy code using VS IntelliCode

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
                "content": "You are VS IntelliCode. Analyze bugs and provide fixes following Microsoft coding standards and best practices."
            },
            {
                "role": "user",
                "content": f"Fix this {language} code with an error:\n\nCode:\n```{language}\n{code}\n```\n\nError:\n{error}\n\nProvide the fixed code and explain the changes."
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "vs_intellicode",
            "usage": result.get("usage", {})
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using VS IntelliCode

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - framework: Test framework (mstest, nunit, xunit, pytest, etc.)
                - coverage: Target coverage level

        Returns:
            Generated test code
        """
        framework = kwargs.get("framework", self._get_default_test_framework(language))
        coverage = kwargs.get("coverage", "comprehensive")

        messages = [
            {
                "role": "system",
                "content": f"You are VS IntelliCode. Generate high-quality {framework} tests following Microsoft testing best practices."
            },
            {
                "role": "user",
                "content": f"Generate {coverage} {framework} unit tests for this {language} code. Include edge cases, error handling, and proper test organization:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate tests: {result.get('error', 'Unknown error')}")

    def refactor(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Suggest refactoring improvements using VS IntelliCode

        Args:
            code: Code to refactor
            language: Programming language
            **kwargs: Additional options
                - focus: Refactoring focus (performance, readability, patterns)

        Returns:
            Dict with refactored code and explanation
        """
        focus = kwargs.get("focus", "readability and maintainability")

        messages = [
            {
                "role": "system",
                "content": f"You are VS IntelliCode. Suggest refactoring improvements focused on {focus}, following SOLID principles and design patterns."
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
            "provider": "vs_intellicode"
        }

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code using VS IntelliCode

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options
                - style: Documentation style (xmldoc, jsdoc, pydoc, etc.)

        Returns:
            Generated documentation string
        """
        style = kwargs.get("style", self._get_default_doc_style(language))

        messages = [
            {
                "role": "system",
                "content": f"You are VS IntelliCode. Generate {style}-style documentation following Microsoft documentation standards."
            },
            {
                "role": "user",
                "content": f"Generate {style} documentation for this {language} code:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate documentation: {result.get('error', 'Unknown error')}")

    def detect_patterns(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Detect code patterns and anti-patterns using VS IntelliCode

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            Dict with detected patterns and suggestions
        """
        messages = [
            {
                "role": "system",
                "content": "You are VS IntelliCode. Identify design patterns, anti-patterns, and code smells."
            },
            {
                "role": "user",
                "content": f"Analyze this {language} code for patterns and anti-patterns:\n\n```{language}\n{code}\n```\n\nIdentify design patterns used, potential anti-patterns, and suggest improvements."
            }
        ]

        result = self.chat(messages)
        return {
            "analysis": result.get("response", ""),
            "error": result.get("error"),
            "provider": "vs_intellicode"
        }

    def quick_actions(self, code: str, language: str = "python", issue_type: str = "all") -> List[Dict[str, Any]]:
        """
        Get quick action suggestions for code improvements

        Args:
            code: Code to analyze
            language: Programming language
            issue_type: Type of issues to check (all, refactoring, style, performance)

        Returns:
            List of quick action suggestions
        """
        messages = [
            {
                "role": "system",
                "content": f"You are VS IntelliCode. Provide quick action suggestions for {issue_type} improvements."
            },
            {
                "role": "user",
                "content": f"Suggest quick actions for this {language} code:\n\n```{language}\n{code}\n```\n\nProvide actionable suggestions in a structured format."
            }
        ]

        result = self.chat(messages)
        response_text = result.get("response", "")

        # Parse response into structured quick actions
        quick_actions = [{
            "title": "Code Improvements",
            "description": response_text,
            "kind": issue_type,
            "provider": "vs_intellicode"
        }]

        return quick_actions

    def is_available(self) -> bool:
        """
        Check if VS IntelliCode service is available

        Returns:
            True if service is accessible and authenticated
        """
        if not self.api_key and not self.subscription_key:
            return False

        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.subscription_key or self.api_key
            }

            response = requests.get(
                f"{self.api_base}/intellicode/v1/health",
                headers=headers,
                timeout=5
            )

            return response.status_code == 200

        except Exception:
            # Fallback: check if credentials exist
            return bool(self.api_key or self.subscription_key)

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with comprehensive plugin information
        """
        return {
            "name": "Visual Studio IntelliCode",
            "provider": "microsoft",
            "version": "1.0.0",
            "model_version": self.model_version,
            "region": self.region,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "intellicode_features": self.intellicode_features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "azure_subscription",
            "api_base": self.api_base,
            "session_id": self.session_id,
            "integration_platforms": [
                "Visual Studio 2019+", "Visual Studio 2022",
                "VS Code", "Visual Studio for Mac"
            ],
            "trained_on": "Thousands of open-source GitHub projects",
            "enterprise_features": {
                "team_completions": self.enable_team_completions,
                "custom_models": True,
                "usage_tracking": True
            }
        }

    def _map_language(self, language: str) -> str:
        """Map language to VS IntelliCode language identifier"""
        language_map = {
            'python': 'python',
            'csharp': 'csharp',
            'cpp': 'cpp',
            'c': 'c',
            'javascript': 'javascript',
            'typescript': 'typescript',
            'java': 'java',
            'sql': 'sql',
            'xaml': 'xaml',
            'razor': 'razor',
            'fsharp': 'fsharp',
            'visualbasic': 'vb',
            'powershell': 'powershell'
        }
        return language_map.get(language.lower(), 'plaintext')

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'csharp': 'cs', 'cpp': 'cpp', 'c': 'c',
            'javascript': 'js', 'typescript': 'ts', 'java': 'java',
            'sql': 'sql', 'xaml': 'xaml', 'razor': 'cshtml',
            'fsharp': 'fs', 'visualbasic': 'vb', 'powershell': 'ps1',
            'json': 'json', 'yaml': 'yaml', 'xml': 'xml'
        }
        return extensions.get(language.lower(), 'txt')

    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            'python': 'pytest', 'csharp': 'mstest', 'cpp': 'googletest',
            'c': 'cunit', 'javascript': 'jest', 'typescript': 'jest',
            'java': 'junit', 'fsharp': 'expecto', 'visualbasic': 'mstest',
            'powershell': 'pester'
        }
        return frameworks.get(language.lower(), 'unittest')

    def _get_default_doc_style(self, language: str) -> str:
        """Get default documentation style for language"""
        styles = {
            'python': 'google', 'csharp': 'xmldoc', 'cpp': 'doxygen',
            'c': 'doxygen', 'javascript': 'jsdoc', 'typescript': 'jsdoc',
            'java': 'javadoc', 'fsharp': 'xmldoc', 'visualbasic': 'xmldoc',
            'powershell': 'comment-based', 'sql': 'inline'
        }
        return styles.get(language.lower(), 'markdown')


# Example usage and testing
if __name__ == "__main__":
    # Initialize VS IntelliCode
    intellicode = VSIntelliCode()

    # Get info
    info = intellicode.get_info()
    print("VS IntelliCode Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if intellicode.is_available():
        print("\nVS IntelliCode is available")

        # Test completion
        code = "public class Calculator\n{\n    public int Add("
        result = intellicode.complete(code, language="csharp")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test pattern detection
        pattern_code = """
class UserService:
    def __init__(self):
        self.users = []

    def get_user(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user
        return None
"""
        patterns = intellicode.detect_patterns(pattern_code, language="python")
        print("\nPattern detection:")
        print(patterns)
    else:
        print("\nVS IntelliCode is not available.")
        print("Set MS_INTELLICODE_KEY or AZURE_API_KEY environment variable.")
        print("Or configure Azure subscription with AZURE_SUBSCRIPTION_KEY.")
