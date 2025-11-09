"""
LLaMA Local Plugin
Run LLaMA models locally using llama-cpp-python
"""
from typing import Dict, Any, List, Optional
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama, LlamaGrammar
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not installed. Install with: pip install llama-cpp-python")


class Plugin:
    """Plugin for running LLaMA models locally"""

    def __init__(self):
        self.name = "LLaMA Local"
        self.version = "2.0.0"
        self.description = "Run LLaMA models locally with llama-cpp-python (GGUF format)"

        # Configuration
        self.model_path = os.getenv("LLAMA_MODEL_PATH", "models/llama-2-7b.Q4_K_M.gguf")
        self.n_ctx = int(os.getenv("LLAMA_CONTEXT_SIZE", "2048"))
        self.n_threads = int(os.getenv("LLAMA_THREADS", os.cpu_count() or 4))
        self.n_gpu_layers = int(os.getenv("LLAMA_GPU_LAYERS", "0"))  # 0 = CPU only

        self.llm: Optional[Llama] = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the LLaMA model if available"""
        if not LLAMA_CPP_AVAILABLE:
            return

        # Check if model file exists
        if not Path(self.model_path).exists():
            logger.warning(f"Model file not found: {self.model_path}")
            return

        try:
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
            logger.info(f"LLaMA model loaded: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load LLaMA model: {e}")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute LLaMA inference

        Args:
            action (str): Action to perform (generate, chat, embed)
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not LLAMA_CPP_AVAILABLE:
            return {
                "status": "error",
                "message": "llama-cpp-python not installed. Install with: pip install llama-cpp-python"
            }

        if not self.llm:
            return {
                "status": "error",
                "message": f"Model not loaded. Check model path: {self.model_path}"
            }

        try:
            action = kwargs.get("action", "generate")

            if action == "generate":
                return await self._generate(**kwargs)
            elif action == "chat":
                return await self._chat(**kwargs)
            elif action == "embed":
                return await self._embed(**kwargs)
            elif action == "load_model":
                return await self._load_model(**kwargs)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"LLaMA error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _generate(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text from prompt
        """
        try:
            prompt = kwargs.get("prompt", "")
            max_tokens = kwargs.get("max_tokens", 512)
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.95)
            top_k = kwargs.get("top_k", 40)
            repeat_penalty = kwargs.get("repeat_penalty", 1.1)
            stop = kwargs.get("stop", [])
            echo = kwargs.get("echo", False)

            response = self.llm(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop if stop else None,
                echo=echo
            )

            return {
                "status": "success",
                "text": response["choices"][0]["text"],
                "finish_reason": response["choices"][0]["finish_reason"],
                "usage": response["usage"]
            }

        except Exception as e:
            logger.error(f"LLaMA generate error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with conversation history
        """
        try:
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 512)
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.95)
            top_k = kwargs.get("top_k", 40)
            repeat_penalty = kwargs.get("repeat_penalty", 1.1)

            # If single message, convert to messages format
            if "prompt" in kwargs and not messages:
                messages = [{"role": "user", "content": kwargs["prompt"]}]

            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty
            )

            return {
                "status": "success",
                "response": response["choices"][0]["message"]["content"],
                "finish_reason": response["choices"][0]["finish_reason"],
                "usage": response["usage"]
            }

        except Exception as e:
            logger.error(f"LLaMA chat error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))

            embedding = self.llm.embed(text)

            return {
                "status": "success",
                "embedding": embedding,
                "dimensions": len(embedding)
            }

        except Exception as e:
            logger.error(f"LLaMA embed error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _load_model(self, **kwargs) -> Dict[str, Any]:
        """
        Load a different model
        """
        try:
            model_path = kwargs.get("model_path", "")
            n_ctx = kwargs.get("n_ctx", self.n_ctx)
            n_gpu_layers = kwargs.get("n_gpu_layers", self.n_gpu_layers)

            if not model_path:
                return {"status": "error", "message": "model_path required"}

            if not Path(model_path).exists():
                return {
                    "status": "error",
                    "message": f"Model file not found: {model_path}"
                }

            # Unload current model
            if self.llm:
                del self.llm

            # Load new model
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )

            self.model_path = model_path
            self.n_ctx = n_ctx
            self.n_gpu_layers = n_gpu_layers

            return {
                "status": "success",
                "message": f"Model loaded: {model_path}",
                "model_path": model_path,
                "context_size": n_ctx,
                "gpu_layers": n_gpu_layers
            }

        except Exception as e:
            logger.error(f"LLaMA load model error: {str(e)}")
            return {"status": "error", "message": str(e)}
