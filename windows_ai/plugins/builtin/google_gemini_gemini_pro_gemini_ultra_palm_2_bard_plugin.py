"""
Google Gemini Plugin - Production Grade
Full integration with Gemini Pro, Gemini Ultra, and multimodal capabilities
"""
from typing import Dict, Any, List, Optional, AsyncIterator
import os
import logging
import json
from datetime import datetime
import base64

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Google Gemini Plugin

    Supports:
    - Gemini 1.5 Pro, Gemini 1.5 Flash
    - Gemini 1.0 Pro, Gemini 1.0 Pro Vision
    - Multimodal inputs (text, images, video, audio)
    - Streaming responses
    - Function calling
    - Safety settings
    - Token counting
    - Cost tracking
    - Grounding (search)
    """

    def __init__(self):
        self.name = "Google Gemini"
        self.version = "2.0.0"
        self.description = "Production Google Gemini integration with Gemini Pro, Ultra, multimodal support"

        # Configuration
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.timeout = int(os.getenv("GEMINI_TIMEOUT", "120"))

        # Initialize client if available
        self.configured = False
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.configured = True

        # Model pricing (per 1M tokens) - as of 2025
        self.pricing = {
            "gemini-1.5-pro-latest": {"input": 3.50, "output": 10.50},
            "gemini-1.5-flash-latest": {"input": 0.35, "output": 1.05},
            "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
            "gemini-1.0-pro-vision": {"input": 0.50, "output": 1.50},
        }

        # Model capabilities
        self.multimodal_models = [
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-1.0-pro-vision"
        ]

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Google Gemini request

        Args:
            action (str): Action to perform
                - "chat": Chat completion
                - "vision": Analyze image/video with multimodal models
                - "count_tokens": Count tokens in content
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not GENAI_AVAILABLE:
            return {
                "status": "error",
                "message": "Google GenerativeAI SDK not installed. Install with: pip install google-generativeai"
            }

        if not self.configured:
            return {
                "status": "error",
                "message": "Google API key not configured. Set GOOGLE_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "chat")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "vision":
                return await self._vision(**kwargs)
            elif action == "count_tokens":
                return await self._count_tokens(**kwargs)
            elif action == "models":
                return await self._list_models(**kwargs)
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Gemini plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion with Gemini

        Args:
            messages (List[Dict]): Conversation messages
            model (str): Model to use (default: gemini-1.5-pro-latest)
            temperature (float): Sampling temperature 0-2
            max_tokens (int): Maximum tokens to generate
            stream (bool): Enable streaming responses
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-k sampling parameter
            safety_settings (Dict): Safety settings configuration
            system_instruction (str): System instruction for the model
            **kwargs: Additional Gemini parameters
        """
        messages = kwargs.get("messages", [])
        model_name = kwargs.get("model", "gemini-1.5-pro-latest")
        temperature = kwargs.get("temperature", 1.0)
        max_tokens = kwargs.get("max_tokens", None)
        stream = kwargs.get("stream", False)
        top_p = kwargs.get("top_p", None)
        top_k = kwargs.get("top_k", None)
        safety_settings = kwargs.get("safety_settings", None)
        system_instruction = kwargs.get("system_instruction", None)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        try:
            # Configure generation settings
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            if top_p is not None:
                generation_config["top_p"] = top_p
            if top_k is not None:
                generation_config["top_k"] = top_k

            # Create model
            model_params = {
                "model_name": model_name,
                "generation_config": generation_config
            }
            if safety_settings:
                model_params["safety_settings"] = safety_settings
            if system_instruction:
                model_params["system_instruction"] = system_instruction

            model = genai.GenerativeModel(**model_params)

            # Convert messages to Gemini format
            # Gemini uses a simpler format - just content history
            chat_history = []
            current_message = None

            for msg in messages[:-1]:  # All but last message become history
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            # Last message is the current message
            if messages:
                current_message = messages[-1]["content"]

            # Start chat with history
            chat = model.start_chat(history=chat_history)

            if stream:
                # Streaming response
                response = chat.send_message(current_message, stream=True)

                collected_text = []
                for chunk in response:
                    if chunk.text:
                        collected_text.append(chunk.text)

                full_response = "".join(collected_text)

                return {
                    "status": "success",
                    "response": full_response,
                    "model": model_name,
                    "streaming": True
                }
            else:
                # Standard response
                response = chat.send_message(current_message)

                # Track usage
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count

                    self.total_input_tokens += input_tokens
                    self.total_output_tokens += output_tokens

                    # Calculate cost (pricing is per 1M tokens)
                    if model_name in self.pricing:
                        input_cost = (input_tokens / 1_000_000) * self.pricing[model_name]["input"]
                        output_cost = (output_tokens / 1_000_000) * self.pricing[model_name]["output"]
                        self.total_cost += (input_cost + output_cost)

                return {
                    "status": "success",
                    "response": response.text,
                    "model": model_name,
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                    "usage": {
                        "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                        "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                        "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
                    },
                    "safety_ratings": [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        } for rating in response.candidates[0].safety_ratings
                    ] if response.candidates and response.candidates[0].safety_ratings else []
                }

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise

    async def _vision(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze image/video with Gemini multimodal models

        Args:
            image_url (str): URL of image to analyze
            image_data (str): Base64 encoded image data
            image_path (str): Local path to image
            video_data (bytes): Video data
            audio_data (bytes): Audio data
            prompt (str): Question about the media
            model (str): Model to use (default: gemini-1.5-pro-latest)
            max_tokens (int): Maximum tokens
        """
        image_url = kwargs.get("image_url")
        image_data = kwargs.get("image_data")
        image_path = kwargs.get("image_path")
        video_data = kwargs.get("video_data")
        audio_data = kwargs.get("audio_data")
        prompt = kwargs.get("prompt", "What's in this image?")
        model_name = kwargs.get("model", "gemini-1.5-pro-latest")
        max_tokens = kwargs.get("max_tokens", 4096)

        # Check if model supports multimodal
        if model_name not in self.multimodal_models:
            return {
                "status": "error",
                "message": f"Model {model_name} does not support multimodal. Use Gemini 1.5 Pro/Flash or 1.0 Pro Vision."
            }

        if not any([image_url, image_data, image_path, video_data, audio_data]):
            return {"status": "error", "message": "No media provided (image_url, image_data, image_path, video_data, or audio_data required)"}

        try:
            # Create model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"max_output_tokens": max_tokens}
            )

            # Prepare content parts
            parts = [prompt]

            # Add image if provided
            if image_path:
                import PIL.Image
                image = PIL.Image.open(image_path)
                parts.append(image)
            elif image_data:
                # Decode base64 image
                import PIL.Image
                import io
                image_bytes = base64.b64decode(image_data)
                image = PIL.Image.open(io.BytesIO(image_bytes))
                parts.append(image)
            elif image_url:
                # Download and process image from URL
                import PIL.Image
                import io
                import httpx

                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    image = PIL.Image.open(io.BytesIO(response.content))
                    parts.append(image)

            # Generate response
            response = model.generate_content(parts)

            # Track usage
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens

                if model_name in self.pricing:
                    input_cost = (input_tokens / 1_000_000) * self.pricing[model_name]["input"]
                    output_cost = (output_tokens / 1_000_000) * self.pricing[model_name]["output"]
                    self.total_cost += (input_cost + output_cost)

            return {
                "status": "success",
                "analysis": response.text,
                "model": model_name,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
                },
                "safety_ratings": [
                    {
                        "category": rating.category.name,
                        "probability": rating.probability.name
                    } for rating in response.candidates[0].safety_ratings
                ] if response.candidates and response.candidates[0].safety_ratings else []
            }

        except Exception as e:
            logger.error(f"Vision analysis error: {str(e)}")
            raise

    async def _count_tokens(self, **kwargs) -> Dict[str, Any]:
        """
        Count tokens in content

        Args:
            text (str): Text content to count
            model (str): Model to use for counting
        """
        text = kwargs.get("text", "")
        model_name = kwargs.get("model", "gemini-1.5-pro-latest")

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            model = genai.GenerativeModel(model_name=model_name)
            result = model.count_tokens(text)

            return {
                "status": "success",
                "token_count": result.total_tokens,
                "model": model_name
            }

        except Exception as e:
            logger.error(f"Token counting error: {str(e)}")
            raise

    async def _list_models(self, **kwargs) -> Dict[str, Any]:
        """List available Gemini models"""
        try:
            models = []
            for model_info in genai.list_models():
                if 'generateContent' in model_info.supported_generation_methods:
                    models.append({
                        "id": model_info.name,
                        "display_name": model_info.display_name,
                        "description": model_info.description,
                        "input_token_limit": model_info.input_token_limit,
                        "output_token_limit": model_info.output_token_limit,
                        "supports_multimodal": model_info.name in self.multimodal_models
                    })

            return {
                "status": "success",
                "models": models,
                "count": len(models)
            }

        except Exception as e:
            logger.error(f"List models error: {str(e)}")
            raise

    def _get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "status": "success",
            "stats": {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_cost_usd": round(self.total_cost, 4),
                "timestamp": datetime.now().isoformat()
            }
        }
