"""
GPT4All-J Platform Implementation
GPT-J based local language model with simple Python bindings
"""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class GPT4AllJPlatform:
    """
    GPT4All-J - GPT-J based local language model

    Easy-to-use local model with simple Python API
    """

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize GPT4All-J platform

        Args:
            models_dir: Directory containing models (default: ~/.local/share/nomic.ai/GPT4All)
        """
        self.models_dir = Path(models_dir or "~/.local/share/nomic.ai/GPT4All").expanduser()
        self.executable = "python"
        self.model = None
        self.current_model = None

    def is_installed(self) -> bool:
        """Check if GPT4All is installed"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "gpt4all"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install GPT4All platform"""
        print("Installing GPT4All...")
        try:
            # Install gpt4all package
            subprocess.run(
                [self.executable, "-m", "pip", "install", "gpt4all"],
                check=True
            )

            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("GPT4All installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Initialize GPT4All model

        Args:
            model: Model to load (optional)

        Returns:
            True if model initialized successfully
        """
        if not self.is_installed():
            print("GPT4All not installed. Installing...")
            if not self.install():
                return False

        if model:
            return self.load_model(model)

        print("GPT4All ready (use load_model to load a model)")
        return True

    def stop_server(self) -> bool:
        """Unload model"""
        if self.model:
            self.model = None
            self.current_model = None
            print("GPT4All model unloaded")
            return True
        return False

    def is_running(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None

    def list_models(self) -> List[str]:
        """List available GPT4All models"""
        # Available GPT4All models
        available_models = [
            "ggml-gpt4all-j-v1.3-groovy.bin",
            "ggml-gpt4all-j-v1.2-jazzy.bin",
            "ggml-gpt4all-j-v1.1-breezy.bin",
            "ggml-gpt4all-j.bin",
            "ggml-gpt4all-l13b-snoozy.bin",
            "ggml-mpt-7b-chat.bin",
            "ggml-mpt-7b-instruct.bin",
        ]

        # Check which ones are downloaded
        local_models = []
        if self.models_dir.exists():
            for model_file in self.models_dir.iterdir():
                if model_file.is_file() and model_file.suffix == ".bin":
                    local_models.append(model_file.name)

        # Return local models if any, otherwise available models
        return local_models if local_models else available_models

    def load_model(self, model_name: str = "ggml-gpt4all-j-v1.3-groovy.bin") -> bool:
        """
        Load a model

        Args:
            model_name: Name of model to load

        Returns:
            True if model loaded successfully
        """
        try:
            print(f"Loading {model_name}...")

            from gpt4all import GPT4All

            # Check if model exists locally
            model_path = self.models_dir / model_name
            if model_path.exists():
                # Load from local path
                self.model = GPT4All(model_name, model_path=str(self.models_dir))
            else:
                # Download and load
                print(f"Downloading {model_name}...")
                self.model = GPT4All(model_name, model_path=str(self.models_dir))

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
            **kwargs: Generation parameters (max_tokens, temp, etc.)

        Returns:
            Generated text or None if failed
        """
        if not self.is_running():
            print("No model loaded. Use load_model first.")
            return None

        try:
            # Extract parameters
            max_tokens = kwargs.get("max_tokens", 200)
            temp = kwargs.get("temperature", 0.7)
            top_k = kwargs.get("top_k", 40)
            top_p = kwargs.get("top_p", 0.9)
            repeat_penalty = kwargs.get("repeat_penalty", 1.1)

            # Generate
            result = self.model.generate(
                prompt,
                max_tokens=max_tokens,
                temp=temp,
                top_k=top_k,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
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
        if not self.is_running():
            print("No model loaded. Use load_model first.")
            return None

        try:
            # GPT4All supports chat sessions
            with self.model.chat_session():
                # Process all messages
                for msg in messages[:-1]:  # All but last
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        # Generate to build context (don't return)
                        self.model.generate(content, max_tokens=1)

                # Generate response to last message
                last_msg = messages[-1]
                prompt = last_msg.get("content", "")

                max_tokens = kwargs.get("max_tokens", 200)
                temp = kwargs.get("temperature", 0.7)
                top_k = kwargs.get("top_k", 40)
                top_p = kwargs.get("top_p", 0.9)

                result = self.model.generate(
                    prompt,
                    max_tokens=max_tokens,
                    temp=temp,
                    top_k=top_k,
                    top_p=top_p,
                )

                return result

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

    def stream_generate(self, prompt: str, **kwargs):
        """
        Generate text with streaming

        Args:
            prompt: Input prompt
            **kwargs: Generation parameters

        Yields:
            Generated tokens
        """
        if not self.is_running():
            print("No model loaded. Use load_model first.")
            return

        try:
            max_tokens = kwargs.get("max_tokens", 200)
            temp = kwargs.get("temperature", 0.7)
            top_k = kwargs.get("top_k", 40)
            top_p = kwargs.get("top_p", 0.9)

            # Stream tokens
            for token in self.model.generate(
                prompt,
                max_tokens=max_tokens,
                temp=temp,
                top_k=top_k,
                top_p=top_p,
                streaming=True,
            ):
                yield token

        except Exception as e:
            print(f"Streaming generation failed: {e}")

    def download_model(self, model_name: str) -> bool:
        """
        Download a model

        Args:
            model_name: Model name to download

        Returns:
            True if download successful
        """
        try:
            print(f"Downloading {model_name}...")

            from gpt4all import GPT4All

            # This will download the model
            GPT4All(model_name, model_path=str(self.models_dir))

            print(f"Downloaded {model_name}")
            return True

        except Exception as e:
            print(f"Failed to download model: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "GPT4All-J",
            "full_name": "GPT4All-J - Local GPT-J Model",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "current_model": self.current_model,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "features": ["text_generation", "chat", "streaming"],
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "gpt4all"],
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

    def embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Get embeddings for texts (if model supports it)

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors or None if not supported
        """
        if not self.is_running():
            print("No model loaded. Use load_model first.")
            return None

        try:
            # Check if model supports embeddings
            if hasattr(self.model, "embed"):
                embeddings = []
                for text in texts:
                    embedding = self.model.embed(text)
                    embeddings.append(embedding)
                return embeddings
            else:
                print("Current model does not support embeddings")
                return None

        except Exception as e:
            print(f"Embeddings failed: {e}")
            return None
