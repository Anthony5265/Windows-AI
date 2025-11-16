"""
Oobabooga (Text Generation WebUI) Platform Implementation
Local model inference platform with web interface
"""

import subprocess
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import sys


class OobaboogaPlatform:
    """
    Oobabooga Text Generation WebUI Platform

    Web-based interface for running large language models locally
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 7860, api_port: int = 5000):
        """
        Initialize Oobabooga platform

        Args:
            models_dir: Directory containing models (default: ~/text-generation-webui/models)
            port: Port for web UI (default: 7860)
            api_port: Port for API server (default: 5000)
        """
        self.models_dir = Path(models_dir or "~/text-generation-webui/models").expanduser()
        self.port = port
        self.api_port = api_port
        self.base_url = f"http://localhost:{api_port}"
        self.web_ui_url = f"http://localhost:{port}"
        self.process = None
        self.install_dir = Path("~/text-generation-webui").expanduser()
        self.executable = "python"

    def is_installed(self) -> bool:
        """Check if Oobabooga is installed"""
        server_py = self.install_dir / "server.py"
        return server_py.exists()

    def install(self) -> bool:
        """Install Oobabooga platform"""
        print("Installing Oobabooga Text Generation WebUI...")
        try:
            # Clone repository
            subprocess.run(
                ["git", "clone", "https://github.com/oobabooga/text-generation-webui",
                 str(self.install_dir)],
                check=True
            )

            # Install dependencies
            if sys.platform == "win32":
                install_script = self.install_dir / "start_windows.bat"
            else:
                install_script = self.install_dir / "start_linux.sh"

            if install_script.exists():
                subprocess.run([str(install_script)], cwd=self.install_dir, check=True)

            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None, api: bool = True) -> bool:
        """
        Start Oobabooga server

        Args:
            model: Model to load (optional)
            api: Enable API mode (default: True)

        Returns:
            True if server started successfully
        """
        if not self.is_installed():
            print("Oobabooga not installed. Installing...")
            if not self.install():
                return False

        if self.is_running():
            print("Server already running")
            return True

        try:
            cmd = [
                self.executable,
                str(self.install_dir / "server.py"),
                "--listen-port", str(self.port)
            ]

            if api:
                cmd.extend(["--api", "--api-port", str(self.api_port)])

            if model:
                cmd.extend(["--model", model])

            self.process = subprocess.Popen(
                cmd,
                cwd=self.install_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(30):
                if self.is_running():
                    print(f"Oobabooga server started on port {self.port}")
                    if api:
                        print(f"API available on port {self.api_port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop Oobabooga server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("Server stopped")
            return True
        return False

    def is_running(self) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/model",
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
            if item.is_dir():
                models.append(item.name)

        return sorted(models)

    def load_model(self, model_name: str) -> bool:
        """
        Load a model

        Args:
            model_name: Name of model to load

        Returns:
            True if model loaded successfully
        """
        if not self.is_running():
            return self.start_server(model=model_name)

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/model",
                json={"model_name": model_name},
                timeout=60
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Generate text from prompt

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters (max_length, temperature, etc.)

        Returns:
            Generated text or None if failed
        """
        if not self.is_running():
            print("Server not running. Start server first.")
            return None

        try:
            payload = {
                "prompt": prompt,
                "max_new_tokens": kwargs.get("max_length", 200),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "top_k": kwargs.get("top_k", 40),
                "repetition_penalty": kwargs.get("repetition_penalty", 1.1),
            }

            response = requests.post(
                f"{self.base_url}/api/v1/generate",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("results", [{}])[0].get("text", "")

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
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "Oobabooga",
            "full_name": "Text Generation WebUI",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "port": self.port,
            "api_port": self.api_port,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            if self.install_dir.exists():
                # Try to get git version
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
