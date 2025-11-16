"""
Google Code Assist Code Model Integration

Google Code Assist (formerly Duet AI) is Google Cloud's AI-powered code assistant
providing intelligent code completion, generation, and analysis powered by PaLM 2 and Codey.
"""

import os
import json
import uuid
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta


class GoogleCodeAssist:
    """
    Google Code Assist - AI-powered code assistant from Google Cloud

    Uses Google Cloud's Vertex AI and PaLM 2 Codey models for code assistance.
    Provides enterprise-grade code completion, chat, and analysis.

    Supported languages: Python, Java, JavaScript, TypeScript, Go, C++, and 20+ more
    Features: autocomplete, chat, explain, generate-tests, fix-bugs, code-review
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Google Code Assist client

        Args:
            api_key: Google Cloud API key (or set GOOGLE_API_KEY/GOOGLE_CLOUD_KEY env var)
            **kwargs: Additional configuration options
                - project_id: GCP project ID (required for some features)
                - region: GCP region (default: us-central1)
                - model: Model to use (default: code-bison)
                - timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_CLOUD_KEY")
        self.project_id = kwargs.get("project_id", os.getenv("GOOGLE_PROJECT_ID", ""))
        self.region = kwargs.get("region", "us-central1")
        self.model = kwargs.get("model", "code-bison")
        self.timeout = kwargs.get("timeout", 30)
        self.provider = "google"
        self.session_id = str(uuid.uuid4())

        # API endpoints
        self.api_base = kwargs.get("api_base", "https://generativelanguage.googleapis.com")
        self.vertex_api = f"https://{self.region}-aiplatform.googleapis.com"

        # Comprehensive language support
        self.supported_languages = [
            'python', 'java', 'javascript', 'typescript', 'go', 'cpp', 'c',
            'csharp', 'php', 'ruby', 'kotlin', 'swift', 'rust', 'scala',
            'sql', 'html', 'css', 'yaml', 'json', 'shell', 'r', 'dart'
        ]

        self.features = [
            'autocomplete', 'chat', 'explain', 'generate-tests', 'fix-bugs',
            'generate-docs', 'code-review', 'security-scan', 'optimize'
        ]

        # Model capabilities
        self.model_info = {
            'code-bison': {'max_tokens': 1024, 'context_window': 6144},
            'code-gecko': {'max_tokens': 64, 'context_window': 2048},
            'codechat-bison': {'max_tokens': 1024, 'context_window': 6144}
        }

        # Token cache for OAuth
        self._token_cache = None
        self._token_expiry = None

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Google Code Assist

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - max_output_tokens: Maximum tokens to generate (default: 128)
                - temperature: Sampling temperature 0-1 (default: 0.2)
                - suffix: Code after cursor
                - n: Number of completions (default: 3)

        Returns:
            Dict with completions and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required. Set GOOGLE_API_KEY environment variable.",
                "completions": [],
                "provider": "google_code_assist"
            }

        try:
            max_tokens = kwargs.get("max_output_tokens", 128)
            temperature = kwargs.get("temperature", 0.2)
            n = kwargs.get("n", 3)
            suffix = kwargs.get("suffix", "")

            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key
            }

            # Build prompt with context
            prompt = self._build_completion_prompt(code, language, suffix)

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "candidateCount": n,
                    "stopSequences": ["\n\n", "```"]
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_ONLY_HIGH"
                    }
                ]
            }

            response = requests.post(
                f"{self.api_base}/v1beta/models/{self.model}:generateContent",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                for candidate in result.get("candidates", []):
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])

                    if parts:
                        text = parts[0].get("text", "")
                        completions.append({
                            "text": text.strip(),
                            "finish_reason": candidate.get("finishReason", ""),
                            "safety_ratings": candidate.get("safetyRatings", [])
                        })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "google_code_assist",
                    "model": self.model,
                    "usage": result.get("usageMetadata", {})
                }
            elif response.status_code == 401:
                return {
                    "error": "Authentication failed. Check your API key.",
                    "completions": [],
                    "provider": "google_code_assist"
                }
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "google_code_assist"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timed out",
                "completions": [],
                "provider": "google_code_assist"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "google_code_assist"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code with Google Code Assist

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options
                - temperature: Sampling temperature (default: 0.5)
                - max_tokens: Maximum response tokens (default: 2048)

        Returns:
            Dict with response and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required",
                "response": "",
                "provider": "google_code_assist"
            }

        try:
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key
            }

            # Convert messages to Google format
            contents = []
            for msg in messages:
                role = "user" if msg.get("role") in ["user", "system"] else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": kwargs.get("temperature", 0.5),
                    "maxOutputTokens": kwargs.get("max_tokens", 2048),
                    "topP": 0.95,
                    "topK": 40
                }
            }

            # Use codechat model for chat
            chat_model = "codechat-bison" if "chat" not in self.model else self.model

            response = requests.post(
                f"{self.api_base}/v1beta/models/{chat_model}:generateContent",
                headers=headers,
                json=payload,
                timeout=self.timeout * 2
            )

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])

                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    response_text = parts[0].get("text", "") if parts else ""

                    return {
                        "response": response_text,
                        "role": "assistant",
                        "provider": "google_code_assist",
                        "model": chat_model,
                        "usage": result.get("usageMetadata", {}),
                        "safety_ratings": candidates[0].get("safetyRatings", [])
                    }

                return {
                    "error": "No response generated",
                    "response": "",
                    "provider": "google_code_assist"
                }
            else:
                return {
                    "error": f"Chat request failed: {response.status_code}",
                    "message": response.text,
                    "response": "",
                    "provider": "google_code_assist"
                }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "google_code_assist"
            }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Google Code Assist

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Detailed explanation string
        """
        messages = [
            {
                "role": "user",
                "content": f"Explain this {language} code in detail. Focus on what it does, how it works, and any important patterns or best practices:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to explain code: {result.get('error', 'Unknown error')}")

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Google Code Assist

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fixes and explanations
        """
        messages = [
            {
                "role": "user",
                "content": f"Fix this {language} code that has an error. Provide the corrected code and explain what was wrong:\n\nCode:\n```{language}\n{code}\n```\n\nError:\n{error}"
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "google_code_assist",
            "safety_ratings": result.get("safety_ratings", [])
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Google Code Assist

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - framework: Test framework (junit, pytest, jest, etc.)
                - coverage: Target coverage (basic, medium, comprehensive)

        Returns:
            Generated test code
        """
        framework = kwargs.get("framework", self._get_default_test_framework(language))
        coverage = kwargs.get("coverage", "comprehensive")

        messages = [
            {
                "role": "user",
                "content": f"Generate {coverage} {framework} tests for this {language} code. Include setup, teardown, edge cases, and error handling:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate tests: {result.get('error', 'Unknown error')}")

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code using Google Code Assist

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options
                - style: Documentation style (google, numpy, jsdoc, etc.)

        Returns:
            Generated documentation string
        """
        style = kwargs.get("style", self._get_default_doc_style(language))

        messages = [
            {
                "role": "user",
                "content": f"Generate {style}-style documentation for this {language} code. Include description, parameters, return values, and examples:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to generate documentation: {result.get('error', 'Unknown error')}")

    def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Perform code review with Google Code Assist

        Args:
            code: Code to review
            language: Programming language

        Returns:
            Dict with review findings and suggestions
        """
        messages = [
            {
                "role": "user",
                "content": f"Perform a comprehensive code review of this {language} code. Check for:\n- Bugs and errors\n- Security vulnerabilities\n- Performance issues\n- Code style and best practices\n- Potential improvements\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return {
            "review": result.get("response", ""),
            "error": result.get("error"),
            "provider": "google_code_assist",
            "safety_ratings": result.get("safety_ratings", [])
        }

    def optimize_code(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Suggest code optimizations using Google Code Assist

        Args:
            code: Code to optimize
            language: Programming language
            **kwargs: Additional options
                - focus: Optimization focus (performance, memory, readability)

        Returns:
            Dict with optimized code and explanation
        """
        focus = kwargs.get("focus", "performance")

        messages = [
            {
                "role": "user",
                "content": f"Optimize this {language} code for {focus}. Provide the optimized version and explain the improvements:\n\n```{language}\n{code}\n```"
            }
        ]

        result = self.chat(messages)
        return {
            "optimized_code": result.get("response", ""),
            "error": result.get("error"),
            "provider": "google_code_assist"
        }

    def is_available(self) -> bool:
        """
        Check if Google Code Assist service is available

        Returns:
            True if service is accessible and authenticated
        """
        if not self.api_key:
            return False

        try:
            headers = {
                "X-Goog-Api-Key": self.api_key
            }

            response = requests.get(
                f"{self.api_base}/v1beta/models",
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
            "name": "Google Code Assist",
            "provider": "google",
            "version": "1.0.0",
            "model": self.model,
            "project_id": self.project_id,
            "region": self.region,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "model_info": self.model_info.get(self.model, {}),
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "api_key",
            "api_base": self.api_base,
            "session_id": self.session_id,
            "powered_by": "PaLM 2 Codey",
            "integration_platforms": [
                "Google Cloud Console", "Cloud Workstations", "Cloud Shell Editor",
                "VS Code", "JetBrains IDEs", "Colab Enterprise"
            ]
        }

    def _build_completion_prompt(self, code: str, language: str, suffix: str = "") -> str:
        """Build completion prompt with context"""
        prompt = f"Complete the following {language} code:\n\n```{language}\n{code}"
        if suffix:
            prompt += f"\n# ... complete here ...\n{suffix}"
        prompt += "\n```\n\nProvide only the completion code without explanations."
        return prompt

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'java': 'java', 'javascript': 'js', 'typescript': 'ts',
            'go': 'go', 'cpp': 'cpp', 'c': 'c', 'csharp': 'cs', 'php': 'php',
            'ruby': 'rb', 'kotlin': 'kt', 'swift': 'swift', 'rust': 'rs',
            'scala': 'scala', 'sql': 'sql', 'r': 'r', 'dart': 'dart'
        }
        return extensions.get(language.lower(), 'txt')

    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            'python': 'pytest', 'java': 'junit', 'javascript': 'jest',
            'typescript': 'jest', 'go': 'testing', 'cpp': 'googletest',
            'c': 'cunit', 'csharp': 'nunit', 'php': 'phpunit',
            'ruby': 'rspec', 'kotlin': 'junit', 'swift': 'xctest',
            'rust': 'cargo test', 'scala': 'scalatest'
        }
        return frameworks.get(language.lower(), 'unittest')

    def _get_default_doc_style(self, language: str) -> str:
        """Get default documentation style for language"""
        styles = {
            'python': 'google', 'java': 'javadoc', 'javascript': 'jsdoc',
            'typescript': 'jsdoc', 'go': 'godoc', 'cpp': 'doxygen',
            'c': 'doxygen', 'csharp': 'xmldoc', 'php': 'phpdoc',
            'ruby': 'rdoc', 'kotlin': 'kdoc', 'swift': 'markup',
            'rust': 'rustdoc', 'scala': 'scaladoc'
        }
        return styles.get(language.lower(), 'markdown')


# Example usage and testing
if __name__ == "__main__":
    # Initialize Google Code Assist
    google_assist = GoogleCodeAssist()

    # Get info
    info = google_assist.get_info()
    print("Google Code Assist Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if google_assist.is_available():
        print("\nGoogle Code Assist is available")

        # Test completion
        code = "def calculate_factorial(n):\n    "
        result = google_assist.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test explanation
        code_to_explain = """
public int binarySearch(int[] arr, int target) {
    int left = 0, right = arr.length - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
"""
        explanation = google_assist.explain(code_to_explain, language="java")
        print("\nCode explanation:")
        print(explanation)
    else:
        print("\nGoogle Code Assist is not available.")
        print("Set GOOGLE_API_KEY environment variable with your API key.")
