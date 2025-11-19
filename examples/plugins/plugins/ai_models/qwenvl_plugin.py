"""
Qwen-VL Plugin
Alibaba's vision-language model
"""

from typing import Dict, Any, Optional, List
import os


class QwenVLPlugin:
    """Plugin for Qwen-VL"""

    name = "qwen_vl"
    version = "1.0.0"
    description = "Integration with Qwen-VL vision-language model"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Qwen-VL plugin"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            model_name = config.get("model", "Qwen/Qwen-VL-Chat") if config else "Qwen/Qwen-VL-Chat"

            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
            self._initialized = True
            return True

        except ImportError:
            print("transformers package not installed. Install with: pip install transformers")
            return False
        except Exception as e:
            print(f"Error initializing Qwen-VL plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Qwen-VL action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "chat":
                return self._chat(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat about images"""
        image_path = params.get("image_path", "")
        question = params.get("question", "Describe this image")

        query = self.tokenizer.from_list_format([
            {'image': image_path},
            {'text': question}
        ])

        response, _ = self.model.chat(self.tokenizer, query=query, history=None)

        return {
            "success": True,
            "response": response
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.tokenizer = None
        return True
