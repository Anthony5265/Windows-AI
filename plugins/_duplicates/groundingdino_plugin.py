"""
GroundingDINO Model Provider Plugin
Supports open-vocabulary object detection using text prompts
"""

from typing import Dict, Any, Optional, List, Tuple
import os
import numpy as np
from PIL import Image
import io
import base64


class GroundingDINOPlugin:
    """Plugin for GroundingDINO open-vocabulary object detection"""

    name = "groundingdino"
    version = "1.0.0"
    description = "Integration with GroundingDINO for open-vocabulary object detection"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GroundingDINO plugin"""
        try:
            # Try to import GroundingDINO dependencies
            try:
                import torch
                from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
            except ImportError:
                print("GroundingDINO dependencies not installed. Install with: pip install transformers torch")
                return False

            # Set device
            self.device = config.get("device", "cuda" if torch.cuda.is_available() else "cpu")

            # Model selection
            model_name = config.get("model", "IDEA-Research/grounding-dino-base") if config else "IDEA-Research/grounding-dino-base"

            # Load processor and model
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = AutoModelForZeroShotObjectDetection.from_pretrained(model_name)

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
            print(f"Error initializing GroundingDINO plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GroundingDINO action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check dependencies."}

        try:
            if action == "detect_objects_with_text":
                return self._detect_objects_with_text(params)
            elif action == "grounding_detection":
                return self._grounding_detection(params)
            elif action == "batch_detection":
                return self._batch_detection(params)
            elif action == "phrase_grounding":
                return self._phrase_grounding(params)
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
                return Image.open(io.BytesIO(image_input)).convert('RGB')
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input)).convert('RGB')
        elif isinstance(image_input, Image.Image):
            return image_input.convert('RGB')
        else:
            raise ValueError("Unsupported image input format")

    def _detect_objects_with_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects using text prompts"""
        image_input = params.get("image")
        text_prompts = params.get("text_prompts", [])
        confidence_threshold = params.get("confidence_threshold", 0.35)
        max_detections = params.get("max_detections", 10)

        if not image_input:
            return {"error": "image parameter required"}
        if not text_prompts:
            return {"error": "text_prompts parameter required"}

        # Ensure text_prompts is a list
        if isinstance(text_prompts, str):
            text_prompts = [text_prompts]

        image = self._load_image(image_input)

        # Prepare inputs
        inputs = self.processor(images=image, text=text_prompts, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        import torch

        # Forward pass
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Post-process results
        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=confidence_threshold,
            text_threshold=confidence_threshold,
            target_sizes=[image.size[::-1]]  # (height, width)
        )

        # Extract detections
        detections = []
        for result in results:
            for score, label, box in zip(result["scores"], result["labels"], result["boxes"]):
                if len(detections) >= max_detections:
                    break

                # Convert box to [x1, y1, x2, y2] format
                box = box.tolist()

                detections.append({
                    "label": label,
                    "confidence": float(score),
                    "bbox": box,  # [x1, y1, x2, y2]
                    "bbox_normalized": [
                        box[0] / image.width,
                        box[1] / image.height,
                        box[2] / image.width,
                        box[3] / image.height
                    ]
                })

        # Sort by confidence
        detections.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "detections": detections,
            "detection_count": len(detections),
            "text_prompts": text_prompts,
            "confidence_threshold": confidence_threshold,
            "image_size": [image.width, image.height]
        }

    def _grounding_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Grounding detection with detailed output"""
        result = self._detect_objects_with_text(params)

        if "error" in result:
            return result

        # Add additional grounding-specific information
        grounding_info = {
            "model": "groundingdino",
            "detection_method": "open_vocabulary",
            "grounding_type": "text_to_bbox"
        }

        result.update(grounding_info)
        return result

    def _batch_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects in batch mode with multiple prompts"""
        image_input = params.get("image")
        prompt_sets = params.get("prompt_sets", [])  # List of text prompt lists
        confidence_threshold = params.get("confidence_threshold", 0.35)

        if not image_input:
            return {"error": "image parameter required"}
        if not prompt_sets:
            return {"error": "prompt_sets parameter required"}

        image = self._load_image(image_input)
        all_results = []

        # Process each prompt set
        for i, prompts in enumerate(prompt_sets):
            batch_params = {
                "image": image,
                "text_prompts": prompts,
                "confidence_threshold": confidence_threshold
            }

            result = self._detect_objects_with_text(batch_params)
            if "error" not in result:
                result["prompt_set_index"] = i
                result["prompts"] = prompts
                all_results.append(result)

        return {
            "batch_results": all_results,
            "total_prompt_sets": len(prompt_sets),
            "successful_detections": len(all_results),
            "image_size": [image.width, image.height]
        }

    def _phrase_grounding(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ground specific phrases in image"""
        image_input = params.get("image")
        phrases = params.get("phrases", [])
        confidence_threshold = params.get("confidence_threshold", 0.35)

        if not image_input:
            return {"error": "image parameter required"}
        if not phrases:
            return {"error": "phrases parameter required"}

        # Use the main detection method
        detection_params = {
            "image": image_input,
            "text_prompts": phrases,
            "confidence_threshold": confidence_threshold
        }

        result = self._detect_objects_with_text(detection_params)

        if "error" in result:
            return result

        # Group detections by phrase
        phrase_detections = {}
        for detection in result["detections"]:
            label = detection["label"]
            if label not in phrase_detections:
                phrase_detections[label] = []
            phrase_detections[label].append(detection)

        return {
            "phrase_detections": phrase_detections,
            "phrases": phrases,
            "total_detections": len(result["detections"]),
            "image_size": result["image_size"],
            "confidence_threshold": confidence_threshold
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
PLUGIN_CLASS = GroundingDINOPlugin
PLUGIN_NAME = "groundingdino"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with GroundingDINO for open-vocabulary object detection"
PLUGIN_ACTIONS = [
    "detect_objects_with_text", "grounding_detection", "batch_detection", "phrase_grounding"
]