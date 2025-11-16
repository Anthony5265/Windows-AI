"""
Tabnine Code Model Integration

Tabnine is an AI code assistant that provides whole-line and full-function
code completions supporting all programming languages.
"""

import os
import json
import socket
import struct
import requests
from typing import List, Dict, Optional, Any
from pathlib import Path


class Tabnine:
    """
    Tabnine - AI-powered code assistant

    Uses Tabnine's local server or cloud API for code completion.
    Supports all programming languages with AI-powered suggestions.

    Supported languages: All programming languages
    Features: autocomplete, whole-line, full-function, semantic-completion
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Tabnine client

        Args:
            api_key: Tabnine API key (optional, or set TABNINE_API_KEY)
            **kwargs: Additional configuration options
                - use_local: Use local Tabnine process (default: True)
                - api_base: Cloud API endpoint (default: https://api.tabnine.com)
                - port: Local server port (default: 9999)
        """
        self.api_key = api_key or os.getenv("TABNINE_API_KEY")
        self.use_local = kwargs.get("use_local", True)
        self.api_base = kwargs.get("api_base", "https://api.tabnine.com")
        self.port = kwargs.get("port", 9999)
        self.provider = "tabnine"

        # All languages supported
        self.supported_languages = ["all"]

        self.features = [
            'autocomplete', 'whole-line', 'full-function',
            'semantic-completion', 'team-learning'
        ]

        # Try to connect to local Tabnine
        self._local_available = self._check_local_server()

    def complete(self, code: str, language: str = "python", **kwargs) -> Dict[str, Any]:
        """
        Generate code completion

        Args:
            code: Code context/prefix
            language: Programming language
            **kwargs: Additional options
                - cursor_position: Cursor position (default: end)
                - max_results: Maximum completions (default: 5)
                - suffix: Code after cursor

        Returns:
            Dict with completions and metadata
        """
        cursor_position = kwargs.get("cursor_position", len(code))
        max_results = kwargs.get("max_results", 5)
        suffix = kwargs.get("suffix", "")

        if self.use_local and self._local_available:
            return self._complete_local(code, language, cursor_position, suffix, max_results)
        else:
            return self._complete_cloud(code, language, cursor_position, suffix, max_results)

    def _complete_local(self, code: str, language: str, cursor: int, suffix: str, max_results: int) -> Dict[str, Any]:
        """Complete using local Tabnine server"""
        try:
            request = {
                "version": "4.4.0",
                "request": {
                    "Autocomplete": {
                        "before": code,
                        "after": suffix,
                        "filename": f"file.{self._get_extension(language)}",
                        "region_includes_beginning": cursor == 0,
                        "region_includes_end": not suffix,
                        "max_num_results": max_results
                    }
                }
            }

            # Send request to local server
            response = self._send_local_request(request)

            if response and "results" in response:
                completions = []
                for result in response["results"]:
                    completions.append({
                        "text": result.get("new_prefix", ""),
                        "detail": result.get("detail", ""),
                        "kind": result.get("kind", ""),
                        "origin": result.get("origin", "")
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "tabnine",
                    "source": "local"
                }

            return {
                "error": "No results from local server",
                "completions": [],
                "provider": "tabnine"
            }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "tabnine"
            }

    def _complete_cloud(self, code: str, language: str, cursor: int, suffix: str, max_results: int) -> Dict[str, Any]:
        """Complete using cloud API"""
        if not self.api_key:
            return {
                "error": "API key required for cloud completions",
                "completions": [],
                "provider": "tabnine"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "before": code,
                "after": suffix,
                "filename": f"file.{self._get_extension(language)}",
                "max_num_results": max_results
            }

            response = requests.post(
                f"{self.api_base}/v1/autocomplete",
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                completions = []

                for item in result.get("results", []):
                    completions.append({
                        "text": item.get("new_prefix", ""),
                        "detail": item.get("detail", "")
                    })

                return {
                    "completions": completions,
                    "language": language,
                    "provider": "tabnine",
                    "source": "cloud"
                }

            return {
                "error": f"API request failed: {response.status_code}",
                "completions": [],
                "provider": "tabnine"
            }

        except Exception as e:
            return {
                "error": str(e),
                "completions": [],
                "provider": "tabnine"
            }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Chat about code (using Tabnine Chat if available)

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional options

        Returns:
            Dict with response and metadata
        """
        if not self.api_key:
            return {
                "error": "API key required for chat",
                "response": "",
                "provider": "tabnine"
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "messages": messages,
                "model": "tabnine-chat"
            }

            response = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "provider": "tabnine"
                }

            return {
                "error": f"Chat request failed: {response.status_code}",
                "response": "",
                "provider": "tabnine"
            }

        except Exception as e:
            return {
                "error": str(e),
                "response": "",
                "provider": "tabnine"
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
        messages = [
            {"role": "user", "content": f"Explain this {language} code:\n\n{code}"}
        ]

        result = self.chat(messages)
        return result.get("response", f"Failed to explain: {result.get('error', 'Unknown error')}")

    def suggest_fix(self, code: str, error: str, language: str = "python") -> Dict[str, Any]:
        """
        Suggest fixes for buggy code

        Args:
            code: Code with bug
            error: Error message
            language: Programming language

        Returns:
            Dict with suggested fixes
        """
        messages = [
            {
                "role": "user",
                "content": f"Fix this {language} code:\n\nCode:\n{code}\n\nError:\n{error}"
            }
        ]

        result = self.chat(messages)
        return {
            "suggestion": result.get("response", ""),
            "error": result.get("error"),
            "provider": "tabnine"
        }

    def generate_docs(self, code: str, language: str = "python", **kwargs) -> str:
        """
        Generate documentation for code

        Args:
            code: Code to document
            language: Programming language
            **kwargs: Additional options

        Returns:
            Generated documentation string
        """
        messages = [
            {
                "role": "user",
                "content": f"Generate documentation for this {language} code:\n\n{code}"
            }
        ]

        result = self.chat(messages)
        return result.get("response", "Failed to generate documentation")

    def is_available(self) -> bool:
        """
        Check if Tabnine service is available

        Returns:
            True if service is accessible
        """
        if self.use_local:
            return self._check_local_server()
        else:
            return self.api_key is not None

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin metadata and status

        Returns:
            Dict with plugin information
        """
        return {
            "name": "Tabnine",
            "provider": "tabnine",
            "version": "4.4.0",
            "supported_languages": "All",
            "features": self.features,
            "available": self.is_available(),
            "local_server": self._local_available,
            "cloud_api": self.api_key is not None,
            "requires_auth": not self.use_local,
            "auth_type": "api_key"
        }

    def _check_local_server(self) -> bool:
        """Check if local Tabnine server is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except:
            return False

    def _send_local_request(self, request: Dict) -> Optional[Dict]:
        """Send request to local Tabnine server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('localhost', self.port))

            # Encode request
            request_json = json.dumps(request).encode('utf-8')
            size = struct.pack('<I', len(request_json))

            # Send
            sock.sendall(size + request_json)

            # Receive response
            size_data = sock.recv(4)
            if len(size_data) == 4:
                response_size = struct.unpack('<I', size_data)[0]
                response_data = b''

                while len(response_data) < response_size:
                    chunk = sock.recv(min(4096, response_size - len(response_data)))
                    if not chunk:
                        break
                    response_data += chunk

                sock.close()
                return json.loads(response_data.decode('utf-8'))

            sock.close()
            return None

        except Exception:
            return None

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py', 'javascript': 'js', 'typescript': 'ts',
            'java': 'java', 'cpp': 'cpp', 'c': 'c', 'csharp': 'cs',
            'go': 'go', 'rust': 'rs', 'ruby': 'rb', 'php': 'php'
        }
        return extensions.get(language, 'txt')


# Example usage and testing
if __name__ == "__main__":
    # Initialize Tabnine
    tabnine = Tabnine()

    # Get info
    info = tabnine.get_info()
    print("Tabnine Info:")
    print(json.dumps(info, indent=2))

    # Test if available
    if tabnine.is_available():
        print("\nTabnine is available")

        # Test completion
        code = "def fibonacci(n):\n    "
        result = tabnine.complete(code, language="python")
        print("\nCode completion:")
        print(json.dumps(result, indent=2))
    else:
        print("\nTabnine is not available. Install Tabnine or set API key.")
