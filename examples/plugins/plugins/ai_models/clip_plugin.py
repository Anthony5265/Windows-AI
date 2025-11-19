"""
CLIP Vision Model Plugin
Contrastive Language-Image Pre-training
"""

from typing import Dict, Any, Optional, List
import os


class CLIPPlugin:
    """Plugin for OpenAI CLIP"""
    
    name = "clip"
    version = "1.0.0"
    description = "Integration with OpenAI CLIP for vision-language tasks"
    author = "Windows AI Team"
    
    def __init__(self):
        self.model = None
        self.processor = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CLIP plugin"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            model_name = (
                config.get("model_name") if config 
                else "openai/clip-vit-large-patch14"
            )
            
            self.processor = CLIPProcessor.from_pretrained(model_name)
            self.model = CLIPModel.from_pretrained(model_name)
            
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            
            self._initialized = True
            return True
            
        except ImportError:
            print("transformers not installed. Install with: pip install transformers torch pillow")
            return False
        except Exception as e:
            print(f"Error initializing CLIP plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CLIP action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
            
        try:
            if action == "classify":
                return self._zero_shot_classification(params)
            elif action == "similarity":
                return self._image_text_similarity(params)
            elif action == "embeddings":
                return self._get_embeddings(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _zero_shot_classification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Zero-shot image classification"""
        from PIL import Image
        import torch
        
        image_path = params.get("image_path", "")
        labels = params.get("labels", [])
        
        if not os.path.exists(image_path):
            return {"success": False, "error": "Image not found"}
        
        image = Image.open(image_path)
        
        inputs = self.processor(
            text=labels,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        outputs = self.model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        
        results = [
            {"label": label, "score": float(prob)}
            for label, prob in zip(labels, probs[0])
        ]
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "success": True,
            "predictions": results
        }
    
    def _image_text_similarity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate image-text similarity"""
        from PIL import Image
        import torch
        
        image_path = params.get("image_path", "")
        text = params.get("text", "")
        
        if not os.path.exists(image_path):
            return {"success": False, "error": "Image not found"}
        
        image = Image.open(image_path)
        
        inputs = self.processor(
            text=[text],
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        outputs = self.model(**inputs)
        similarity = float(outputs.logits_per_image[0][0])
        
        return {
            "success": True,
            "similarity": similarity
        }
    
    def _get_embeddings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get image and text embeddings"""
        from PIL import Image
        import torch
        
        image_path = params.get("image_path")
        text = params.get("text")
        
        result = {}
        
        if image_path and os.path.exists(image_path):
            image = Image.open(image_path)
            inputs = self.processor(images=image, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            image_features = self.model.get_image_features(**inputs)
            result["image_embedding"] = image_features[0].cpu().detach().tolist()
        
        if text:
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            text_features = self.model.get_text_features(**inputs)
            result["text_embedding"] = text_features[0].cpu().detach().tolist()
        
        return {
            "success": True,
            **result
        }
    
    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.model = None
        self.processor = None
        return True
