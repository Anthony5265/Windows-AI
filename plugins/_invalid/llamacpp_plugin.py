"""
Llama.cpp Plugin
Supports GGUF model inference using llama.cpp
"""

from typing import Dict, Any, Optional, List
import os


class LlamaCppPlugin:
    """Plugin for Llama.cpp GGUF model inference"""

    name = "llamacpp"
    version = "1.0.0"
    description = "Local GGUF model inference using llama.cpp"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Llama.cpp plugin"""
        try:
            from llama_cpp import Llama

            # No API key needed for local models
            self._initialized = True
            return True

        except ImportError:
            print("llama-cpp-python package not installed. Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            print(f"Error initializing Llama.cpp plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Llama.cpp action"""
        if not self._initialized:
            return {"error": "Plugin not initialized."}

        try:
            if action == "load_model":
                return self._load_model(params)
            elif action == "text_generation":
                return self._text_generation(params)
            elif action == "chat":
                return self._chat(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _load_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load a GGUF model"""
        model_path = params.get("model_path")
        if not model_path:
            return {"error": "model_path required"}

        if not os.path.exists(model_path):
            return {"error": f"Model file not found: {model_path}"}

        try:
            from llama_cpp import Llama

            # Optional parameters
            n_ctx = params.get("n_ctx", 2048)
            n_threads = params.get("n_threads", -1)  # Use all available threads
            n_gpu_layers = params.get("n_gpu_layers", 0)

            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )

            return {
                "status": "loaded",
                "model_path": model_path,
                "n_ctx": n_ctx
            }

        except Exception as e:
            return {"error": f"Failed to load model: {str(e)}"}

    def _text_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        if not self.model:
            return {"error": "No model loaded. Use load_model action first."}

        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 256)
        temperature = params.get("temperature", 0.8)
        top_p = params.get("top_p", 0.95)
        stop = params.get("stop", [])

        try:
            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                echo=False
            )

            return {
                "text": output["choices"][0]["text"],
                "usage": {
                    "prompt_tokens": output["usage"]["prompt_tokens"],
                    "completion_tokens": output["usage"]["completion_tokens"],
                    "total_tokens": output["usage"]["total_tokens"]
                }
            }

        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        if not self.model:
            return {"error": "No model loaded. Use load_model action first."}

        messages = params.get("messages", [])
        max_tokens = params.get("max_tokens", 256)
        temperature = params.get("temperature", 0.8)
        top_p = params.get("top_p", 0.95)

        try:
            # Convert messages to prompt format
            prompt = self._messages_to_prompt(messages)

            output = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                echo=False
            )

            return {
                "response": output["choices"][0]["text"],
                "usage": {
                    "prompt_tokens": output["usage"]["prompt_tokens"],
                    "completion_tokens": output["usage"]["completion_tokens"],
                    "total_tokens": output["usage"]["total_tokens"]
                }
            }

        except Exception as e:
            return {"error": f"Chat completion failed: {str(e)}"}

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to prompt format"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n".join(prompt_parts) + "\nAssistant:"

    def cleanup(self):
        """Cleanup resources"""
        self.model = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = LlamaCppPlugin
PLUGIN_NAME = "llamacpp"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Local GGUF model inference using llama.cpp"
PLUGIN_ACTIONS = [
    "load_model", "text_generation", "chat"
]