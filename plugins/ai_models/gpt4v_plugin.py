"""
GPT-4 Vision Plugin
OpenAI's multimodal vision model
"""

from typing import Dict, Any, Optional, List
import os


class GPT4VisionPlugin:
    """Plugin for GPT-4 Vision"""

    name = "gpt4_vision"
    version = "1.0.0"
    description = "Integration with GPT-4 Vision for image understanding"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GPT-4 Vision plugin"""
        try:
            import openai

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("OPENAI_API_KEY")
            )

            if not self.api_key:
                return False

            openai.api_key = self.api_key
            self.client = openai
            self._initialized = True
            return True

        except ImportError:
            print("openai package not installed. Install with: pip install openai")
            return False
        except Exception as e:
            print(f"Error initializing GPT-4 Vision plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GPT-4 Vision action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "analyze":
                return self._analyze_image(params)
            elif action == "describe":
                return self._describe_image(params)
            elif action == "ocr":
                return self._ocr(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image with custom prompt"""
        image_url = params.get("image_url", "")
        prompt = params.get("prompt", "What's in this image?")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]

        response = self.client.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=500
        )

        return {
            "success": True,
            "response": response.choices[0].message.content
        }

    def _describe_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Describe image in detail"""
        image_url = params.get("image_url", "")

        return self._analyze_image({
            "image_url": image_url,
            "prompt": "Describe this image in detail."
        })

    def _ocr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from image"""
        image_url = params.get("image_url", "")

        return self._analyze_image({
            "image_url": image_url,
            "prompt": "Extract all text from this image."
        })

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
