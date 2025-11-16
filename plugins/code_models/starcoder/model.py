"""
StarCoder Code Model Integration

StarCoder is an open-source code generation model trained on permissively licensed code
from GitHub. Supports 80+ programming languages with high-quality code completion.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class StarCoder:
    """
    StarCoder - Open-source AI code assistant

    Uses Hugging Face Inference API or self-hosted endpoint for code generation.
    Trained on 80+ programming languages from The Stack dataset.

    Supported languages: Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, PHP, Ruby, and 70+ more
    Features: autocomplete, code-generation, fill-in-middle, explain, fix-bugs
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize StarCoder client

        Args:
            api_key: Hugging Face API token (or set HUGGINGFACE_API_KEY env var)
            **kwargs: Additional configuration options
                - model: Model variant (starcoder, starcoder-base, starcoderbase-1b, starcoderbase-3b, starcoderbase-7b)
                - api_base: Custom API endpoint (default: Hugging Face Inference API)
                - temperature: Sampling temperature (default: 0.2)
                - max_new_tokens: Maximum tokens to generate (default: 256)
        """
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        self.model = kwargs.get("model", "bigcode/starcoder")
        self.api_base = kwargs.get("api_base", "https://api-inference.huggingface.co/models")
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_new_tokens = kwargs.get("max_new_tokens", 256)
        self.provider = "starcoder"

        # Supported programming languages
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
            'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'shell', 'yaml', 'json', 'markdown',
            'julia', 'lua', 'perl', 'haskell', 'elixir', 'clojure'
        ]

        self.features = [
            'autocomplete', 'code-generation', 'fill-in-middle',
            'explain', 'fix-bugs', 'multi-line'
        ]

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - suffix: Code after cursor (for fill-in-middle)
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - num_return_sequences: Number of completions to generate (default: 1)

        Returns:
            Dict with completions and metadata
        """
        suffix = kwargs.get("suffix", "")
        max_tokens = kwargs.get("max_tokens", self.max_new_tokens)
        temperature = kwargs.get("temperature", self.temperature)
        num_sequences = kwargs.get("num_return_sequences", 1)

        try:
            if not self.api_key:
                return {
                    "error": "Hugging Face API key required. Set HUGGINGFACE_API_KEY environment variable.",
                    "completions": [],
                    "provider": "starcoder"
                }

            # Build prompt (use fill-in-middle if suffix provided)
            if suffix:
                prompt = f"<fim_prefix>{code}<fim_suffix>{suffix}<fim_middle>"
            else:
                prompt = code

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.95,
                    "do_sample": temperature > 0,
                    "num_return_sequences": num_sequences,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True
                }
            }

            response = requests.post(
                f"{self.api_base}/{self.model}",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                # Handle both single result and list of results
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and "generated_text" in item:
                            completions.append({
                                "text": item["generated_text"],
                                "score": 1.0
                            })
                elif isinstance(result, dict) and "generated_text" in result:
                    completions.append({
                        "text": result["generated_text"],
                        "score": 1.0
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "starcoder",
                    "model": self.model
                }
            else:
                return {
                    "error": f"API request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "starcoder"
                }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "starcoder"
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
        prompt = f"""# Language: {language}
# Task: Explain the following code

{code}

# Explanation:
"""

        result = self.complete(prompt, language=language, max_tokens=512, temperature=0.3)

        if result.get("completions"):
            return result["completions"][0]["text"].strip()
        else:
            return f"Failed to explain code: {result.get('error', 'Unknown error')}"

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fix
        """
        prompt = f"""# Language: {language}
# Task: Fix the bug in this code

# Buggy code:
{code}

# Error: {error}

# Fixed code:
"""

        result = self.complete(prompt, language=language, max_tokens=512, temperature=0.2)

        return {
            "suggestion": result.get("completions", [{}])[0].get("text", "").strip() if result.get("completions") else "",
            "error": result.get("error"),
            "provider": "starcoder"
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options
                - test_framework: Testing framework (pytest, unittest, jest, junit)

        Returns:
            Generated tests string
        """
        framework = kwargs.get("test_framework", "pytest" if language == "python" else "jest")

        prompt = f"""# Language: {language}
# Task: Generate {framework} tests for the following code

# Code to test:
{code}

# {framework} tests:
"""

        result = self.complete(prompt, language=language, max_tokens=1024, temperature=0.3)

        if result.get("completions"):
            return result["completions"][0]["text"].strip()
        else:
            return f"# Failed to generate tests: {result.get('error', 'Unknown error')}"

    def is_available(self) -> bool:
        """
        Check if StarCoder service is available

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
                f"{self.api_base}/{self.model}",
                headers=headers,
                timeout=10
            )

            return response.status_code in [200, 503]  # 503 means model is loading

        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "StarCoder",
            "provider": "bigcode",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "available": self.is_available(),
            "requires_auth": True,
            "auth_type": "huggingface_token",
            "api_base": self.api_base,
            "open_source": True,
            "license": "BigCode OpenRAIL-M"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize StarCoder
    starcoder = StarCoder()

    # Get info
    info = starcoder.get_info()
    print("StarCoder Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if starcoder.is_available():
        print("\nStarCoder is available")

        # Test completion
        code = "def fibonacci(n):\n    "
        result = starcoder.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nStarCoder is not available. Check your Hugging Face API token.")
        print("Set HUGGINGFACE_API_KEY environment variable with your HF token.")
