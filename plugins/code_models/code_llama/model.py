"""
Code Llama Code Model Integration

Code Llama is Meta AI's specialized large language model for code generation,
supporting multiple programming languages with advanced code understanding capabilities.
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any


class CodeLlama:
    """
    Code Llama - Meta's AI code generation model

    Uses Code Llama models (7B, 13B, 34B, 70B) via Ollama or HuggingFace for
    code completion, generation, and understanding tasks.

    Supported languages: Python, C++, Java, JavaScript, TypeScript, PHP, Bash, and more
    Features: code-generation, completion, infilling, explain, fix-bugs, refactor
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Code Llama client

        Args:
            api_key: API key for hosted service (or set CODELLAMA_API_KEY env var)
            **kwargs: Additional configuration options
                - model: Model variant (codellama:7b, codellama:13b, codellama:34b, codellama:70b)
                - api_base: API endpoint (default: http://localhost:11434 for Ollama)
                - provider: Service provider (ollama, huggingface, replicate)
                - timeout: Request timeout in seconds (default: 60)
                - temperature: Sampling temperature (default: 0.2)
                - max_tokens: Maximum tokens to generate (default: 512)
        """
        self.api_key = api_key or os.getenv("CODELLAMA_API_KEY")
        self.model = kwargs.get("model", "codellama:7b")
        self.api_base = kwargs.get("api_base", os.getenv("CODELLAMA_API_BASE", "http://localhost:11434"))
        self.provider = kwargs.get("provider", "ollama")
        self.timeout = kwargs.get("timeout", 60)
        self.temperature = kwargs.get("temperature", 0.2)
        self.max_tokens = kwargs.get("max_tokens", 512)

        # Model capabilities and variants
        self.model_variants = {
            'codellama:7b': {'params': '7B', 'context': 16384, 'best_for': 'fast inference'},
            'codellama:13b': {'params': '13B', 'context': 16384, 'best_for': 'balanced'},
            'codellama:34b': {'params': '34B', 'context': 16384, 'best_for': 'quality'},
            'codellama:70b': {'params': '70B', 'context': 16384, 'best_for': 'maximum quality'},
            'codellama-python': {'params': '7B', 'context': 16384, 'best_for': 'python-specific'},
            'codellama-instruct': {'params': '7B', 'context': 16384, 'best_for': 'instruction-following'}
        }

        # Comprehensive language support
        self.supported_languages = [
            'python', 'cpp', 'java', 'javascript', 'typescript', 'php', 'bash',
            'c', 'csharp', 'go', 'rust', 'kotlin', 'swift', 'ruby', 'scala',
            'sql', 'html', 'css', 'json', 'yaml', 'markdown'
        ]

        self.features = [
            'code-generation', 'completion', 'infilling', 'explain',
            'fix-bugs', 'refactor', 'generate-docs', 'translate',
            'optimize', 'generate-tests'
        ]

        # Code Llama-specific capabilities
        self.capabilities = {
            'fill_in_middle': True,  # FIM capability
            'long_context': True,    # 16K context window
            'instruction_following': 'instruct' in self.model,
            'python_specialized': 'python' in self.model
        }

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion using Code Llama

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - suffix: Code after cursor (for fill-in-middle)
                - max_tokens: Maximum tokens to generate
                - temperature: Sampling temperature
                - stop: Stop sequences
                - n: Number of completions

        Returns:
            Dict with completions and metadata
        """
        try:
            suffix = kwargs.get("suffix", "")
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            stop = kwargs.get("stop", ["\n\n", "```"])
            n = kwargs.get("n", 1)

            # Build prompt based on whether we have suffix (FIM mode)
            if suffix and self.capabilities['fill_in_middle']:
                prompt = self._build_fim_prompt(code, suffix, language)
            else:
                prompt = self._build_completion_prompt(code, language)

            if self.provider == "ollama":
                return self._complete_ollama(prompt, max_tokens, temperature, stop, n, language)
            elif self.provider == "huggingface":
                return self._complete_huggingface(prompt, max_tokens, temperature, stop, n, language)
            elif self.provider == "replicate":
                return self._complete_replicate(prompt, max_tokens, temperature, stop, n, language)
            else:
                return {
                    "error": f"Unsupported provider: {self.provider}",
                    "completions": [],
                    "provider": "code_llama"
                }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "code_llama"
            }

    def _complete_ollama(self, prompt: str, max_tokens: int, temperature: float,
                         stop: List[str], n: int, language: str) -> Dict[str, Any]:
        """Complete using Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "stop": stop
                }
            }

            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                completion_text = result.get("response", "")

                return {
                    "completions": [{"text": completion_text}],
                    "language": language,
                    "provider": "code_llama",
                    "model": self.model,
                    "eval_count": result.get("eval_count", 0),
                    "eval_duration": result.get("eval_duration", 0)
                }
            else:
                return {
                    "error": f"Ollama request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "code_llama"
                }

        except requests.exceptions.Timeout:
            return {
                "error": "Request timed out",
                "completions": [],
                "provider": "code_llama"
            }
        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "code_llama"
            }

    def _complete_huggingface(self, prompt: str, max_tokens: int, temperature: float,
                              stop: List[str], n: int, language: str) -> Dict[str, Any]:
        """Complete using HuggingFace API"""
        if not self.api_key:
            return {
                "error": "API key required for HuggingFace",
                "completions": [],
                "provider": "code_llama"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False,
                    "stop_sequences": stop
                }
            }

            response = requests.post(
                f"https://api-inference.huggingface.co/models/codellama/{self.model}",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                if isinstance(result, list):
                    for item in result:
                        completions.append({"text": item.get("generated_text", "")})
                else:
                    completions.append({"text": result.get("generated_text", "")})

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "code_llama",
                    "model": self.model
                }
            else:
                return {
                    "error": f"HuggingFace request failed: {response.status_code}",
                    "message": response.text,
                    "completions": [],
                    "provider": "code_llama"
                }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "code_llama"
            }

    def _complete_replicate(self, prompt: str, max_tokens: int, temperature: float,
                           stop: List[str], n: int, language: str) -> Dict[str, Any]:
        """Complete using Replicate API"""
        if not self.api_key:
            return {
                "error": "API key required for Replicate",
                "completions": [],
                "provider": "code_llama"
            }

        # Replicate implementation would go here
        return {
            "error": "Replicate provider not yet implemented",
            "completions": [],
            "provider": "code_llama"
        }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code with Code Llama

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options

        Returns:
            Dict with response and metadata
        """
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.5),
                    "num_predict": kwargs.get("max_tokens", 2000)
                }
            }

            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                timeout=self.timeout * 2
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "provider": "code_llama",
                    "model": self.model
                }
            else:
                return {
                    "error": f"Request failed: {response.status_code}",
                    "response": "",
                    "provider": "code_llama"
                }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "code_llama"
            }

    def explain(self, code: str, language: str = "python") -> str:
        """
        Explain what code does using Code Llama

        Args:
            code: Code to explain
            language: Programming language

        Returns:
            Detailed explanation string
        """
        prompt = f"""Explain this {language} code in detail:

```{language}
{code}
```

Provide a clear explanation of what this code does, how it works, and any important concepts."""

        result = self.complete(prompt, language=language, max_tokens=1000)
        completions = result.get("completions", [])
        return completions[0].get("text", "") if completions else f"Failed to explain: {result.get('error', 'Unknown error')}"

    def fix_bug(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code using Code Llama

        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language

        Returns:
            Dict with suggested fixes
        """
        prompt = f"""Fix this {language} code that has an error:

Code:
```{language}
{code}
```

Error:
{error}

Provide the fixed code and explain what was wrong."""

        result = self.complete(prompt, language=language, max_tokens=1500)
        completions = result.get("completions", [])

        return {
            "suggestion": completions[0].get("text", "") if completions else "",
            "error": result.get("error"),
            "provider": "code_llama"
        }

    def generate_tests(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate unit tests for code using Code Llama

        Args:
            code: Code to test
            language: Programming language
            **kwargs: Additional options

        Returns:
            Generated test code
        """
        framework = kwargs.get("framework", self._get_default_test_framework(language))

        prompt = f"""Generate comprehensive {framework} unit tests for this {language} code:

```{language}
{code}
```

Include edge cases, error handling, and proper test structure."""

        result = self.complete(prompt, language=language, max_tokens=2000)
        completions = result.get("completions", [])
        return completions[0].get("text", "") if completions else f"Failed to generate tests: {result.get('error', 'Unknown error')}"

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code using Code Llama

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options

        Returns:
            Generated documentation string
        """
        style = kwargs.get("style", self._get_default_doc_style(language))

        prompt = f"""Generate {style}-style documentation for this {language} code:

```{language}
{code}
```

Include description, parameters, return values, and examples."""

        result = self.complete(prompt, language=language, max_tokens=1000)
        completions = result.get("completions", [])
        return completions[0].get("text", "") if completions else f"Failed to generate docs: {result.get('error', 'Unknown error')}"

    def refactor(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Suggest code refactoring improvements

        Args:
            code: Code to refactor
            language: Programming language
            **kwargs: Additional options

        Returns:
            Dict with refactored code and explanation
        """
        focus = kwargs.get("focus", "readability and performance")

        prompt = f"""Refactor this {language} code for improved {focus}:

```{language}
{code}
```

Provide the refactored code and explain the improvements."""

        result = self.complete(prompt, language=language, max_tokens=2000)
        completions = result.get("completions", [])

        return {
            "refactored_code": completions[0].get("text", "") if completions else "",
            "error": result.get("error"),
            "provider": "code_llama"
        }

    def translate(self, code: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
        """
        Translate code from one language to another

        Args:
            code: Code to translate
            from_lang: Source language
            to_lang: Target language

        Returns:
            Dict with translated code
        """
        prompt = f"""Translate this {from_lang} code to {to_lang}:

```{from_lang}
{code}
```

Provide only the translated {to_lang} code with equivalent functionality."""

        result = self.complete(prompt, language=to_lang, max_tokens=2000)
        completions = result.get("completions", [])

        return {
            "translated_code": completions[0].get("text", "") if completions else "",
            "from_language": from_lang,
            "to_language": to_lang,
            "error": result.get("error"),
            "provider": "code_llama"
        }

    def is_available(self) -> bool:
        """
        Check if Code Llama service is available

        Returns:
            True if service is accessible
        """
        try:
            if self.provider == "ollama":
                response = requests.get(f"{self.api_base}/api/tags", timeout=5)
                return response.status_code == 200
            elif self.provider == "huggingface":
                return bool(self.api_key)
            else:
                return False
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with comprehensive plugin information
        """
        model_info = self.model_variants.get(self.model, {})

        return {
            "name": "Code Llama",
            "provider": "meta",
            "version": "1.0.0",
            "model": self.model,
            "model_info": model_info,
            "api_base": self.api_base,
            "service_provider": self.provider,
            "supported_languages": self.supported_languages,
            "features": self.features,
            "capabilities": self.capabilities,
            "available": self.is_available(),
            "requires_auth": self.provider in ["huggingface", "replicate"],
            "auth_type": "api_key" if self.provider != "ollama" else "none",
            "model_variants": list(self.model_variants.keys()),
            "context_window": model_info.get("context", 16384),
            "developed_by": "Meta AI",
            "license": "Custom Meta License"
        }

    def _build_completion_prompt(self, code: str, language: str) -> str:
        """Build standard completion prompt"""
        return f"<｜begin▁of▁sentence｜>{code}"

    def _build_fim_prompt(self, prefix: str, suffix: str, language: str) -> str:
        """Build Fill-in-Middle (FIM) prompt"""
        return f"<｜fim▁begin｜>{prefix}<｜fim▁hole｜>{suffix}<｜fim▁end｜>"

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to Code Llama prompt format"""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        prompt += "Assistant: "
        return prompt

    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            'python': 'pytest', 'java': 'junit', 'javascript': 'jest',
            'typescript': 'jest', 'cpp': 'googletest', 'c': 'cunit',
            'csharp': 'nunit', 'go': 'testing', 'rust': 'cargo test',
            'kotlin': 'junit', 'swift': 'xctest', 'ruby': 'rspec',
            'php': 'phpunit', 'scala': 'scalatest'
        }
        return frameworks.get(language.lower(), 'unittest')

    def _get_default_doc_style(self, language: str) -> str:
        """Get default documentation style for language"""
        styles = {
            'python': 'google', 'java': 'javadoc', 'javascript': 'jsdoc',
            'typescript': 'jsdoc', 'cpp': 'doxygen', 'c': 'doxygen',
            'csharp': 'xmldoc', 'go': 'godoc', 'rust': 'rustdoc',
            'kotlin': 'kdoc', 'swift': 'markup', 'ruby': 'rdoc',
            'php': 'phpdoc', 'scala': 'scaladoc'
        }
        return styles.get(language.lower(), 'markdown')


# Example usage and testing
if __name__ == "__main__":
    # Initialize Code Llama
    model = CodeLlama()

    # Get info
    info = model.get_info()
    print("Code Llama Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if model.is_available():
        print("\nCode Llama is available")

        # Test completion
        code = "def fibonacci(n):\n    "
        result = model.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))

        # Test explanation
        code_to_explain = """
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
"""
        explanation = model.explain(code_to_explain, language="python")
        print("\nCode explanation:")
        print(explanation)

        # Test translation
        py_code = "print('Hello, World!')"
        translation = model.translate(py_code, "python", "javascript")
        print("\nCode translation:")
        print(translation)
    else:
        print("\nCode Llama is not available.")
        print("Make sure Ollama is running with Code Llama installed:")
        print("  ollama pull codellama")
        print("  ollama serve")
