"""
Dalai Platform Implementation
Run LLaMA and Alpaca models locally with simple npm installation
"""

import subprocess
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class DalaiPlatform:
    """
    Dalai - Dead simple way to run LLaMA and Alpaca on your computer

    Uses npx to download and run models without complex setup
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 4000):
        """
        Initialize Dalai platform

        Args:
            models_dir: Directory containing models (default: ~/dalai)
            port: Port for server (default: 4000)
        """
        self.models_dir = Path(models_dir or "~/dalai").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.executable = "npx"
        self.node_executable = "node"

    def is_installed(self) -> bool:
        """Check if Dalai is installed (checks for node/npm)"""
        try:
            # Check if node is installed
            result = subprocess.run(
                [self.node_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False

            # Check if dalai directory exists
            return self.models_dir.exists()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self, model: str = "alpaca.7B") -> bool:
        """
        Install Dalai and download a model

        Args:
            model: Model to install (e.g., alpaca.7B, alpaca.13B, llama.7B)

        Returns:
            True if installation successful
        """
        print(f"Installing Dalai with {model}...")
        try:
            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            # Use npx to install model
            print(f"Downloading {model} (this may take a while)...")
            subprocess.run(
                [self.executable, "dalai", model],
                cwd=self.models_dir,
                check=True
            )

            print("Dalai installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Start Dalai server

        Args:
            model: Model to load (optional)

        Returns:
            True if server started successfully
        """
        if not self.is_installed():
            print("Dalai not installed. Installing...")
            if not self.install():
                return False

        if self.is_running():
            print("Server already running")
            return True

        try:
            cmd = [self.executable, "dalai", "serve"]

            if model:
                cmd.append(model)

            self.process = subprocess.Popen(
                cmd,
                cwd=self.models_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(60):
                if self.is_running():
                    print(f"Dalai server started on port {self.port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop Dalai server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("Dalai server stopped")
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
        """List available models"""
        models = []

        if not self.models_dir.exists():
            return models

        # Look for model directories
        for model_type in ["alpaca", "llama"]:
            model_dir = self.models_dir / model_type
            if model_dir.exists():
                for size_dir in model_dir.iterdir():
                    if size_dir.is_dir():
                        models.append(f"{model_type}.{size_dir.name}")

        return sorted(models)

    def load_model(self, model_name: str) -> bool:
        """
        Load a model

        Args:
            model_name: Name of model to load (e.g., alpaca.7B)

        Returns:
            True if model loaded successfully
        """
        if not self.is_running():
            return self.start_server(model=model_name)

        # Dalai requires server restart to change models
        self.stop_server()
        return self.start_server(model=model_name)

    def download_model(self, model_name: str) -> bool:
        """
        Download a model

        Args:
            model_name: Model to download (e.g., alpaca.7B, llama.13B)

        Returns:
            True if download successful
        """
        try:
            print(f"Downloading {model_name}...")
            subprocess.run(
                [self.executable, "dalai", model_name],
                cwd=self.models_dir,
                check=True
            )
            print(f"Downloaded {model_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to download model: {e}")
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
            models = self.list_models()
            if not models:
                print("No models available")
                return None

            model = kwargs.get("model", models[0])

            payload = {
                "model": model,
                "prompt": prompt,
                "n_predict": kwargs.get("max_tokens", 200),
                "temp": kwargs.get("temperature", 0.7),
                "top_k": kwargs.get("top_k", 40),
                "top_p": kwargs.get("top_p", 0.9),
                "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
            }

            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")

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
        # Convert chat messages to prompt
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
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "Dalai",
            "full_name": "Dalai - Simple LLaMA/Alpaca Runner",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "port": self.port,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "supported_models": ["alpaca.7B", "alpaca.13B", "llama.7B", "llama.13B", "llama.30B", "llama.65B"],
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "dalai", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "unknown"
