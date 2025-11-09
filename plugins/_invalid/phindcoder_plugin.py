"""
Phind CodeLlama Model Provider Plugin
Supports Phind's fine-tuned CodeLlama models for advanced code generation
"""

from typing import Dict, Any, Optional, List
import os


class PhindCoderPlugin:
    """Plugin for Phind CodeLlama models"""

    name = "phindcoder"
    version = "1.0.0"
    description = "Integration with Phind CodeLlama for advanced code generation"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the PhindCoder plugin"""
        try:
            from huggingface_hub import InferenceClient

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
            )

            if not self.api_key:
                return False

            self.client = InferenceClient(token=self.api_key)
            self._initialized = True
            return True

        except ImportError:
            print("huggingface_hub package not installed. Install with: pip install huggingface_hub")
            return False
        except Exception as e:
            print(f"Error initializing PhindCoder plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PhindCoder action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}

        try:
            if action == "code_generation":
                return self._code_generation(params)
            elif action == "code_completion":
                return self._code_completion(params)
            elif action == "chat":
                return self._chat(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _code_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced code generation"""
        prompt = params.get("prompt", "")
        model = params.get("model", "Phind/Phind-CodeLlama-34B-v2")
        language = params.get("language", "")
        task = params.get("task", "")

        max_tokens = params.get("max_tokens", 1024)
        temperature = params.get("temperature", 0.2)
        top_p = params.get("top_p", 0.95)

        # Enhanced prompt for code generation
        enhanced_prompt = self._enhance_code_prompt(prompt, language, task)

        result = self.client.text_generation(
            prompt=enhanced_prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            return_full_text=False
        )

        # Extract code from response
        generated_code = self._extract_code(result)

        return {
            "code": generated_code,
            "full_response": result,
            "model": model,
            "language": language,
            "task": task
        }

    def _code_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Code completion"""
        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        model = params.get("model", "Phind/Phind-CodeLlama-34B-v2")

        max_tokens = params.get("max_tokens", 512)
        temperature = params.get("temperature", 0.1)

        # Create completion prompt
        prompt = f"{prefix}<FILL_ME>{suffix}"

        result = self.client.text_generation(
            prompt=prompt,
            model=model,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=False,
            return_full_text=False
        )

        # Extract completion
        completion = result.split("<FILL_ME>")[0] if "<FILL_ME>" in result else result

        return {
            "completion": completion,
            "full_response": result,
            "model": model
        }

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat completion with coding focus"""
        messages = params.get("messages", [])
        model = params.get("model", "Phind/Phind-CodeLlama-34B-v2")
        max_tokens = params.get("max_tokens", 1024)
        temperature = params.get("temperature", 0.3)

        # Convert messages to chat format
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                chat_messages.append({"role": "system", "content": content})
            elif role == "user":
                chat_messages.append({"role": "user", "content": content})
            elif role == "assistant":
                chat_messages.append({"role": "assistant", "content": content})

        response = self.client.chat_completion(
            messages=chat_messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return {
            "response": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    def _enhance_code_prompt(self, prompt: str, language: str, task: str) -> str:
        """Enhance prompt for better code generation"""
        enhanced = ""

        if language:
            enhanced += f"Language: {language}\n"

        if task:
            enhanced += f"Task: {task}\n"

        enhanced += f"Generate code for: {prompt}\n\n"

        # Add instructions for Phind CodeLlama
        enhanced += "Please provide a complete, working code solution with proper syntax and comments.\n\n"

        return enhanced

    def _extract_code(self, response: str) -> str:
        """Extract code from model response"""
        # Look for code blocks
        import re

        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()

        # If no code blocks, return the response as is
        return response.strip()

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = PhindCoderPlugin
PLUGIN_NAME = "phindcoder"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Phind CodeLlama for advanced code generation"
PLUGIN_ACTIONS = ["code_generation", "code_completion", "chat"]