"""
FastChat Platform Implementation
Distributed multi-model LLM serving system with OpenAI-compatible API
"""

import subprocess
import requests
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class FastChatPlatform:
    """
    FastChat - An open platform for training, serving, and evaluating LLMs

    Provides OpenAI-compatible RESTful APIs for model serving
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 8000, controller_port: int = 21001):
        """
        Initialize FastChat platform

        Args:
            models_dir: Directory containing models (default: ~/.cache/fastchat)
            port: Port for API server (default: 8000)
            controller_port: Port for controller (default: 21001)
        """
        self.models_dir = Path(models_dir or "~/.cache/fastchat").expanduser()
        self.port = port
        self.controller_port = controller_port
        self.base_url = f"http://localhost:{port}"
        self.controller_url = f"http://localhost:{controller_port}"
        self.controller_process = None
        self.api_process = None
        self.worker_process = None
        self.executable = "python"

    def is_installed(self) -> bool:
        """Check if FastChat is installed"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "fschat"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install FastChat platform"""
        print("Installing FastChat...")
        try:
            # Install FastChat package
            subprocess.run(
                [self.executable, "-m", "pip", "install", "fschat[model_worker,webui]"],
                check=True
            )

            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("FastChat installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Start FastChat server (controller, worker, and API)

        Args:
            model: Model name to load (optional)

        Returns:
            True if server started successfully
        """
        if not self.is_installed():
            print("FastChat not installed. Installing...")
            if not self.install():
                return False

        if self.is_running():
            print("Server already running")
            return True

        try:
            # Start controller
            print("Starting FastChat controller...")
            self.controller_process = subprocess.Popen(
                [self.executable, "-m", "fastchat.serve.controller",
                 "--host", "0.0.0.0",
                 "--port", str(self.controller_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)

            # Start model worker if model specified
            if model:
                print(f"Starting model worker with {model}...")
                self.worker_process = subprocess.Popen(
                    [self.executable, "-m", "fastchat.serve.model_worker",
                     "--model-path", model,
                     "--controller-address", self.controller_url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                time.sleep(5)

            # Start OpenAI API server
            print("Starting OpenAI-compatible API server...")
            self.api_process = subprocess.Popen(
                [self.executable, "-m", "fastchat.serve.openai_api_server",
                 "--host", "0.0.0.0",
                 "--port", str(self.port),
                 "--controller-address", self.controller_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(30):
                if self.is_running():
                    print(f"FastChat server started on port {self.port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop FastChat server"""
        stopped = False

        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait(timeout=10)
            self.api_process = None
            stopped = True

        if self.worker_process:
            self.worker_process.terminate()
            self.worker_process.wait(timeout=10)
            self.worker_process = None
            stopped = True

        if self.controller_process:
            self.controller_process.terminate()
            self.controller_process.wait(timeout=10)
            self.controller_process = None
            stopped = True

        if stopped:
            print("FastChat server stopped")
        return stopped

    def is_running(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """List available models"""
        if not self.is_running():
            # List local model directories
            if not self.models_dir.exists():
                return []

            models = []
            for item in self.models_dir.iterdir():
                if item.is_dir():
                    models.append(item.name)
            return sorted(models)

        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            print(f"Failed to list models: {e}")
            return []

    def load_model(self, model_name: str) -> bool:
        """
        Load a model

        Args:
            model_name: Name or path of model to load

        Returns:
            True if model loaded successfully
        """
        if not self.is_running():
            return self.start_server(model=model_name)

        # FastChat requires restarting worker with new model
        if self.worker_process:
            self.worker_process.terminate()
            self.worker_process.wait(timeout=10)

        try:
            print(f"Loading model {model_name}...")
            self.worker_process = subprocess.Popen(
                [self.executable, "-m", "fastchat.serve.model_worker",
                 "--model-path", model_name,
                 "--controller-address", self.controller_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters (max_tokens, temperature, etc.)

        Returns:
            Generated text or None if failed
        """
        if not self.is_running():
            print("Server not running. Start server first.")
            return None

        try:
            # Get available models
            models = self.list_models()
            if not models:
                print("No models available")
                return None

            model = kwargs.get("model", models[0])

            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 200),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "n": 1,
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/v1/completions",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("text", "")

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
            # Get available models
            models = self.list_models()
            if not models:
                print("No models available")
                return None

            model = kwargs.get("model", models[0])

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 200),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
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

            return None

        except Exception as e:
            print(f"Chat failed: {e}")
            return None

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "FastChat",
            "full_name": "FastChat - Distributed Multi-Model Serving System",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "port": self.port,
            "controller_port": self.controller_port,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "api_compatible": "OpenAI",
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "fschat"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
        except:
            pass
        return "unknown"
