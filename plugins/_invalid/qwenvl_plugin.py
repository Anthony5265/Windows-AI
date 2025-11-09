"""
Qwen-VL Model Provider Plugin
Supports Qwen-VL multimodal vision-language tasks
"""

from typing import Dict, Any, Optional, List
import os
import base64
import io
from PIL import Image


class QwenVLPlugin:
    """Plugin for Qwen-VL multimodal model"""

    name = "qwenvl"
    version = "1.0.0"
    description = "Integration with Qwen-VL for multimodal vision-language tasks"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Qwen-VL plugin"""
        try:
            import torch
            from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor

            # Set device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # Model selection
            model_name = config.get("model", "Qwen/Qwen2-VL-7B-Instruct") if config else "Qwen/Qwen2-VL-7B-Instruct"

            # Load tokenizer, processor and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                trust_remote_code=True
            )

            # Move to device
            self.model.to(self.device)

            # Set to eval mode
            self.model.eval()

            self._initialized = True
            return True

        except ImportError:
            print("Required packages not installed. Install with: pip install transformers torch pillow")
            return False
        except Exception as e:
            print(f"Error initializing Qwen-VL plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Qwen-VL action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check dependencies."}

        try:
            if action == "image_captioning":
                return self._image_captioning(params)
            elif action == "visual_question_answering":
                return self._visual_question_answering(params)
            elif action == "visual_reasoning":
                return self._visual_reasoning(params)
            elif action == "image_classification":
                return self._image_classification(params)
            elif action == "object_detection":
                return self._object_detection(params)
            elif action == "scene_understanding":
                return self._scene_understanding(params)
            elif action == "text_extraction":
                return self._text_extraction(params)
            elif action == "image_comparison":
                return self._image_comparison(params)
            elif action == "instruction_following":
                return self._instruction_following(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _load_image(self, image_input: Any) -> Image.Image:
        """Load image from various input formats"""
        if isinstance(image_input, str):
            # File path
            if os.path.exists(image_input):
                return Image.open(image_input).convert('RGB')
            # Base64 string
            elif image_input.startswith('data:image'):
                image_data = base64.b64decode(image_input.split(',')[1])
                return Image.open(io.BytesIO(image_data)).convert('RGB')
            else:
                # Assume base64 without data URL prefix
                image_data = base64.b64decode(image_input)
                return Image.open(io.BytesIO(image_data)).convert('RGB')
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input)).convert('RGB')
        elif isinstance(image_input, Image.Image):
            return image_input.convert('RGB')
        else:
            raise ValueError("Unsupported image input format")

    def _generate_response(self, image: Optional[Image.Image], prompt: str, **kwargs) -> str:
        """Generate response using Qwen-VL"""
        import torch

        # Prepare messages for Qwen-VL
        messages = []
        if image is not None:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # Process inputs
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.processor(
            text=[text],
            images=[image] if image is not None else None,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generation parameters
        max_new_tokens = kwargs.get("max_new_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 0.9)
        do_sample = kwargs.get("do_sample", True)

        # Generate response
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id
            )

        # Extract only the generated part (remove input)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]

        # Decode response
        response = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        return response

    def _image_captioning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image caption"""
        image_input = params.get("image")
        caption_type = params.get("caption_type", "detailed")  # brief, detailed, creative

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        # Different prompts for different caption types
        prompts = {
            "brief": "Briefly describe this image in one sentence.",
            "detailed": "Provide a detailed description of this image, including objects, scenes, and context.",
            "creative": "Describe this image in a creative and engaging way."
        }

        prompt = prompts.get(caption_type, prompts["detailed"])

        caption = self._generate_response(
            image,
            prompt,
            max_new_tokens=params.get("max_new_tokens", 150 if caption_type == "brief" else 300)
        )

        return {
            "caption": caption,
            "caption_type": caption_type,
            "model": "qwenvl"
        }

    def _visual_question_answering(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Answer questions about images"""
        image_input = params.get("image")
        question = params.get("question", "")

        if not image_input:
            return {"error": "image parameter required"}
        if not question:
            return {"error": "question parameter required"}

        image = self._load_image(image_input)

        answer = self._generate_response(
            image,
            question,
            max_new_tokens=params.get("max_new_tokens", 100),
            temperature=params.get("temperature", 0.7)
        )

        return {
            "question": question,
            "answer": answer,
            "model": "qwenvl"
        }

    def _visual_reasoning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform visual reasoning tasks"""
        image_input = params.get("image")
        task = params.get("task", "analyze")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        # Different reasoning tasks
        prompts = {
            "analyze": "Analyze this image and explain what you see in detail.",
            "compare": "Compare and contrast the main elements in this image.",
            "explain": "Explain the relationships between objects in this image.",
            "predict": "Based on this image, what might happen next?",
            "evaluate": "Evaluate the composition and visual elements of this image."
        }

        prompt = prompts.get(task, prompts["analyze"])

        reasoning = self._generate_response(
            image,
            prompt,
            max_new_tokens=params.get("max_new_tokens", 400)
        )

        return {
            "task": task,
            "reasoning": reasoning,
            "model": "qwenvl"
        }

    def _image_classification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classify image content"""
        image_input = params.get("image")
        categories = params.get("categories", [])

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        if categories:
            # Zero-shot classification with provided categories
            categories_str = ", ".join(categories)
            prompt = f"Classify this image into one of these categories: {categories_str}. Answer with just the category name."
        else:
            # General classification
            prompt = "What type of image is this? Provide the main category and subcategory."

        classification = self._generate_response(
            image,
            prompt,
            max_new_tokens=params.get("max_new_tokens", 50),
            temperature=0.3
        )

        return {
            "classification": classification,
            "categories_provided": categories,
            "model": "qwenvl"
        }

    def _object_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect and list objects in image"""
        image_input = params.get("image")
        object_type = params.get("object_type", "all")  # all, specific type

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        if object_type == "all":
            prompt = "List all objects you can identify in this image."
        else:
            prompt = f"Find and describe all {object_type} objects in this image."

        objects = self._generate_response(
            image,
            prompt,
            max_new_tokens=params.get("max_new_tokens", 300)
        )

        return {
            "objects": objects,
            "object_type": object_type,
            "model": "qwenvl"
        }

    def _scene_understanding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Understand and describe scene context"""
        image_input = params.get("image")
        aspect = params.get("aspect", "general")  # general, mood, setting, activity

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        prompts = {
            "general": "Describe the overall scene and context of this image.",
            "mood": "What is the mood and atmosphere of this scene?",
            "setting": "Where and when does this scene take place?",
            "activity": "What activities are happening in this scene?"
        }

        prompt = prompts.get(aspect, prompts["general"])

        scene_description = self._generate_response(
            image,
            prompt,
            max_new_tokens=params.get("max_new_tokens", 350)
        )

        return {
            "scene_description": scene_description,
            "aspect": aspect,
            "model": "qwenvl"
        }

    def _text_extraction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from images"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        prompt = "Extract all text visible in this image. If there's no text, say 'No text found'."

        extracted_text = self._generate_response(
            image,
            prompt,
            max_new_tokens=params.get("max_new_tokens", 500),
            temperature=0.1
        )

        return {
            "extracted_text": extracted_text,
            "model": "qwenvl"
        }

    def _image_comparison(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two images"""
        image1_input = params.get("image1")
        image2_input = params.get("image2")
        comparison_type = params.get("comparison_type", "similarities")  # similarities, differences, both

        if not image1_input or not image2_input:
            return {"error": "Both image1 and image2 parameters required"}

        image1 = self._load_image(image1_input)
        image2 = self._load_image(image2_input)

        prompts = {
            "similarities": "What are the similarities between these two images?",
            "differences": "What are the differences between these two images?",
            "both": "Compare these two images, describing both similarities and differences."
        }

        prompt = prompts.get(comparison_type, prompts["both"])

        # For comparison, we'll process each image separately and combine
        # This is a simplified approach - in practice, you might need a different strategy
        response1 = self._generate_response(image1, "Describe this image in detail.", max_new_tokens=200)
        response2 = self._generate_response(image2, "Describe this image in detail.", max_new_tokens=200)

        # Create a comparison prompt using both descriptions
        comparison_prompt = f"Image 1: {response1}\n\nImage 2: {response2}\n\n{prompt}"

        comparison = self._generate_response(
            image1,  # Use first image as context
            comparison_prompt,
            max_new_tokens=params.get("max_new_tokens", 400)
        )

        return {
            "comparison": comparison,
            "comparison_type": comparison_type,
            "image1_description": response1,
            "image2_description": response2,
            "model": "qwenvl"
        }

    def _instruction_following(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Follow custom instructions for image analysis"""
        image_input = params.get("image")
        instruction = params.get("instruction", "")

        if not image_input:
            return {"error": "image parameter required"}
        if not instruction:
            return {"error": "instruction parameter required"}

        image = self._load_image(image_input)

        response = self._generate_response(
            image,
            instruction,
            max_new_tokens=params.get("max_new_tokens", 500),
            temperature=params.get("temperature", 0.8)
        )

        return {
            "instruction": instruction,
            "response": response,
            "model": "qwenvl"
        }

    def cleanup(self):
        """Cleanup resources"""
        if self.model:
            import torch
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        self.processor = None
        self.tokenizer = None
        self.device = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = QwenVLPlugin
PLUGIN_NAME = "qwenvl"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Qwen-VL for multimodal vision-language tasks"
PLUGIN_ACTIONS = [
    "image_captioning", "visual_question_answering", "visual_reasoning",
    "image_classification", "object_detection", "scene_understanding",
    "text_extraction", "image_comparison", "instruction_following"
]