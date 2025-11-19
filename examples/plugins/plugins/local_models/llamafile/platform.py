"""
Llamafile Platform Implementation
Single-file executable LLM server with built-in web UI
"""

import subprocess
import requests
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class LlamafilePlatform:
    """
    Llamafile - Distribute and run LLMs with a single file

    Self-contained executable combining model weights and inference engine
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 8080):
        """
        Initialize Llamafile platform

        Args:
            models_dir: Directory containing llamafiles (default: ~/llamafile/models)
            port: Port for server (default: 8080)
        """
        self.models_dir = Path(models_dir or "~/llamafile/models").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.current_model = None

    def is_installed(self) -> bool:
        """Check if any llamafiles exist"""
        if not self.models_dir.exists():
            return False

        # Check for any llamafile executables
        for item in self.models_dir.iterdir():
            if item.is_file() and self._is_llamafile(item):
                return True

        return False

    def _is_llamafile(self, path: Path) -> bool:
        """Check if file is a llamafile executable"""
        # Llamafiles typically don't have extensions or have .llamafile extension
        if path.suffix in ["", ".llamafile", ".exe"]:
            return True
        return False

    def install(self) -> bool:
        """Install Llamafile (download a model)"""
        print("To use Llamafile, download a .llamafile from:")
        print("https://github.com/Mozilla-Ocho/llamafile#quickstart")
        print(f"Place it in: {self.models_dir}")
        print("\nPopular llamafiles:")
        print("- TinyLlama-1.1B-Chat-v1.0.Q5_K_M.llamafile")
        print("- LLaVA-1.5-7B-q4.llamafile")
        print("- Mistral-7B-Instruct-v0.2.Q5_K_M.llamafile")

        self.models_dir.mkdir(parents=True, exist_ok=True)
        return True

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Start Llamafile server

        Args:
            model: Path or name of llamafile to run

        Returns:
            True if server started successfully
        """
        if self.is_running():
            print("Server already running")
            return True

        # Find model
        if not model:
            models = self.list_models()
            if not models:
                print("No llamafiles found.")
                self.install()
                return False
            model = models[0]

        model_path = self._resolve_model_path(model)
        if not model_path or not model_path.exists():
            print(f"Model not found: {model}")
            return False

        try:
            # Make executable on Unix
            if sys.platform != "win32":
                subprocess.run(["chmod", "+x", str(model_path)], check=True)

            # Start llamafile
            cmd = [str(model_path), "--server", "--port", str(self.port)]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(60):
                if self.is_running():
                    self.current_model = model
                    print(f"Llamafile server started on port {self.port}")
                    print(f"Web UI: http://localhost:{self.port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop Llamafile server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            self.current_model = None
            print("Llamafile server stopped")
            return True
        return False

    def is_running(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """List available llamafiles"""
        if not self.models_dir.exists():
            return []

        models = []
        for item in self.models_dir.iterdir():
            if item.is_file() and self._is_llamafile(item):
                models.append(item.name)

        return sorted(models)

    def _resolve_model_path(self, model_name: str) -> Optional[Path]:
        """Resolve model name to full path"""
        if Path(model_name).exists():
            return Path(model_name)

        model_path = self.models_dir / model_name
        if model_path.exists():
            return model_path

        return None

    def load_model(self, model_name: str) -> bool:
        """
        Load a model (restart server with new model)

        Args:
            model_name: Name of llamafile to load

        Returns:
            True if model loaded successfully
        """
        if self.is_running():
            self.stop_server()

        return self.start_server(model=model_name)

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters (n_predict, temp, etc.)

        Returns:
            Generated text or None if failed
        """
        if not self.is_running():
            print("Server not running. Start server first.")
            return None

        try:
            payload = {
                "prompt": prompt,
                "n_predict": kwargs.get("max_tokens", 200),
                "temperature": kwargs.get("temperature", 0.7),
                "top_k": kwargs.get("top_k", 40),
                "top_p": kwargs.get("top_p", 0.9),
                "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
            }

            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("content", "")

            return None

        except Exception as e:
            print(f"Generation failed: {e}")
            return None

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        Chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Generation parameters

        Returns:
            Assistant response or None if failed
        """
        if not self.is_running():
            print("Server not running. Start server first.")
            return None

        try:
            # Try OpenAI-compatible chat endpoint
            payload = {
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 200),
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Fallback to completion endpoint
            prompt = self._format_chat_prompt(messages)
            return self.generate(prompt, **kwargs)

        except Exception as e:
            print(f"Chat failed: {e}")
            # Fallback to formatted prompt
            prompt = self._format_chat_prompt(messages)
            return self.generate(prompt, **kwargs)

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    def download_model(self, model_name: str) -> bool:
        """
        Download a llamafile

        Args:
            model_name: Model to download

        Returns:
            True if download successful
        """
        try:
            # Map of popular llamafiles
            model_urls = {
                "TinyLlama-1.1B": "https://huggingface.co/jartine/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q5_K_M.llamafile",
                "Mistral-7B": "https://huggingface.co/jartine/Mistral-7B-Instruct-v0.2-llamafile/resolve/main/Mistral-7B-Instruct-v0.2.Q5_K_M.llamafile",
                "LLaVA-1.5": "https://huggingface.co/jartine/llava-v1.5-7B-GGUF/resolve/main/llava-v1.5-7b-q4.llamafile",
            }

            if model_name not in model_urls:
                print(f"Unknown model: {model_name}")
                print(f"Available models: {list(model_urls.keys())}")
                print("\nOr download manually from:")
                print("https://github.com/Mozilla-Ocho/llamafile#other-example-llamafiles")
                return False

            url = model_urls[model_name]
            filename = url.split("/")[-1]
            output_path = self.models_dir / filename

            self.models_dir.mkdir(parents=True, exist_ok=True)

            print(f"Downloading {filename}...")
            print("This may take a while (files are several GB)")

            import urllib.request
            urllib.request.urlretrieve(url, output_path)

            # Make executable on Unix
            if sys.platform != "win32":
                subprocess.run(["chmod", "+x", str(output_path)], check=True)

            print(f"Downloaded {filename}")
            return True

        except Exception as e:
            print(f"Failed to download model: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "Llamafile",
            "full_name": "Llamafile - Single-file LLM Distribution",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "current_model": self.current_model,
            "port": self.port,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "features": ["text_generation", "chat", "web_ui"],
            "web_ui": f"http://localhost:{self.port}" if self.is_running() else None,
        }

    def _get_version(self) -> str:
        """Get platform version"""
        # Llamafile version is embedded in the executable
        # Return "embedded" since it's self-contained
        return "embedded"
