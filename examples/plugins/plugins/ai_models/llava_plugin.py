"""
LLaVA Vision Model Plugin
Large Language and Vision Assistant
"""

from typing import Dict, Any, Optional, List
import os


class LLaVAPlugin:
    """Plugin for LLaVA vision model"""
    
    name = "llava"
    version = "1.0.0"
    description = "Integration with LLaVA (Large Language and Vision Assistant)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.image_processor = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LLaVA plugin"""
        try:
            from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
            import torch
            
            model_name = (
                config.get("model_name") if config 
                else "llava-hf/llava-v1.6-mistral-7b-hf"
            )
            
            self.processor = LlavaNextProcessor.from_pretrained(model_name)
            self.model = LlavaNextForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            self._initialized = True
            return True
            
        except ImportError:
            print("transformers not installed. Install with: pip install transformers torch pillow")
            return False
        except Exception as e:
            print(f"Error initializing LLaVA plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LLaVA action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "analyze":
                return self._analyze_image(params)
            elif action == "chat":
                return self._vision_chat(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image with text prompt"""
        from PIL import Image
        
        image_path = params.get("image_path", "")
        prompt = params.get("prompt", "Describe this image in detail")
        max_length = params.get("max_length", 200)
        
        if not os.path.exists(image_path):
            return {"success": False, "error": "Image not found"}
        
        image = Image.open(image_path)
        
        # Format prompt for LLaVA
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        prompt_text = self.processor.apply_chat_template(conversation, add_generation_prompt=True)
        inputs = self.processor(prompt_text, image, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_length,
            do_sample=False
        )
        
        response = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "success": True,
            "response": response
        }
    
    def _vision_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-turn chat with vision"""
        from PIL import Image
        
        image_path = params.get("image_path", "")
        messages = params.get("messages", [])
        
        if not os.path.exists(image_path):
            return {"success": False, "error": "Image not found"}
        
        image = Image.open(image_path)
        
        prompt_text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(prompt_text, image, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(**inputs, max_new_tokens=200)
        response = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        return {
            "success": True,
            "response": response
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.processor = None
        return True
