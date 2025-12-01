"""
Stability AI Plugin - Production Grade
Full integration with Stability AI API - SDXL, SD3, and more
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime
import base64
import io

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Stability AI Plugin

    Supports:
    - Stable Diffusion XL (SDXL)
    - Stable Diffusion 3 (SD3)
    - Stable Image Core
    - Image-to-image transformation
    - Image upscaling
    - Inpainting & outpainting
    - Multiple aspect ratios
    - Style presets
    """

    def __init__(self):
        self.name = "Stability AI"
        self.version = "2.0.0"
        self.description = "Production Stability AI integration with SDXL, SD3"

        # Configuration
        self.api_key = os.getenv("STABILITY_API_KEY", "")
        self.base_url = "https://api.stability.ai/v2beta"
        self.timeout = 120

        # Model configurations
        self.models = {
            "sd3": "sd3",
            "sd3-turbo": "sd3-turbo",
            "sdxl": "stable-diffusion-xl-1024-v1-0",
            "core": "stable-image-core",
            "ultra": "stable-image-ultra"
        }

        # Style presets
        self.style_presets = [
            "3d-model", "analog-film", "anime", "cinematic", "comic-book",
            "digital-art", "enhance", "fantasy-art", "isometric", "line-art",
            "low-poly", "modeling-compound", "neon-punk", "origami", "photographic",
            "pixel-art", "tile-texture"
        ]

        # Usage tracking
        self.total_generations = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Stability AI request

        Args:
            action (str): Action to perform
                - "text_to_image": Generate image from text
                - "image_to_image": Transform image
                - "upscale": Upscale image
                - "inpaint": Inpaint image
                - "outpaint": Outpaint image
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not HTTPX_AVAILABLE:
            return {
                "status": "error",
                "message": "httpx not installed. Install with: pip install httpx"
            }

        if not self.api_key:
            return {
                "status": "error",
                "message": "Stability AI API key not configured. Set STABILITY_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "text_to_image")

            # Route to appropriate handler
            if action == "text_to_image":
                return await self._text_to_image(**kwargs)
            elif action == "image_to_image":
                return await self._image_to_image(**kwargs)
            elif action == "upscale":
                return await self._upscale(**kwargs)
            elif action == "inpaint":
                return await self._inpaint(**kwargs)
            elif action == "outpaint":
                return await self._outpaint(**kwargs)
            elif action == "models":
                return self._list_models()
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Stability AI plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _text_to_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image from text

        Args:
            prompt (str): Text description
            model (str): Model to use (sd3, sdxl, core, ultra)
            negative_prompt (str): What to avoid
            aspect_ratio (str): Aspect ratio (1:1, 16:9, etc.)
            style_preset (str): Style preset
            seed (int): Random seed
            output_format (str): png or webp
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "core")
        negative_prompt = kwargs.get("negative_prompt", "")
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")
        style_preset = kwargs.get("style_preset", None)
        seed = kwargs.get("seed", 0)
        output_format = kwargs.get("output_format", "png")

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        # Get model ID
        model_id = self.models.get(model, self.models["core"])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare form data
                form_data = {
                    "prompt": prompt,
                    "output_format": output_format,
                    "aspect_ratio": aspect_ratio
                }

                if negative_prompt:
                    form_data["negative_prompt"] = negative_prompt
                if style_preset and style_preset in self.style_presets:
                    form_data["style_preset"] = style_preset
                if seed:
                    form_data["seed"] = seed

                response = await client.post(
                    f"{self.base_url}/stable-image/generate/{model_id}",
                    headers={
                        "authorization": f"Bearer {self.api_key}",
                        "accept": "image/*"
                    },
                    files={"none": ''},  # Required by API
                    data=form_data
                )

                if response.status_code == 200:
                    self.total_generations += 1

                    # Convert image to base64
                    image_data = response.content
                    img_base64 = base64.b64encode(image_data).decode()

                    return {
                        "status": "success",
                        "image_base64": img_base64,
                        "format": output_format,
                        "model": model,
                        "prompt": prompt
                    }
                else:
                    error_msg = response.text
                    return {
                        "status": "error",
                        "message": f"API error: {error_msg}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Text-to-image error: {str(e)}")
            raise

    async def _image_to_image(self, **kwargs) -> Dict[str, Any]:
        """
        Transform image

        Args:
            image (str): Base64 encoded image or file path
            prompt (str): Transformation description
            model (str): Model to use
            strength (float): Transformation strength (0-1)
            negative_prompt (str): What to avoid
        """
        image = kwargs.get("image", "")
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "sdxl")
        strength = kwargs.get("strength", 0.35)
        negative_prompt = kwargs.get("negative_prompt", "")

        if not image or not prompt:
            return {"status": "error", "message": "Image and prompt required"}

        model_id = self.models.get(model, self.models["sdxl"])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare image data
                if image.startswith("data:image"):
                    # Extract base64 from data URL
                    image_data = base64.b64decode(image.split(",")[1])
                elif os.path.exists(image):
                    with open(image, "rb") as f:
                        image_data = f.read()
                else:
                    image_data = base64.b64decode(image)

                # Prepare form data
                files = {
                    "image": ("image.png", image_data, "image/png")
                }
                data = {
                    "prompt": prompt,
                    "strength": strength,
                    "output_format": "png"
                }

                if negative_prompt:
                    data["negative_prompt"] = negative_prompt

                response = await client.post(
                    f"{self.base_url}/stable-image/generate/image-to-image",
                    headers={
                        "authorization": f"Bearer {self.api_key}",
                        "accept": "image/*"
                    },
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    self.total_generations += 1

                    output_data = response.content
                    img_base64 = base64.b64encode(output_data).decode()

                    return {
                        "status": "success",
                        "image_base64": img_base64,
                        "model": model
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Image-to-image error: {str(e)}")
            raise

    async def _upscale(self, **kwargs) -> Dict[str, Any]:
        """
        Upscale image using Stability AI

        Args:
            image (str): Base64 encoded image or file path
            prompt (str): Optional upscaling prompt
        """
        image = kwargs.get("image", "")
        prompt = kwargs.get("prompt", "")

        if not image:
            return {"status": "error", "message": "No image provided"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare image data
                if image.startswith("data:image"):
                    image_data = base64.b64decode(image.split(",")[1])
                elif os.path.exists(image):
                    with open(image, "rb") as f:
                        image_data = f.read()
                else:
                    image_data = base64.b64decode(image)

                files = {
                    "image": ("image.png", image_data, "image/png")
                }
                data = {
                    "output_format": "png"
                }

                if prompt:
                    data["prompt"] = prompt

                response = await client.post(
                    f"{self.base_url}/stable-image/upscale/conservative",
                    headers={
                        "authorization": f"Bearer {self.api_key}",
                        "accept": "image/*"
                    },
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    self.total_generations += 1

                    output_data = response.content
                    img_base64 = base64.b64encode(output_data).decode()

                    return {
                        "status": "success",
                        "image_base64": img_base64
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Upscaling error: {str(e)}")
            raise

    async def _inpaint(self, **kwargs) -> Dict[str, Any]:
        """
        Inpaint image

        Args:
            image (str): Base64 encoded image or file path
            mask (str): Base64 encoded mask or file path
            prompt (str): Inpainting description
        """
        image = kwargs.get("image", "")
        mask = kwargs.get("mask", "")
        prompt = kwargs.get("prompt", "")

        if not image or not mask or not prompt:
            return {"status": "error", "message": "Image, mask, and prompt required"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare image and mask data
                image_data = self._prepare_image_data(image)
                mask_data = self._prepare_image_data(mask)

                files = {
                    "image": ("image.png", image_data, "image/png"),
                    "mask": ("mask.png", mask_data, "image/png")
                }
                data = {
                    "prompt": prompt,
                    "output_format": "png"
                }

                response = await client.post(
                    f"{self.base_url}/stable-image/edit/inpaint",
                    headers={
                        "authorization": f"Bearer {self.api_key}",
                        "accept": "image/*"
                    },
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    self.total_generations += 1

                    output_data = response.content
                    img_base64 = base64.b64encode(output_data).decode()

                    return {
                        "status": "success",
                        "image_base64": img_base64
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Inpainting error: {str(e)}")
            raise

    async def _outpaint(self, **kwargs) -> Dict[str, Any]:
        """
        Outpaint image (extend beyond borders)

        Args:
            image (str): Base64 encoded image or file path
            prompt (str): Outpainting description
            left (int): Pixels to extend left
            right (int): Pixels to extend right
            up (int): Pixels to extend up
            down (int): Pixels to extend down
        """
        image = kwargs.get("image", "")
        prompt = kwargs.get("prompt", "")
        left = kwargs.get("left", 0)
        right = kwargs.get("right", 0)
        up = kwargs.get("up", 0)
        down = kwargs.get("down", 0)

        if not image or not prompt:
            return {"status": "error", "message": "Image and prompt required"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                image_data = self._prepare_image_data(image)

                files = {
                    "image": ("image.png", image_data, "image/png")
                }
                data = {
                    "prompt": prompt,
                    "left": left,
                    "right": right,
                    "up": up,
                    "down": down,
                    "output_format": "png"
                }

                response = await client.post(
                    f"{self.base_url}/stable-image/edit/outpaint",
                    headers={
                        "authorization": f"Bearer {self.api_key}",
                        "accept": "image/*"
                    },
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    self.total_generations += 1

                    output_data = response.content
                    img_base64 = base64.b64encode(output_data).decode()

                    return {
                        "status": "success",
                        "image_base64": img_base64
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Outpainting error: {str(e)}")
            raise

    def _prepare_image_data(self, image: str) -> bytes:
        """Prepare image data from various input formats"""
        if image.startswith("data:image"):
            return base64.b64decode(image.split(",")[1])
        elif os.path.exists(image):
            with open(image, "rb") as f:
                return f.read()
        else:
            return base64.b64decode(image)

    def _list_models(self) -> Dict[str, Any]:
        """List available Stability AI models"""
        models = [
            {
                "id": "sd3",
                "name": "Stable Diffusion 3",
                "description": "Latest SD3 model with improved quality",
                "type": "text_to_image"
            },
            {
                "id": "sd3-turbo",
                "name": "SD3 Turbo",
                "description": "Fast SD3 variant for quick generation",
                "type": "text_to_image"
            },
            {
                "id": "sdxl",
                "name": "Stable Diffusion XL",
                "description": "High-quality 1024x1024 generation",
                "type": "text_to_image"
            },
            {
                "id": "core",
                "name": "Stable Image Core",
                "description": "Balanced quality and speed",
                "type": "text_to_image"
            },
            {
                "id": "ultra",
                "name": "Stable Image Ultra",
                "description": "Highest quality output",
                "type": "text_to_image"
            }
        ]

        return {
            "status": "success",
            "models": models,
            "style_presets": self.style_presets,
            "count": len(models)
        }

    def _get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "status": "success",
            "stats": {
                "total_generations": self.total_generations,
                "total_cost_usd": round(self.total_cost, 4),
                "timestamp": datetime.now().isoformat()
            }
        }
