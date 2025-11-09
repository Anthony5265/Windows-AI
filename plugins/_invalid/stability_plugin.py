"""
Stability AI Model Provider Plugin
Supports Stable Diffusion XL, StableCode, and other Stability AI models
"""

from typing import Dict, Any, Optional, List
import os


class StabilityPlugin:
    """Plugin for Stability AI models"""
    
    name = "stability"
    version = "1.0.0"
    description = "Integration with Stability AI (SDXL, StableCode, etc.)"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.stability.ai/v1"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Stability AI plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("STABILITY_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing Stability AI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Stability AI action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "text_to_image":
                return self._text_to_image(params)
            elif action == "image_to_image":
                return self._image_to_image(params)
            elif action == "upscale":
                return self._upscale(params)
            elif action == "inpaint":
                return self._inpaint(params)
            elif action == "outpaint":
                return self._outpaint(params)
            elif action == "list_engines":
                return self._list_engines()
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _text_to_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image from text"""
        import requests
        import base64
        
        text_prompts = params.get("text_prompts", [])
        if isinstance(text_prompts, str):
            text_prompts = [{"text": text_prompts, "weight": 1.0}]
        
        engine_id = params.get("engine_id", "stable-diffusion-xl-1024-v1-0")
        # Available engines:
        # - stable-diffusion-xl-1024-v1-0
        # - stable-diffusion-v1-6
        # - stable-diffusion-512-v2-1
        # - stable-diffusion-xl-beta-v2-2-2
        
        height = params.get("height", 1024)
        width = params.get("width", 1024)
        cfg_scale = params.get("cfg_scale", 7.0)
        steps = params.get("steps", 30)
        samples = params.get("samples", 1)
        style_preset = params.get("style_preset")  # photographic, digital-art, etc.
        
        payload = {
            "text_prompts": text_prompts,
            "cfg_scale": cfg_scale,
            "height": height,
            "width": width,
            "steps": steps,
            "samples": samples
        }
        
        if style_preset:
            payload["style_preset"] = style_preset
        
        response = requests.post(
            f"{self.base_url}/generation/{engine_id}/text-to-image",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        
        # Decode base64 images
        images = []
        for artifact in data.get("artifacts", []):
            if artifact["finishReason"] == "SUCCESS":
                images.append({
                    "base64": artifact["base64"],
                    "seed": artifact["seed"]
                })
        
        return {
            "images": images,
            "engine": engine_id,
            "count": len(images)
        }
    
    def _image_to_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform image with text guidance"""
        import requests
        
        init_image_path = params.get("init_image")
        text_prompts = params.get("text_prompts", [])
        engine_id = params.get("engine_id", "stable-diffusion-xl-1024-v1-0")
        
        if not init_image_path:
            return {"error": "init_image path required"}
        
        if isinstance(text_prompts, str):
            text_prompts = [{"text": text_prompts, "weight": 1.0}]
        
        cfg_scale = params.get("cfg_scale", 7.0)
        steps = params.get("steps", 30)
        image_strength = params.get("image_strength", 0.35)
        
        with open(init_image_path, 'rb') as f:
            files = {"init_image": f}
            data = {
                "text_prompts[0][text]": text_prompts[0]["text"],
                "text_prompts[0][weight]": text_prompts[0]["weight"],
                "cfg_scale": cfg_scale,
                "steps": steps,
                "image_strength": image_strength
            }
            
            response = requests.post(
                f"{self.base_url}/generation/{engine_id}/image-to-image",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files,
                data=data,
                timeout=120
            )
        
        response.raise_for_status()
        result = response.json()
        
        images = []
        for artifact in result.get("artifacts", []):
            if artifact["finishReason"] == "SUCCESS":
                images.append({
                    "base64": artifact["base64"],
                    "seed": artifact["seed"]
                })
        
        return {
            "images": images,
            "engine": engine_id,
            "count": len(images)
        }
    
    def _upscale(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upscale image"""
        import requests
        
        image_path = params.get("image")
        engine_id = "esrgan-v1-x2plus"  # upscaling engine
        
        if not image_path:
            return {"error": "image path required"}
        
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/generation/{engine_id}/image-to-image/upscale",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"image": f},
                timeout=120
            )
        
        response.raise_for_status()
        result = response.json()
        
        images = []
        for artifact in result.get("artifacts", []):
            images.append({"base64": artifact["base64"]})
        
        return {
            "images": images,
            "engine": engine_id
        }
    
    def _inpaint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inpaint image with mask"""
        # Similar to image_to_image but with mask
        return {"error": "Inpainting not yet implemented"}
    
    def _outpaint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Outpaint image to extend beyond boundaries"""
        # Similar to image_to_image with outpainting params
        return {"error": "Outpainting not yet implemented"}
    
    def _list_engines(self) -> Dict[str, Any]:
        """List available engines"""
        import requests
        
        response = requests.get(
            f"{self.base_url}/engines/list",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "engines": [
                {
                    "id": engine["id"],
                    "name": engine["name"],
                    "description": engine["description"],
                    "type": engine["type"]
                }
                for engine in data
            ],
            "count": len(data)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = StabilityPlugin
PLUGIN_NAME = "stability"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Stability AI (Stable Diffusion XL, etc.)"
PLUGIN_ACTIONS = ["text_to_image", "image_to_image", "upscale", "inpaint", "outpaint", "list_engines"]
