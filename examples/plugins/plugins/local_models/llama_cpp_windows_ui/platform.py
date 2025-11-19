"""
LLaMA.cpp Windows UI Platform Implementation
Windows GUI application for running llama.cpp models with a user-friendly interface
"""

import subprocess
import requests
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class LlamaCppWindowsUIPlatform:
    """
    LLaMA.cpp Windows UI - User-friendly Windows interface for llama.cpp

    Provides a GUI application for running GGML/GGUF models on Windows
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 8080):
        """
        Initialize LLaMA.cpp Windows UI platform

        Args:
            models_dir: Directory containing models (default: ~/llama-cpp-ui/models)
            port: Port for API server (default: 8080)
        """
        self.models_dir = Path(models_dir or "~/llama-cpp-ui/models").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.install_dir = Path("~/llama-cpp-ui").expanduser()
        self.executable = self.install_dir / "llama-cpp-ui.exe" if sys.platform == "win32" else self.install_dir / "llama-cpp-ui"

    def is_installed(self) -> bool:
        """Check if LLaMA.cpp Windows UI is installed"""
        return self.install_dir.exists() and self.executable.exists()

    def install(self) -> bool:
        """Install LLaMA.cpp Windows UI"""
        print("Installing LLaMA.cpp Windows UI...")

        if sys.platform != "win32":
            print("Note: This platform is primarily designed for Windows.")
            print("Consider using the regular llama.cpp platform instead.")

        try:
            # Create directories
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("\nPlease download LLaMA.cpp Windows UI from:")
            print("https://github.com/ggerganov/llama.cpp/releases")
            print("\nOr download a pre-built Windows UI from:")
            print("https://github.com/ggerganov/llama.cpp")
            print(f"\nExtract to: {self.install_dir}")
            print(f"Place models in: {self.models_dir}")

            return True

        except Exception as e:
            print(f"Installation setup failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None, threads: int = 4) -> bool:
        """
        Start LLaMA.cpp server

        Args:
            model: Model to load (optional)
            threads: Number of threads (default: 4)

        Returns:
            True if server started successfully
        """
        if not self.is_installed():
            print("LLaMA.cpp Windows UI not installed. Setting up...")
            if not self.install():
                return False

        if self.is_running():
            print("Server already running")
            return True

        # Find model if not specified
        if not model:
            models = self.list_models()
            if not models:
                print("No models found.")
                return False
            model = str(self.models_dir / models[0])
        elif not Path(model).exists():
            model_path = self.models_dir / model
            if model_path.exists():
                model = str(model_path)

        try:
            # Use llama.cpp server executable
            server_exe = self.install_dir / "server.exe" if sys.platform == "win32" else self.install_dir / "server"

            if not server_exe.exists():
                # Try alternate locations
                server_exe = self.install_dir / "llama-server.exe" if sys.platform == "win32" else self.install_dir / "llama-server"

            if not server_exe.exists():
                print(f"Server executable not found at {server_exe}")
                return False

            cmd = [
                str(server_exe),
                "-m", model,
                "-t", str(threads),
                "--port", str(self.port),
                "--host", "0.0.0.0"
            ]

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(30):
                if self.is_running():
                    print(f"LLaMA.cpp server started on port {self.port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop LLaMA.cpp server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("LLaMA.cpp server stopped")
            return True
        return False

    def is_running(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """List available models"""
        if not self.models_dir.exists():
            return []

        models = []
        for item in self.models_dir.iterdir():
            if item.is_file() and item.suffix in [".gguf", ".ggml", ".bin"]:
                models.append(item.name)

        return sorted(models)

    def load_model(self, model_name: str) -> bool:
        """
        Load a model (requires server restart)

        Args:
            model_name: Name of model to load

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
            **kwargs: Generation parameters

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
                "stream": False,
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
            # Try v1/chat/completions endpoint
            payload = {
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 200),
                "stream": False,
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

    def embeddings(self, text: str) -> Optional[List[float]]:
        """
        Get embeddings for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if failed
        """
        if not self.is_running():
            print("Server not running. Start server first.")
            return None

        try:
            payload = {"content": text}

            response = requests.post(
                f"{self.base_url}/embedding",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", [])

            return None

        except Exception as e:
            print(f"Embeddings failed: {e}")
            return None

    def download_model(self, model_name: str) -> bool:
        """
        Download a model from HuggingFace

        Args:
            model_name: Model to download

        Returns:
            True if download successful
        """
        try:
            # Popular GGUF models
            model_urls = {
                "TinyLlama-1.1B": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "Llama-2-7B": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
                "Mistral-7B": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                "Phi-2": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
            }

            if model_name not in model_urls:
                print(f"Unknown model: {model_name}")
                print(f"Available models: {list(model_urls.keys())}")
                print("\nYou can also download GGUF models from:")
                print("https://huggingface.co/TheBloke")
                return False

            url = model_urls[model_name]
            filename = url.split("/")[-1]
            output_path = self.models_dir / filename

            self.models_dir.mkdir(parents=True, exist_ok=True)

            print(f"Downloading {filename}...")
            print("This may take a while...")

            import urllib.request
            urllib.request.urlretrieve(url, output_path)

            print(f"Downloaded {filename}")
            return True

        except Exception as e:
            print(f"Failed to download model: {e}")
            return False

    def launch_ui(self) -> bool:
        """
        Launch the Windows UI application

        Returns:
            True if launched successfully
        """
        if not self.is_installed():
            print("LLaMA.cpp Windows UI not installed.")
            return False

        try:
            if self.executable.exists():
                subprocess.Popen([str(self.executable)])
                print("Launched Windows UI")
                return True
            else:
                print(f"UI executable not found at {self.executable}")
                return False

        except Exception as e:
            print(f"Failed to launch UI: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "LLaMA.cpp Windows UI",
            "full_name": "LLaMA.cpp Windows User Interface",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "port": self.port,
            "models_dir": str(self.models_dir),
            "install_dir": str(self.install_dir),
            "available_models": len(self.list_models()),
            "model_format": "GGUF/GGML",
            "features": ["text_generation", "chat", "embeddings", "gui"],
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            server_exe = self.install_dir / "server.exe" if sys.platform == "win32" else self.install_dir / "server"
            if server_exe.exists():
                result = subprocess.run(
                    [str(server_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
        except:
            pass
        return "unknown"
