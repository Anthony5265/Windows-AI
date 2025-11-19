"""
GroundingDINO Plugin
Open-set object detection with text prompts
"""

from typing import Dict, Any, Optional, List
import os


class GroundingDINOPlugin:
    """Plugin for GroundingDINO"""

    name = "groundingdino"
    version = "1.0.0"
    description = "Integration with GroundingDINO for open-set object detection"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.processor = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GroundingDINO plugin"""
        try:
            from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

            model_name = "IDEA-Research/grounding-dino-tiny"

            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = AutoModelForZeroShotObjectDetection.from_pretrained(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("transformers package not installed. Install with: pip install transformers")
            return False
        except Exception as e:
            print(f"Error initializing GroundingDINO plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GroundingDINO action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "detect":
                return self._detect(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _detect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect objects based on text prompt"""
        from PIL import Image

        image_path = params.get("image_path", "")
        text_prompt = params.get("text_prompt", "")
        threshold = params.get("threshold", 0.3)

        image = Image.open(image_path)
        inputs = self.processor(images=image, text=text_prompt, return_tensors="pt")
        outputs = self.model(**inputs)

        # Post-process results
        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=threshold,
            text_threshold=threshold,
            target_sizes=[image.size[::-1]]
        )

        # Extract boxes, scores, and labels
        detections = []
        for score, label, box in zip(results[0]["scores"], results[0]["labels"], results[0]["boxes"]):
            detections.append({
                "score": float(score),
                "label": label,
                "box": box.tolist()
            })

        return {
            "success": True,
            "detections": detections
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.processor = None
        return True
