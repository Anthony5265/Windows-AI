"""
LangChain Local Platform Implementation
Local LLM integration using LangChain framework with various backends
"""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class LangChainLocalPlatform:
    """
    LangChain Local - Use LangChain with local models

    Integrates various local model backends (LlamaCpp, GPT4All, HuggingFace)
    """

    def __init__(self, models_dir: Optional[str] = None, backend: str = "llamacpp"):
        """
        Initialize LangChain Local platform

        Args:
            models_dir: Directory containing models (default: ~/langchain-local)
            backend: Backend to use (llamacpp, gpt4all, huggingface)
        """
        self.models_dir = Path(models_dir or "~/langchain-local").expanduser()
        self.backend = backend
        self.executable = "python"
        self.llm = None
        self.current_model = None

    def is_installed(self) -> bool:
        """Check if LangChain is installed"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "langchain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install LangChain and dependencies"""
        print("Installing LangChain Local...")
        try:
            # Install base langchain
            subprocess.run(
                [self.executable, "-m", "pip", "install", "langchain"],
                check=True
            )

            # Install backend-specific packages
            if self.backend == "llamacpp":
                subprocess.run(
                    [self.executable, "-m", "pip", "install", "llama-cpp-python"],
                    check=True
                )
            elif self.backend == "gpt4all":
                subprocess.run(
                    [self.executable, "-m", "pip", "install", "gpt4all"],
                    check=True
                )
            elif self.backend == "huggingface":
                subprocess.run(
                    [self.executable, "-m", "pip", "install", "transformers", "torch"],
                    check=True
                )

            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("LangChain Local installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, model: Optional[str] = None) -> bool:
        """
        Initialize LangChain LLM

        Args:
            model: Model to load

        Returns:
            True if LLM initialized successfully
        """
        if not self.is_installed():
            print("LangChain not installed. Installing...")
            if not self.install():
                return False

        if model:
            return self.load_model(model)

        print("LangChain ready (use load_model to initialize an LLM)")
        return True

    def stop_server(self) -> bool:
        """Cleanup LLM"""
        if self.llm:
            self.llm = None
            self.current_model = None
            print("LangChain LLM unloaded")
            return True
        return False

    def is_running(self) -> bool:
        """Check if LLM is loaded"""
        return self.llm is not None

    def list_models(self) -> List[str]:
        """List available models"""
        if not self.models_dir.exists():
            return []

        models = []
        for item in self.models_dir.iterdir():
            if item.is_file() and item.suffix in [".bin", ".gguf", ".ggml"]:
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
            print(f"Loading {model_name} with {self.backend} backend...")

            # Determine model path
            if Path(model_name).exists():
                model_path = model_name
            else:
                model_path = str(self.models_dir / model_name)

            if self.backend == "llamacpp":
                from langchain_community.llms import LlamaCpp

                self.llm = LlamaCpp(
                    model_path=model_path,
                    n_ctx=2048,
                    n_batch=512,
                    verbose=False,
                )

            elif self.backend == "gpt4all":
                from langchain_community.llms import GPT4All

                self.llm = GPT4All(
                    model=model_path,
                    n_ctx=2048,
                    backend="gptj",
                    verbose=False,
                )

            elif self.backend == "huggingface":
                from langchain_community.llms import HuggingFacePipeline
                from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForCausalLM.from_pretrained(model_name)
                pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_new_tokens=200,
                )
                self.llm = HuggingFacePipeline(pipeline=pipe)

            else:
                print(f"Unknown backend: {self.backend}")
                return False

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
            **kwargs: Generation parameters

        Returns:
            Generated text or None if failed
        """
        if not self.is_running():
            print("No model loaded. Use load_model first.")
            return None

        try:
            result = self.llm(prompt, **kwargs)
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
            # Use LangChain's chat interface if available
            from langchain.schema import (
                AIMessage,
                HumanMessage,
                SystemMessage,
            )

            lc_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))

            # Some backends don't support chat, fallback to prompt
            try:
                result = self.llm(lc_messages, **kwargs)
                return result
            except:
                # Fallback to formatted prompt
                prompt = self._format_chat_prompt(messages)
                return self.generate(prompt, **kwargs)

        except Exception as e:
            print(f"Chat failed: {e}")
            return None

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

    def create_chain(self, chain_type: str = "llm") -> Optional[Any]:
        """
        Create a LangChain chain

        Args:
            chain_type: Type of chain (llm, conversation, qa, etc.)

        Returns:
            Chain object or None if failed
        """
        if not self.is_running():
            print("No model loaded. Use load_model first.")
            return None

        try:
            if chain_type == "conversation":
                from langchain.chains import ConversationChain
                from langchain.memory import ConversationBufferMemory

                memory = ConversationBufferMemory()
                chain = ConversationChain(llm=self.llm, memory=memory)
                return chain

            elif chain_type == "qa":
                from langchain.chains import RetrievalQA
                from langchain_community.vectorstores import FAISS
                from langchain_community.embeddings import HuggingFaceEmbeddings

                embeddings = HuggingFaceEmbeddings()
                # User would need to provide documents
                return None

            else:
                # Return basic LLM chain
                from langchain.chains import LLMChain
                from langchain.prompts import PromptTemplate

                template = "{prompt}"
                prompt = PromptTemplate(template=template, input_variables=["prompt"])
                chain = LLMChain(llm=self.llm, prompt=prompt)
                return chain

        except Exception as e:
            print(f"Failed to create chain: {e}")
            return None

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "LangChain Local",
            "full_name": "LangChain Local Model Integration",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "backend": self.backend,
            "current_model": self.current_model,
            "models_dir": str(self.models_dir),
            "available_models": len(self.list_models()),
            "supported_backends": ["llamacpp", "gpt4all", "huggingface"],
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "langchain"],
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
