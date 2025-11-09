"""
Kosmos-2 Multimodal Model Plugin
Supports vision and language understanding with grounding capabilities
"""

from typing import Dict, Any, Optional, List, Union
import os
import base64
import io
from PIL import Image


class KosmosPlugin:
    """Plugin for Kosmos-2 multimodal model"""
    
    name = "kosmos"
    version = "1.0.0"
    description = "Integration with Kosmos-2 multimodal model for vision and language understanding"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.model = None
        self.processor = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Kosmos-2 plugin"""
        try:
            # Try to import transformers
            try:
                from transformers import AutoProcessor, Kosmos2ForConditionalGeneration
                import torch
            except ImportError:
                print("transformers and torch packages required. Install with: pip install transformers torch")
                return False
            
            # Load model and processor
            model_name = "microsoft/kosmos-2-patch14-224"
            
            try:
                self.processor = AutoProcessor.from_pretrained(model_name)
                self.model = Kosmos2ForConditionalGeneration.from_pretrained(model_name)
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    self.model = self.model.to("cuda")
                    
                self._initialized = True
                return True
                
            except Exception as e:
                print(f"Error loading Kosmos-2 model: {e}")
                print("Model will be downloaded on first use (requires internet connection)")
                return False
                
        except Exception as e:
            print(f"Error initializing Kosmos-2 plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Kosmos-2 action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please ensure transformers and torch are installed."}
        
        try:
            if action == "image_captioning":
                return self._image_captioning(params)
            elif action == "visual_question_answering":
                return self._visual_question_answering(params)
            elif action == "grounded_captioning":
                return self._grounded_captioning(params)
            elif action == "referring_expression_comprehension":
                return self._referring_expression_comprehension(params)
            elif action == "multimodal_chat":
                return self._multimodal_chat(params)
            elif action == "object_detection":
                return self._object_detection(params)
            elif action == "text_grounding":
                return self._text_grounding(params)
            elif action == "image_description":
                return self._image_description(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _load_image(self, image_input: Union[str, bytes, Image.Image]) -> Image.Image:
        """Load image from various input formats"""
        if isinstance(image_input, Image.Image):
            return image_input
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, str):
            if os.path.exists(image_input):
                return Image.open(image_input)
            else:
                # Assume base64 string
                image_data = base64.b64decode(image_input)
                return Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Unsupported image input format")
    
    def _image_captioning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate caption for image"""
        image_input = params.get("image")
        if not image_input:
            return {"error": "image parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            # Process image
            inputs = self.processor(text=["<image>Describe this image."], images=[image], return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs["pixel_values"],
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=128
                )
            
            # Decode generated text
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Extract caption (remove special tokens)
            caption = self.processor.post_process_generation(generated_text)[0]
            
            return {
                "caption": caption,
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error generating caption: {str(e)}"}
    
    def _visual_question_answering(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about image content"""
        image_input = params.get("image")
        question = params.get("question", "")
        
        if not image_input:
            return {"error": "image parameter required"}
        if not question:
            return {"error": "question parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            # Format prompt for VQA
            prompt = f"<image>{question}"
            
            # Process inputs
            inputs = self.processor(text=[prompt], images=[image], return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate answer
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs["pixel_values"],
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=128
                )
            
            # Decode answer
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            answer = self.processor.post_process_generation(generated_text)[0]
            
            return {
                "question": question,
                "answer": answer,
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error answering question: {str(e)}"}
    
    def _grounded_captioning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate caption with grounding (bounding boxes)"""
        image_input = params.get("image")
        if not image_input:
            return {"error": "image parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            # Process for grounded captioning
            prompt = "<image>Detailed description with object locations:"
            inputs = self.processor(text=[prompt], images=[image], return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate grounded caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs["pixel_values"],
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=256
                )
            
            # Decode and extract entities with bounding boxes
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Post-process to extract entities and their locations
            processed_output = self.processor.post_process_generation(generated_text)
            
            return {
                "caption": processed_output[0] if processed_output else generated_text,
                "entities": self._extract_entities(generated_text),
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error generating grounded caption: {str(e)}"}
    
    def _referring_expression_comprehension(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Locate objects described by referring expressions"""
        image_input = params.get("image")
        expression = params.get("expression", "")
        
        if not image_input:
            return {"error": "image parameter required"}
        if not expression:
            return {"error": "expression parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            # Format prompt for referring expression
            prompt = f"<image>Locate: {expression}"
            inputs = self.processor(text=[prompt], images=[image], return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs["pixel_values"],
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=128
                )
            
            # Decode response
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            processed_output = self.processor.post_process_generation(generated_text)
            
            return {
                "expression": expression,
                "location": processed_output[0] if processed_output else generated_text,
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error locating object: {str(e)}"}
    
    def _multimodal_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chat with multimodal context"""
        image_input = params.get("image")
        messages = params.get("messages", [])
        
        if not messages:
            return {"error": "messages parameter required"}
        
        try:
            # Build conversation context
            if image_input:
                image = self._load_image(image_input)
                # Add image token to first message
                if messages and isinstance(messages[0], str):
                    messages[0] = f"<image>{messages[0]}"
                elif messages and isinstance(messages[0], dict) and "content" in messages[0]:
                    messages[0]["content"] = f"<image>{messages[0]['content']}"
            
            # Process the last message as input
            last_message = messages[-1] if isinstance(messages[-1], str) else messages[-1].get("content", "")
            
            inputs = self.processor(text=[last_message], images=[image] if image_input else None, return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs.get("pixel_values"),
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=256
                )
            
            # Decode response
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            response = self.processor.post_process_generation(generated_text)
            
            return {
                "response": response[0] if response else generated_text,
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error in multimodal chat: {str(e)}"}
    
    def _object_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects in image"""
        image_input = params.get("image")
        if not image_input:
            return {"error": "image parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            # Prompt for object detection
            prompt = "<image>List all objects with their locations:"
            inputs = self.processor(text=[prompt], images=[image], return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate object detection
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs["pixel_values"],
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=256
                )
            
            # Decode and extract objects
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            entities = self._extract_entities(generated_text)
            
            return {
                "objects": entities,
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error detecting objects: {str(e)}"}
    
    def _text_grounding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ground text phrases to image regions"""
        image_input = params.get("image")
        phrases = params.get("phrases", [])
        
        if not image_input:
            return {"error": "image parameter required"}
        if not phrases:
            return {"error": "phrases parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            results = []
            for phrase in phrases:
                prompt = f"<image>Find: {phrase}"
                inputs = self.processor(text=[prompt], images=[image], return_tensors="pt")
                
                # Move to GPU if available
                if hasattr(self.model, 'device'):
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                
                # Generate grounding
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        pixel_values=inputs["pixel_values"],
                        input_ids=inputs["input_ids"],
                        attention_mask=inputs["attention_mask"],
                        image_embeds=None,
                        max_new_tokens=128
                    )
                
                # Decode response
                generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                processed_output = self.processor.post_process_generation(generated_text)
                
                results.append({
                    "phrase": phrase,
                    "grounding": processed_output[0] if processed_output else generated_text,
                    "raw_text": generated_text
                })
            
            return {
                "groundings": results,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error grounding text: {str(e)}"}
    
    def _image_description(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed image description"""
        image_input = params.get("image")
        detail_level = params.get("detail_level", "medium")  # low, medium, high
        
        if not image_input:
            return {"error": "image parameter required"}
        
        try:
            image = self._load_image(image_input)
            
            # Adjust prompt based on detail level
            if detail_level == "low":
                prompt = "<image>Brief description:"
            elif detail_level == "high":
                prompt = "<image>Very detailed description including colors, objects, spatial relationships, and context:"
            else:  # medium
                prompt = "<image>Detailed description:"
            
            inputs = self.processor(text=[prompt], images=[image], return_tensors="pt")
            
            # Move to GPU if available
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate description
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs["pixel_values"],
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    image_embeds=None,
                    max_new_tokens=512 if detail_level == "high" else 256
                )
            
            # Decode description
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            description = self.processor.post_process_generation(generated_text)
            
            return {
                "description": description[0] if description else generated_text,
                "detail_level": detail_level,
                "raw_text": generated_text,
                "model": "kosmos-2"
            }
            
        except Exception as e:
            return {"error": f"Error generating description: {str(e)}"}
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities and their bounding boxes from generated text"""
        entities = []
        
        # Kosmos-2 uses special format for entities: <phrase> (x1, y1, x2, y2)
        # This is a simplified extraction - actual implementation would parse the specific format
        import re
        
        # Pattern to match entities with bounding boxes
        pattern = r'<([^>]+)>\s*\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            phrase = match[0]
            x1, y1, x2, y2 = map(int, match[1:5])
            
            entities.append({
                "phrase": phrase,
                "bounding_box": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
            })
        
        return entities
    
    def cleanup(self):
        """Cleanup resources"""
        if self.model:
            del self.model
        if self.processor:
            del self.processor
        self.model = None
        self.processor = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = KosmosPlugin
PLUGIN_NAME = "kosmos"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Kosmos-2 multimodal model for vision and language understanding"
PLUGIN_ACTIONS = [
    "image_captioning", "visual_question_answering", "grounded_captioning",
    "referring_expression_comprehension", "multimodal_chat", "object_detection",
    "text_grounding", "image_description"
]