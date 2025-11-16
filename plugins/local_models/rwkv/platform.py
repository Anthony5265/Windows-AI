"""
RWKV Platform Implementation
RNN-based language model combining transformer efficiency with RNN inference speed
"""

import subprocess
import requests
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class RWKVPlatform:
    """
    RWKV - Parallelizable RNN with Transformer-level Performance

    Novel architecture combining benefits of transformers and RNNs
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 8000):
        """
        Initialize RWKV platform

        Args:
            models_dir: Directory containing models (default: ~/RWKV/models)
            port: Port for server (default: 8000)
        """
        self.models_dir = Path(models_dir or "~/RWKV/models").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.executable = "python"
        self.model = None
        self.tokenizer = None
        self.current_model = None

    def is_installed(self) -> bool:
        """Check if RWKV is installed"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "rwkv"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install RWKV platform"""
        print("Installing RWKV...")
        try:
            # Install RWKV package
            subprocess.run(
                [self.executable, "-m", "pip", "install", "rwkv"],
                check=True
            )

            # Install tokenizer
            subprocess.run(
                [self.executable, "-m", "pip", "install", "tokenizers"],
                check=True
            )

            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("RWKV installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Initialize RWKV model

        Args:
            model: Model to load (optional)

        Returns:
            True if model initialized successfully
        """
        if not self.is_installed():
            print("RWKV not installed. Installing...")
            if not self.install():
                return False

        if model:
            return self.load_model(model)

        print("RWKV ready (use load_model to load a model)")
        return True

    def stop_server(self) -> bool:
        """Unload model"""
        if self.model:
            self.model = None
            self.tokenizer = None
            self.current_model = None
            print("RWKV model unloaded")
            return True
        return False

    def is_running(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None

    def list_models(self) -> List[str]:
        """List available RWKV models"""
        models = []

        if not self.models_dir.exists():
            # Return popular RWKV models
            return [
                "RWKV-4-Pile-169M",
                "RWKV-4-Pile-430M",
                "RWKV-4-Pile-1B5",
                "RWKV-4-Pile-3B",
                "RWKV-4-Pile-7B",
                "RWKV-4-Pile-14B",
            ]

        # List local model files
        for item in self.models_dir.iterdir():
            if item.is_file() and item.suffix == ".pth":
                models.append(item.name)

        return sorted(models)

    def load_model(self, model_name: str) -> bool:
        """
        Load a model

        Args:
            model_name: Name or path of model to load

        Returns:
            True if model loaded successfully
        """
        try:
            print(f"Loading {model_name}...")

            from rwkv.model import RWKV
            from rwkv.utils import PIPELINE

            # Determine model path
            if Path(model_name).exists():
                model_path = model_name
            else:
                model_path = str(self.models_dir / model_name)

            # Load model
            self.model = RWKV(model=model_path, strategy='cpu fp32')

            # Load tokenizer/pipeline
            self.tokenizer = PIPELINE(self.model, "20B_tokenizer.json")

            self.current_model = model_name
            print(f"Loaded {model_name}")
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
            print("No model loaded. Use load_model first.")
            return None

        try:
            # Extract parameters
            max_tokens = kwargs.get("max_tokens", 200)
            temperature = kwargs.get("temperature", 1.0)
            top_p = kwargs.get("top_p", 0.85)
            top_k = kwargs.get("top_k", 0)  # 0 = disabled
            alpha_frequency = kwargs.get("alpha_frequency", 0.25)
            alpha_presence = kwargs.get("alpha_presence", 0.25)

            # Generate using pipeline
            result = self.tokenizer.generate(
                prompt,
                token_count=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                alpha_frequency=alpha_frequency,
                alpha_presence=alpha_presence,
            )

            return result

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
        return "\n\n".join(prompt_parts)

    def download_model(self, model_name: str) -> bool:
        """
        Download a model from HuggingFace

        Args:
            model_name: Model name (e.g., "RWKV-4-Pile-1B5")

        Returns:
            True if download successful
        """
        try:
            print(f"Downloading {model_name}...")

            # Map model names to HuggingFace URLs
            model_urls = {
                "RWKV-4-Pile-169M": "https://huggingface.co/BlinkDL/rwkv-4-pile-169m/resolve/main/RWKV-4-Pile-169M-20220807-8023.pth",
                "RWKV-4-Pile-430M": "https://huggingface.co/BlinkDL/rwkv-4-pile-430m/resolve/main/RWKV-4-Pile-430M-20220808-8066.pth",
                "RWKV-4-Pile-1B5": "https://huggingface.co/BlinkDL/rwkv-4-pile-1b5/resolve/main/RWKV-4-Pile-1B5-20220929-ctx4096.pth",
                "RWKV-4-Pile-3B": "https://huggingface.co/BlinkDL/rwkv-4-pile-3b/resolve/main/RWKV-4-Pile-3B-20221008-8023.pth",
                "RWKV-4-Pile-7B": "https://huggingface.co/BlinkDL/rwkv-4-pile-7b/resolve/main/RWKV-4-Pile-7B-20230109-ctx4096.pth",
                "RWKV-4-Pile-14B": "https://huggingface.co/BlinkDL/rwkv-4-pile-14b/resolve/main/RWKV-4-Pile-14B-20230228-ctx8192-test663.pth",
            }

            if model_name not in model_urls:
                print(f"Unknown model: {model_name}")
                print(f"Available models: {list(model_urls.keys())}")
                return False

            url = model_urls[model_name]
            output_file = self.models_dir / f"{model_name}.pth"

            self.models_dir.mkdir(parents=True, exist_ok=True)

            # Download using wget or urllib
            import urllib.request
            print("Downloading... (this may take a while)")
            urllib.request.urlretrieve(url, output_file)

            print(f"Downloaded {model_name} to {output_file}")
            return True

        except Exception as e:
            print(f"Failed to download model: {e}")
            return False

    def get_state(self) -> Optional[Any]:
        """
        Get current model state (for stateful generation)

        Returns:
            Model state or None
        """
        if not self.is_running():
            return None

        try:
            # RWKV supports stateful generation
            return self.model.get_state()
        except:
            return None

    def set_state(self, state: Any) -> bool:
        """
        Set model state (for stateful generation)

        Args:
            state: Model state to restore

        Returns:
            True if successful
        """
        if not self.is_running():
            return False

        try:
            self.model.set_state(state)
            return True
        except:
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "RWKV",
            "full_name": "RWKV - Parallelizable RNN with Transformer Performance",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "current_model": self.current_model,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "architecture": "RNN",
            "features": ["text_generation", "chat", "stateful"],
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "rwkv"],
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
