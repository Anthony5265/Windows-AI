"""
Alpaca.cpp Platform Implementation
C++ implementation of Alpaca model for efficient local inference
"""

import subprocess
import requests
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class AlpacaCppPlatform:
    """
    Alpaca.cpp - Efficient C++ implementation for Alpaca models

    Lightweight and fast local inference for Alpaca-style models
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 8080):
        """
        Initialize Alpaca.cpp platform

        Args:
            models_dir: Directory containing models (default: ~/alpaca.cpp/models)
            port: Port for server (default: 8080)
        """
        self.models_dir = Path(models_dir or "~/alpaca.cpp/models").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.install_dir = Path("~/alpaca.cpp").expanduser()
        self.executable = self.install_dir / "server"
        if sys.platform == "win32":
            self.executable = self.install_dir / "server.exe"

    def is_installed(self) -> bool:
        """Check if Alpaca.cpp is installed"""
        return self.install_dir.exists() and self.executable.exists()

    def install(self) -> bool:
        """Install Alpaca.cpp platform"""
        print("Installing Alpaca.cpp...")
        try:
            # Clone repository
            subprocess.run(
                ["git", "clone", "https://github.com/antimatter15/alpaca.cpp",
                 str(self.install_dir)],
                check=True
            )

            # Build the project
            print("Building Alpaca.cpp...")
            if sys.platform == "win32":
                # Windows build
                subprocess.run(
                    ["cmake", "-B", "build"],
                    cwd=self.install_dir,
                    check=True
                )
                subprocess.run(
                    ["cmake", "--build", "build", "--config", "Release"],
                    cwd=self.install_dir,
                    check=True
                )
            else:
                # Unix build
                subprocess.run(
                    ["make", "server"],
                    cwd=self.install_dir,
                    check=True
                )

            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("Alpaca.cpp installed successfully")
            print("Note: You'll need to download GGML model files to the models directory")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None, threads: int = 4) -> bool:
        """
        Start Alpaca.cpp server

        Args:
            model: Path to model file (GGML format)
            threads: Number of threads to use (default: 4)

        Returns:
            True if server started successfully
        """
        if not self.is_installed():
            print("Alpaca.cpp not installed. Installing...")
            if not self.install():
                return False

        if self.is_running():
            print("Server already running")
            return True

        # Find a model if not specified
        if not model:
            models = self.list_models()
            if not models:
                print("No models found. Please download a GGML model file.")
                return False
            model = str(self.models_dir / models[0])

        try:
            cmd = [
                str(self.executable),
                "-m", model,
                "-t", str(threads),
                "--port", str(self.port)
            ]

            self.process = subprocess.Popen(
                cmd,
                cwd=self.install_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(30):
                if self.is_running():
                    print(f"Alpaca.cpp server started on port {self.port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop Alpaca.cpp server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("Alpaca.cpp server stopped")
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
            if item.is_file() and item.suffix in [".bin", ".ggml"]:
                models.append(item.name)

        return sorted(models)

    def load_model(self, model_name: str) -> bool:
        """
        Load a model

        Args:
            model_name: Name of model file to load

        Returns:
            True if model loaded successfully
        """
        model_path = self.models_dir / model_name
        if not model_path.exists():
            print(f"Model not found: {model_path}")
            return False

        # Alpaca.cpp requires server restart to change models
        if self.is_running():
            self.stop_server()

        return self.start_server(model=str(model_path))

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters (n_predict, temp, top_k, etc.)

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
                "temp": kwargs.get("temperature", 0.7),
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
        # Convert chat messages to Alpaca-style prompt
        prompt = self._format_alpaca_prompt(messages)
        return self.generate(prompt, **kwargs)

    def _format_alpaca_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into Alpaca instruction format"""
        # Alpaca instruction format
        instruction = ""
        input_text = ""

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                instruction = content
            elif role == "user":
                if instruction:
                    input_text = content
                else:
                    instruction = content

        if instruction and input_text:
            prompt = f"Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        elif instruction:
            prompt = f"Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Response:\n"
        else:
            prompt = "### Response:\n"

        return prompt

    def download_model(self, model_name: str = "ggml-alpaca-7b-q4.bin") -> bool:
        """
        Download a model

        Args:
            model_name: Model filename to download

        Returns:
            True if download successful
        """
        try:
            # Models are typically downloaded from HuggingFace
            base_url = "https://huggingface.co/Sosaka/Alpaca-native-4bit-ggml/resolve/main"
            url = f"{base_url}/{model_name}"

            print(f"Downloading {model_name}...")
            self.models_dir.mkdir(parents=True, exist_ok=True)

            import urllib.request
            urllib.request.urlretrieve(url, self.models_dir / model_name)

            print(f"Downloaded {model_name}")
            return True
        except Exception as e:
            print(f"Failed to download model: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "Alpaca.cpp",
            "full_name": "Alpaca.cpp - C++ Alpaca Implementation",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "port": self.port,
            "models_dir": str(self.models_dir),
            "install_dir": str(self.install_dir),
            "available_models": len(self.list_models()),
            "model_format": "GGML",
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            if self.install_dir.exists():
                result = subprocess.run(
                    ["git", "describe", "--tags"],
                    cwd=self.install_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
        except:
            pass
        return "unknown"
