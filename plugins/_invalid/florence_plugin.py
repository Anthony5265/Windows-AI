"""
Florence-2 Vision Model Plugin
Supports various vision tasks including captioning, object detection, OCR, and region analysis
"""

from typing import Dict, Any, Optional, List
import os
import base64
import io
from PIL import Image


class FlorencePlugin:
    """Plugin for Florence-2 vision foundation model"""

    name = "florence"
    version = "1.0.0"
    description = "Integration with Florence-2 for various vision tasks"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Florence-2 plugin"""
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM

            # Set device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # Model selection
            model_name = config.get("model", "microsoft/Florence-2-base") if config else "microsoft/Florence-2-base"

            # Load processor and model
            self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
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
            print(f"Error initializing Florence-2 plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Florence-2 action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check dependencies."}

        try:
            if action == "caption":
                return self._caption(params)
            elif action == "detailed_caption":
                return self._detailed_caption(params)
            elif action == "more_detailed_caption":
                return self._more_detailed_caption(params)
            elif action == "object_detection":
                return self._object_detection(params)
            elif action == "dense_region_caption":
                return self._dense_region_caption(params)
            elif action == "region_proposal":
                return self._region_proposal(params)
            elif action == "ocr":
                return self._ocr(params)
            elif action == "ocr_with_region":
                return self._ocr_with_region(params)
            elif action == "caption_to_phrase_grounding":
                return self._caption_to_phrase_grounding(params)
            elif action == "visual_question_answering":
                return self._visual_question_answering(params)
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

    def _generate_response(self, task_prompt: str, image: Image.Image, text_input: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate response using Florence-2"""
        import torch

        # Prepare prompt
        if text_input:
            prompt = task_prompt + text_input
        else:
            prompt = task_prompt

        # Process inputs
        inputs = self.processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generation parameters
        max_new_tokens = kwargs.get("max_new_tokens", 1024)
        num_beams = kwargs.get("num_beams", 3)
        do_sample = kwargs.get("do_sample", False)

        # Generate response
        with torch.no_grad():
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=max_new_tokens,
                num_beams=num_beams,
                do_sample=do_sample
            )

        # Decode response
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

        # Post-process based on task
        parsed_answer = self.processor.post_process_generation(
            generated_text,
            task=task_prompt,
            image_size=(image.width, image.height)
        )

        return {
            "generated_text": generated_text,
            "parsed_answer": parsed_answer
        }

    def _caption(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic image caption"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<CAPTION>", image)

        return {
            "caption": result["parsed_answer"]["<CAPTION>"],
            "model": "florence-2"
        }

    def _detailed_caption(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed image caption"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<DETAILED_CAPTION>", image)

        return {
            "caption": result["parsed_answer"]["<DETAILED_CAPTION>"],
            "model": "florence-2"
        }

    def _more_detailed_caption(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate more detailed image caption"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<MORE_DETAILED_CAPTION>", image)

        return {
            "caption": result["parsed_answer"]["<MORE_DETAILED_CAPTION>"],
            "model": "florence-2"
        }

    def _object_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects in image"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<OD>", image)

        od_result = result["parsed_answer"]["<OD>"]

        return {
            "bboxes": od_result["bboxes"],
            "labels": od_result["labels"],
            "model": "florence-2"
        }

    def _dense_region_caption(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate captions for dense regions in image"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<DENSE_REGION_CAPTION>", image)

        drc_result = result["parsed_answer"]["<DENSE_REGION_CAPTION>"]

        return {
            "bboxes": drc_result["bboxes"],
            "labels": drc_result["labels"],
            "model": "florence-2"
        }

    def _region_proposal(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate region proposals for image"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<REGION_PROPOSAL>", image)

        rp_result = result["parsed_answer"]["<REGION_PROPOSAL>"]

        return {
            "bboxes": rp_result["bboxes"],
            "labels": rp_result["labels"],
            "model": "florence-2"
        }

    def _ocr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<OCR>", image)

        return {
            "text": result["parsed_answer"]["<OCR>"],
            "model": "florence-2"
        }

    def _ocr_with_region(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text with region information from image"""
        image_input = params.get("image")

        if not image_input:
            return {"error": "image parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<OCR_WITH_REGION>", image)

        ocr_result = result["parsed_answer"]["<OCR_WITH_REGION>"]

        return {
            "quad_boxes": ocr_result["quad_boxes"],
            "labels": ocr_result["labels"],
            "model": "florence-2"
        }

    def _caption_to_phrase_grounding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ground phrases from a caption to image regions"""
        image_input = params.get("image")
        caption = params.get("caption", "")

        if not image_input:
            return {"error": "image parameter required"}
        if not caption:
            return {"error": "caption parameter required"}

        image = self._load_image(image_input)

        result = self._generate_response("<CAPTION_TO_PHRASE_GROUNDING>", image, caption)

        grounding_result = result["parsed_answer"]["<CAPTION_TO_PHRASE_GROUNDING>"]

        return {
            "bboxes": grounding_result["bboxes"],
            "labels": grounding_result["labels"],
            "caption": caption,
            "model": "florence-2"
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

        # Use detailed caption task for VQA by framing question as prompt
        prompt = f"<MORE_DETAILED_CAPTION>Question: {question}"

        result = self._generate_response(prompt, image, max_new_tokens=512)

        # Extract answer from the generated detailed caption
        answer = result["parsed_answer"].get("<MORE_DETAILED_CAPTION>", "")

        return {
            "question": question,
            "answer": answer,
            "model": "florence-2"
        }

    def cleanup(self):
        """Cleanup resources"""
        if self.model:
            import torch
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        self.processor = None
        self.device = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = FlorencePlugin
PLUGIN_NAME = "florence"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Florence-2 for various vision tasks"
PLUGIN_ACTIONS = [
    "caption", "detailed_caption", "more_detailed_caption",
    "object_detection", "dense_region_caption", "region_proposal",
    "ocr", "ocr_with_region", "caption_to_phrase_grounding",
    "visual_question_answering"
]