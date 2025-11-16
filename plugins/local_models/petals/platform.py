"""
Petals Platform Implementation
Distributed inference and fine-tuning of large language models
"""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class PetalsPlatform:
    """
    Petals - Run large language models at home via BitTorrent-style inference

    Collaborative inference platform for running 100B+ parameter models
    """

    def __init__(self, models_dir: Optional[str] = None):
        """
        Initialize Petals platform

        Args:
            models_dir: Directory for model cache (default: ~/.cache/petals)
        """
        self.models_dir = Path(models_dir or "~/.cache/petals").expanduser()
        self.executable = "python"
        self.client = None
        self.current_model = None

    def is_installed(self) -> bool:
        """Check if Petals is installed"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "petals"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install Petals platform"""
        print("Installing Petals...")
        try:
            # Install petals package
            subprocess.run(
                [self.executable, "-m", "pip", "install", "petals"],
                check=True
            )

            # Create cache directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("Petals installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Initialize Petals client

        Args:
            model: Model to connect to (e.g., 'bigscience/bloom-petals')

        Returns:
            True if client initialized successfully
        """
        if not self.is_installed():
            print("Petals not installed. Installing...")
            if not self.install():
                return False

        if model:
            return self.load_model(model)

        print("Petals client ready (use load_model to connect to a model)")
        return True

    def stop_server(self) -> bool:
        """Disconnect Petals client"""
        if self.client:
            self.client = None
            self.current_model = None
            print("Petals client disconnected")
            return True
        return False

    def is_running(self) -> bool:
        """Check if client is connected to a model"""
        return self.client is not None

    def list_models(self) -> List[str]:
        """List available Petals models"""
        # Popular Petals models
        return [
            "bigscience/bloom-petals",
            "bigscience/bloomz-petals",
            "enoch/llama-65b-hf",
            "meta-llama/Llama-2-70b-hf",
            "meta-llama/Llama-2-70b-chat-hf",
        ]

    def load_model(self, model_name: str) -> bool:
        """
        Load and connect to a model

        Args:
            model_name: Model name (e.g., 'bigscience/bloom-petals')

        Returns:
            True if model loaded successfully
        """
        try:
            print(f"Connecting to {model_name}...")

            # Import Petals modules
            from petals import AutoDistributedModelForCausalLM
            from transformers import AutoTokenizer

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

            # Connect to distributed model
            self.client = AutoDistributedModelForCausalLM.from_pretrained(model_name)
            self.current_model = model_name

            print(f"Connected to {model_name}")
            return True
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
            print("Not connected to a model. Use load_model first.")
            return None

        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt")

            # Generate
            max_length = kwargs.get("max_length", 200)
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.9)
            top_k = kwargs.get("top_k", 40)

            outputs = self.client.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True,
            )

            # Decode output
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove prompt from result
            if result.startswith(prompt):
                result = result[len(prompt):].strip()

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
        return "\n".join(prompt_parts)

    def run_server(self, model_name: str, **kwargs) -> bool:
        """
        Run as a server node (contribute compute)

        Args:
            model_name: Model to serve
            **kwargs: Server configuration

        Returns:
            True if server started successfully
        """
        try:
            print(f"Starting Petals server for {model_name}...")

            # Server configuration
            initial_peers = kwargs.get("initial_peers", [])
            device = kwargs.get("device", "cpu")
            torch_dtype = kwargs.get("torch_dtype", "auto")

            cmd = [
                self.executable, "-m", "petals.cli.run_server",
                model_name,
                "--device", device,
                "--torch_dtype", torch_dtype,
            ]

            if initial_peers:
                cmd.extend(["--initial_peers"] + initial_peers)

            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            print(f"Petals server started for {model_name}")
            return True
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "Petals",
            "full_name": "Petals - Distributed LLM Inference",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "current_model": self.current_model,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "mode": "distributed",
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "petals"],
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
        Get embeddings for texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors or None if failed
        """
        if not self.is_running():
            print("Not connected to a model. Use load_model first.")
            return None

        try:
            embeddings = []
            for text in texts:
                # Tokenize
                inputs = self.tokenizer(text, return_tensors="pt")

                # Get hidden states
                with self.client.inference_session(max_length=512) as sess:
                    outputs = sess.step(inputs.input_ids)
                    # Use last hidden state as embedding
                    embedding = outputs[0, -1, :].tolist()
                    embeddings.append(embedding)

            return embeddings
        except Exception as e:
            print(f"Embeddings failed: {e}")
            return None
