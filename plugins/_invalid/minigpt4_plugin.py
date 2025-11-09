"""
MiniGPT-4 Vision-Language Model Plugin
Supports multimodal chat with image and text inputs
"""

from typing import Dict, Any, Optional, List
import os
import base64
from PIL import Image
import io


class MiniGPT4Plugin:
    """Plugin for MiniGPT-4 vision-language model"""
    
    name = "minigpt4"
    version = "1.0.0"
    description = "Integration with MiniGPT-4 for vision-language chat"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.model_path: Optional[str] = None
        self.device: str = "cuda"
        self._initialized = False
        self.model = None
        self.processor = None
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the MiniGPT-4 plugin"""
        try:
            # Check for local model path or use default
            self.model_path = (
                config.get("model_path") if config 
                else os.getenv("MINIGPT4_MODEL_PATH")
            )
            
            self.device = config.get("device", "cuda") if config else "cuda"
            
            # Try to import required libraries
            try:
                import torch
                from transformers import AutoTokenizer, AutoModelForCausalLM
                from transformers import Blip2Processor, Blip2ForConditionalGeneration
            except ImportError:
                print("Required packages not installed. Install with: pip install torch transformers pillow")
                return False
            
            # Initialize model and processor
            if self.model_path and os.path.exists(self.model_path):
                # Load local model
                self.processor = Blip2Processor.from_pretrained(self.model_path)
                self.model = Blip2ForConditionalGeneration.from_pretrained(
                    self.model_path, 
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
            else:
                # Use default MiniGPT-4 model from Hugging Face
                model_name = "Salesforce/blip2-flan-t5-xxl"
                self.processor = Blip2Processor.from_pretrained(model_name)
                self.model = Blip2ForConditionalGeneration.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
            
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to(self.device)
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing MiniGPT-4 plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a MiniGPT-4 action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check model installation."}
        
        try:
            if action == "vision_chat":
                return self._vision_chat(params)
            elif action == "image_captioning":
                return self._image_captioning(params)
            elif action == "visual_question_answering":
                return self._visual_question_answering(params)
            elif action == "image_classification":
                return self._image_classification(params)
            elif action == "text_only_chat":
                return self._text_only_chat(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _load_image(self, image_input) -> Image.Image:
        """Load image from various input formats"""
        if isinstance(image_input, str):
            # File path
            if os.path.exists(image_input):
                return Image.open(image_input).convert('RGB')
            # Base64 string
            elif image_input.startswith('data:image'):
                # Remove data URL prefix
                base64_data = image_input.split(',')[1]
                image_data = base64.b64decode(base64_data)
                return Image.open(io.BytesIO(image_data)).convert('RGB')
            else:
                # Assume base64
                image_data = base64.b64decode(image_input)
                return Image.open(io.BytesIO(image_data)).convert('RGB')
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input)).convert('RGB')
        elif isinstance(image_input, Image.Image):
            return image_input.convert('RGB')
        else:
            raise ValueError("Unsupported image input format")
    
    def _vision_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vision-language chat with image and text"""
        image_input = params.get("image")
        prompt = params.get("prompt", "Describe this image in detail.")
        max_length = params.get("max_length", 512)
        temperature = params.get("temperature", 0.7)
        num_beams = params.get("num_beams", 5)
        
        if not image_input:
            return {"error": "image input required"}
        
        try:
            image = self._load_image(image_input)
            
            # Process image and text
            inputs = self.processor(image, prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    num_beams=num_beams,
                    early_stopping=True
                )
            
            # Decode response
            response = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            return {
                "response": response,
                "prompt": prompt,
                "model": "minigpt4",
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "num_beams": num_beams
                }
            }
            
        except Exception as e:
            return {"error": f"Vision chat failed: {str(e)}"}
    
    def _image_captioning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate caption for image"""
        image_input = params.get("image")
        max_length = params.get("max_length", 256)
        num_beams = params.get("num_beams", 3)
        
        if not image_input:
            return {"error": "image input required"}
        
        try:
            image = self._load_image(image_input)
            
            # Process image
            inputs = self.processor(image, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True
                )
            
            caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            return {
                "caption": caption,
                "model": "minigpt4",
                "parameters": {
                    "max_length": max_length,
                    "num_beams": num_beams
                }
            }
            
        except Exception as e:
            return {"error": f"Image captioning failed: {str(e)}"}
    
    def _visual_question_answering(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about images"""
        image_input = params.get("image")
        question = params.get("question", "What is in this image?")
        max_length = params.get("max_length", 256)
        temperature = params.get("temperature", 0.7)
        
        if not image_input:
            return {"error": "image input required"}
        
        if not question:
            return {"error": "question required"}
        
        try:
            image = self._load_image(image_input)
            
            # Format question for VQA
            prompt = f"Question: {question} Answer:"
            
            # Process image and question
            inputs = self.processor(image, prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate answer
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    early_stopping=True
                )
            
            answer = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            return {
                "question": question,
                "answer": answer,
                "model": "minigpt4",
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature
                }
            }
            
        except Exception as e:
            return {"error": f"Visual question answering failed: {str(e)}"}
    
    def _image_classification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classify image content"""
        image_input = params.get("image")
        categories = params.get("categories", [])
        
        if not image_input:
            return {"error": "image input required"}
        
        try:
            image = self._load_image(image_input)
            
            if categories:
                # Zero-shot classification with provided categories
                categories_text = ", ".join(categories)
                prompt = f"Which of these categories best describes this image: {categories_text}?"
            else:
                # General classification
                prompt = "What is the main subject or category of this image?"
            
            # Process image and prompt
            inputs = self.processor(image, prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate classification
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=128,
                    temperature=0.3,
                    early_stopping=True
                )
            
            classification = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            return {
                "classification": classification,
                "categories": categories if categories else None,
                "model": "minigpt4"
            }
            
        except Exception as e:
            return {"error": f"Image classification failed: {str(e)}"}
    
    def _text_only_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Text-only chat conversation"""
        prompt = params.get("prompt", "")
        max_length = params.get("max_length", 512)
        temperature = params.get("temperature", 0.7)
        
        if not prompt:
            return {"error": "prompt required"}
        
        try:
            # Use text-only mode (dummy image processing)
            import torch
            dummy_image = Image.new('RGB', (224, 224), color='white')
            
            inputs = self.processor(dummy_image, prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    early_stopping=True
                )
            
            response = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            return {
                "response": response,
                "prompt": prompt,
                "model": "minigpt4",
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature
                }
            }
            
        except Exception as e:
            return {"error": f"Text chat failed: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model and self.device == "cuda":
            import torch
            if hasattr(torch.cuda, 'empty_cache'):
                torch.cuda.empty_cache()
        
        self.model = None
        self.processor = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = MiniGPT4Plugin
PLUGIN_NAME = "minigpt4"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with MiniGPT-4 for vision-language chat"
PLUGIN_ACTIONS = [
    "vision_chat", "image_captioning", "visual_question_answering", 
    "image_classification", "text_only_chat"
]