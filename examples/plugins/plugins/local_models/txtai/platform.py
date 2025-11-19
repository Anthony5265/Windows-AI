"""
txtai Platform Implementation
All-in-one embeddings database with semantic search and LLM integration
"""

import subprocess
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class TxtaiPlatform:
    """
    txtai - All-in-one embeddings database for semantic search and LLM integration

    Combines embeddings, semantic search, and local LLM capabilities
    """

    def __init__(self, models_dir: Optional[str] = None, port: int = 8000):
        """
        Initialize txtai platform

        Args:
            models_dir: Directory for model cache (default: ~/.cache/txtai)
            port: Port for API server (default: 8000)
        """
        self.models_dir = Path(models_dir or "~/.cache/txtai").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.executable = "python"
        self.embeddings = None
        self.llm = None

    def is_installed(self) -> bool:
        """Check if txtai is installed"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "txtai"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install txtai platform"""
        print("Installing txtai...")
        try:
            # Install txtai with all features
            subprocess.run(
                [self.executable, "-m", "pip", "install", "txtai[api,pipeline]"],
                check=True
            )

            # Create cache directory
            self.models_dir.mkdir(parents=True, exist_ok=True)

            print("txtai installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Installation failed: {e}")
            return False

    def start_server(self, config: Optional[str] = None) -> bool:
        """
        Start txtai API server

        Args:
            config: Path to config file (YAML)

        Returns:
            True if server started successfully
        """
        if not self.is_installed():
            print("txtai not installed. Installing...")
            if not self.install():
                return False

        if self.is_running():
            print("Server already running")
            return True

        try:
            cmd = [self.executable, "-m", "txtai.api"]

            if config:
                cmd.extend(["--config", config])

            # Set port via environment
            import os
            env = os.environ.copy()
            env["TXTAI_PORT"] = str(self.port)

            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            for _ in range(30):
                if self.is_running():
                    print(f"txtai server started on port {self.port}")
                    return True
                time.sleep(1)

            print("Server failed to start within timeout")
            return False

        except Exception as e:
            print(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop txtai server"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("txtai server stopped")
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
        """List available embedding models"""
        # Popular txtai-compatible models
        return [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "BAAI/bge-small-en-v1.5",
            "BAAI/bge-base-en-v1.5",
            "BAAI/bge-large-en-v1.5",
        ]

    def load_model(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> bool:
        """
        Load an embeddings model

        Args:
            model_name: Name of model to load

        Returns:
            True if model loaded successfully
        """
        try:
            print(f"Loading embeddings model {model_name}...")

            from txtai.embeddings import Embeddings

            self.embeddings = Embeddings({
                "path": model_name,
                "content": True,
            })

            print(f"Loaded {model_name}")
            return True

        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

    def load_llm(self, model_name: str) -> bool:
        """
        Load an LLM for text generation

        Args:
            model_name: Name of LLM to load

        Returns:
            True if LLM loaded successfully
        """
        try:
            print(f"Loading LLM {model_name}...")

            from txtai.pipeline import LLM

            self.llm = LLM(model_name)

            print(f"Loaded LLM {model_name}")
            return True

        except Exception as e:
            print(f"Failed to load LLM: {e}")
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
        if not self.llm:
            # Try to load default LLM
            if not self.load_llm("google/flan-t5-base"):
                print("No LLM loaded. Use load_llm first.")
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

    def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Get embeddings for texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors or None if failed
        """
        if not self.embeddings:
            # Try to load default model
            if not self.load_model():
                print("No embeddings model loaded. Use load_model first.")
                return None

        try:
            # Index texts to get embeddings
            self.embeddings.index([(i, text, None) for i, text in enumerate(texts)])

            # Get embeddings
            embeddings = []
            for i in range(len(texts)):
                embedding = self.embeddings.transform([texts[i]])[0]
                embeddings.append(embedding.tolist())

            return embeddings

        except Exception as e:
            print(f"Embedding failed: {e}")
            return None

    def search(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search over documents

        Args:
            query: Search query
            documents: List of documents to search
            top_k: Number of results to return

        Returns:
            List of search results with scores
        """
        if not self.embeddings:
            if not self.load_model():
                print("No embeddings model loaded. Use load_model first.")
                return []

        try:
            # Index documents
            self.embeddings.index([(i, doc, None) for i, doc in enumerate(documents)])

            # Search
            results = self.embeddings.search(query, top_k)

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result[0],
                    "score": result[1],
                    "text": documents[result[0]] if result[0] < len(documents) else None,
                })

            return formatted_results

        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def rag(self, query: str, documents: List[str], **kwargs) -> Optional[str]:
        """
        Retrieval-Augmented Generation

        Args:
            query: User query
            documents: Knowledge base documents
            **kwargs: Generation parameters

        Returns:
            Generated answer or None if failed
        """
        try:
            # Search for relevant documents
            search_results = self.search(query, documents, top_k=3)

            # Build context from top results
            context = "\n\n".join([r["text"] for r in search_results if r["text"]])

            # Generate answer with context
            prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            return self.generate(prompt, **kwargs)

        except Exception as e:
            print(f"RAG failed: {e}")
            return None

    def get_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return {
            "name": "txtai",
            "full_name": "txtai - All-in-one Embeddings Database",
            "version": self._get_version(),
            "installed": self.is_installed(),
            "running": self.is_running(),
            "port": self.port,
            "models_dir": str(self.models_dir),
            "has_embeddings": self.embeddings is not None,
            "has_llm": self.llm is not None,
            "features": ["embeddings", "semantic_search", "llm", "rag"],
        }

    def _get_version(self) -> str:
        """Get platform version"""
        try:
            result = subprocess.run(
                [self.executable, "-m", "pip", "show", "txtai"],
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
