"""
ExLlama/ExLlamaV2 Plugin
Supports quantized model inference using ExLlama libraries
"""

from typing import Dict, Any, Optional, List
import os


class ExLlamaPlugin:
    """Plugin for ExLlama/ExLlamaV2 quantized model inference"""

    name = "exllama"
    version = "1.0.0"
    description = "Local quantized model inference using ExLlama/ExLlamaV2"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.generator = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the ExLlama plugin"""
        try:
            # Try to import ExLlamaV2 first, fall back to ExLlama
            try:
                import exllamav2
                self.exllama_version = "v2"
            except ImportError:
                try:
                    import exllama
                    self.exllama_version = "v1"
                except ImportError:
                    print("Neither exllamav2 nor exllama packages found. Install with: pip install exllamav2 or pip install exllama")
                    return False

            # No API key needed for local models
            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing ExLlama plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an ExLlama action"""
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
        """Load an ExLlama quantized model"""
        model_path = params.get("model_path")
        if not model_path:
            return {"error": "model_path required"}

        if not os.path.exists(model_path):
            return {"error": f"Model directory not found: {model_path}"}

        try:
            if self.exllama_version == "v2":
                return self._load_exllamav2_model(params)
            else:
                return self._load_exllama_model(params)

        except Exception as e:
            return {"error": f"Failed to load model: {str(e)}"}

    def _load_exllamav2_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load ExLlamaV2 model"""
        from exllamav2 import ExLlamaV2, ExLlamaV2Tokenizer, ExLlamaV2Config

        model_path = params.get("model_path")

        # Load config
        config = ExLlamaV2Config()
        config.model_dir = model_path
        config.prepare()

        # Load model
        self.model = ExLlamaV2(config)
        self.model.load()

        # Load tokenizer
        self.tokenizer = ExLlamaV2Tokenizer(config)

        return {
            "status": "loaded",
            "model_path": model_path,
            "version": "ExLlamaV2"
        }

    def _load_exllama_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load ExLlama v1 model"""
        from exllama.model import ExLlama
        from exllama.tokenizer import ExLlamaTokenizer
        from exllama.generator import ExLlamaGenerator

        model_path = params.get("model_path")

        # Load model
        self.model = ExLlama.from_pretrained(model_path)

        # Load tokenizer
        self.tokenizer = ExLlamaTokenizer(self.model.tokenizer_path)

        # Create generator
        self.generator = ExLlamaGenerator(self.model, self.tokenizer)

        return {
            "status": "loaded",
            "model_path": model_path,
            "version": "ExLlama"
        }

    def _text_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text"""
        if not self.model:
            return {"error": "No model loaded. Use load_model action first."}

        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 256)
        temperature = params.get("temperature", 0.8)
        top_p = params.get("top_p", 0.95)
        top_k = params.get("top_k", 40)

        try:
            if self.exllama_version == "v2":
                return self._text_generation_v2(prompt, max_tokens, temperature, top_p, top_k)
            else:
                return self._text_generation_v1(prompt, max_tokens, temperature, top_p, top_k)

        except Exception as e:
            return {"error": f"Text generation failed: {str(e)}"}

    def _text_generation_v2(self, prompt: str, max_tokens: int, temperature: float,
                          top_p: float, top_k: int) -> Dict[str, Any]:
        """Text generation with ExLlamaV2"""
        from exllamav2 import ExLlamaV2Sampler

        # Tokenize prompt
        input_ids = self.tokenizer.encode(prompt)
        prompt_tokens = input_ids.shape[-1]

        # Create sampler
        sampler = ExLlamaV2Sampler.Settings()
        sampler.temperature = temperature
        sampler.top_p = top_p
        sampler.top_k = top_k

        # Generate
        generated_ids = self.model.generate(
            input_ids,
            sampler,
            max_tokens,
            stop_conditions=[]
        )

        # Decode output
        output_text = self.tokenizer.decode(generated_ids)[len(prompt):]

        return {
            "text": output_text,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": generated_ids.shape[-1] - prompt_tokens,
                "total_tokens": generated_ids.shape[-1]
            }
        }

    def _text_generation_v1(self, prompt: str, max_tokens: int, temperature: float,
                          top_p: float, top_k: int) -> Dict[str, Any]:
        """Text generation with ExLlama v1"""
        # Set generator settings
        self.generator.settings.temperature = temperature
        self.generator.settings.top_p = top_p
        self.generator.settings.top_k = top_k

        # Generate
        output = self.generator.generate_simple(prompt, max_tokens)

        # Estimate token usage (approximate)
        prompt_tokens = len(self.tokenizer.encode(prompt))
        completion_tokens = len(self.tokenizer.encode(output)) - prompt_tokens

        return {
            "text": output[len(prompt):],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion"""
        if not self.model:
            return {"error": "No model loaded. Use load_model action first."}

        messages = params.get("messages", [])
        max_tokens = params.get("max_tokens", 256)
        temperature = params.get("temperature", 0.8)
        top_p = params.get("top_p", 0.95)
        top_k = params.get("top_k", 40)

        try:
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)

            # Generate response
            result = self._text_generation({
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            })

            return {
                "response": result["text"],
                "usage": result["usage"]
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
        self.tokenizer = None
        self.generator = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = ExLlamaPlugin
PLUGIN_NAME = "exllama"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Local quantized model inference using ExLlama/ExLlamaV2"
PLUGIN_ACTIONS = [
    "load_model", "text_generation", "chat"
]