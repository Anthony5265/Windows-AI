"""
CLIP Plugin
OpenAI's vision-language embedding model
"""

from typing import Dict, Any, Optional, List
import os


class CLIPPlugin:
    """Plugin for OpenAI CLIP"""

    name = "clip_openai"
    version = "1.0.0"
    description = "Integration with CLIP for vision-language embeddings"
    author = "Windows AI Team"

    def __init__(self):
        self.model = None
        self.processor = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CLIP plugin"""
        try:
            from transformers import CLIPProcessor, CLIPModel

            model_name = config.get("model", "openai/clip-vit-large-patch14") if config else "openai/clip-vit-large-patch14"

            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model = CLIPModel.from_pretrained(model_name)
            self._initialized = True
            return True

        except ImportError:
            print("transformers package not installed. Install with: pip install transformers")
            return False
        except Exception as e:
            print(f"Error initializing CLIP plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CLIP action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "encode_image":
                return self._encode_image(params)
            elif action == "encode_text":
                return self._encode_text(params)
            elif action == "similarity":
                return self._compute_similarity(params)
            elif action == "classify":
                return self._zero_shot_classify(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _encode_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Encode image to embedding"""
        from PIL import Image

        image_path = params.get("image_path", "")
        image = Image.open(image_path)

        inputs = self.processor(images=image, return_tensors="pt")
        image_features = self.model.get_image_features(**inputs)

        return {
            "success": True,
            "embedding": image_features[0].detach().tolist()
        }

    def _encode_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Encode text to embedding"""
        text = params.get("text", "")

        inputs = self.processor(text=[text], return_tensors="pt", padding=True)
        text_features = self.model.get_text_features(**inputs)

        return {
            "success": True,
            "embedding": text_features[0].detach().tolist()
        }

    def _compute_similarity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute image-text similarity"""
        from PIL import Image
        import torch

        image_path = params.get("image_path", "")
        texts = params.get("texts", [])

        image = Image.open(image_path)
        inputs = self.processor(text=texts, images=image, return_tensors="pt", padding=True)
        outputs = self.model(**inputs)

        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)

        results = []
        for i, text in enumerate(texts):
            results.append({
                "text": text,
                "similarity": float(probs[0][i])
            })

        return {
            "success": True,
            "similarities": results
        }

    def _zero_shot_classify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Zero-shot image classification"""
        from PIL import Image

        image_path = params.get("image_path", "")
        labels = params.get("labels", [])

        # Format labels as "a photo of a {label}"
        text_inputs = [f"a photo of a {label}" for label in labels]

        image = Image.open(image_path)
        inputs = self.processor(text=text_inputs, images=image, return_tensors="pt", padding=True)
        outputs = self.model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0]

        results = []
        for i, label in enumerate(labels):
            results.append({
                "label": label,
                "probability": float(probs[i])
            })

        # Sort by probability
        results = sorted(results, key=lambda x: x["probability"], reverse=True)

        return {
            "success": True,
            "classifications": results
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.processor = None
        return True
