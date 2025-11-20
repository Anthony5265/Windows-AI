"""
llama-cpp-python Plugin
Python bindings for llama.cpp
"""

from typing import Dict, Any, Optional, List
import os


class LlamaCppPythonPlugin:
    """Plugin for llama-cpp-python"""

    name = "llamacpp_python"
    version = "1.0.0"
    description = "Integration with llama-cpp-python for local inference"
    author = "Windows AI Team"

    def __init__(self):
        self.llm = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the llama-cpp-python plugin"""
        try:
            from llama_cpp import Llama

            model_path = config.get("model_path") if config else None

            if not model_path:
                return False

            self.llm = Llama(model_path=model_path)
            self._initialized = True
            return True

        except ImportError:
            print("llama-cpp-python package not installed. Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            print(f"Error initializing llama-cpp-python plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a llama-cpp-python action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate":
                return self._generate(params)
            elif action == "chat":
                return self._chat(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text completion"""
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 128)

        output = self.llm(prompt, max_tokens=max_tokens)

        return {
            "success": True,
            "response": output["choices"][0]["text"]
        }

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chat completion"""
        messages = params.get("messages", [])

        output = self.llm.create_chat_completion(messages=messages)

        return {
            "success": True,
            "response": output["choices"][0]["message"]["content"]
        }

    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text embeddings"""
        text = params.get("text", "")

        embedding = self.llm.embed(text)

        return {
            "success": True,
            "embedding": embedding
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.llm = None
        return True
