"""
Amazon Bedrock Plugin - Production Grade
Full integration with Claude, Titan, Llama, and other models on AWS Bedrock
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Amazon Bedrock Plugin

    Supports:
    - Anthropic Claude (Claude 3, Claude 2)
    - Amazon Titan (Text, Embeddings)
    - Meta Llama 2
    - AI21 Jurassic-2
    - Cohere Command
    - Stability AI Stable Diffusion
    - Text generation
    - Embeddings
    - Image generation
    """

    def __init__(self):
        self.name = "Amazon Bedrock"
        self.version = "2.0.0"
        self.description = "Production Amazon Bedrock integration with Claude, Titan, Llama"

        # Configuration
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")

        # Initialize client if available
        self.client = None
        if BOTO3_AVAILABLE and self.aws_access_key:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )

        # Model IDs
        self.models = {
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "claude-2.1": "anthropic.claude-v2:1",
            "claude-2": "anthropic.claude-v2",
            "titan-text-express": "amazon.titan-text-express-v1",
            "titan-text-lite": "amazon.titan-text-lite-v1",
            "titan-embed-text": "amazon.titan-embed-text-v1",
            "titan-embed-image": "amazon.titan-embed-image-v1",
            "llama2-13b": "meta.llama2-13b-chat-v1",
            "llama2-70b": "meta.llama2-70b-chat-v1",
            "j2-ultra": "ai21.j2-ultra-v1",
            "j2-mid": "ai21.j2-mid-v1",
            "command": "cohere.command-text-v14",
            "stable-diffusion": "stability.stable-diffusion-xl-v1"
        }

        # Usage tracking
        self.total_requests = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Amazon Bedrock request

        Args:
            action (str): Action to perform
                - "chat": Chat completion (Claude, Llama, etc.)
                - "complete": Text completion
                - "embed": Generate embeddings
                - "image": Generate image
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not BOTO3_AVAILABLE:
            return {
                "status": "error",
                "message": "boto3 not installed. Install with: pip install boto3"
            }

        if not self.client:
            return {
                "status": "error",
                "message": "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
            }

        try:
            action = kwargs.get("action", "chat")

            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "complete":
                return await self._complete(**kwargs)
            elif action == "embed":
                return await self._embed(**kwargs)
            elif action == "image":
                return await self._generate_image(**kwargs)
            elif action == "models":
                return self._list_models()
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Amazon Bedrock plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """Chat completion with Bedrock models"""
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "claude-3-sonnet")
        max_tokens = kwargs.get("max_tokens", 2048)
        temperature = kwargs.get("temperature", 1.0)
        top_p = kwargs.get("top_p", 0.999)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        model_id = self.models.get(model, self.models["claude-3-sonnet"])

        try:
            # Prepare request based on model type
            if "claude" in model_id:
                # Anthropic Claude format
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": top_p
                }
            elif "llama" in model_id:
                # Meta Llama format
                prompt = self._messages_to_llama_prompt(messages)
                body = {
                    "prompt": prompt,
                    "max_gen_len": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p
                }
            elif "titan" in model_id:
                # Amazon Titan format
                prompt = messages[-1]["content"] if messages else ""
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": top_p
                    }
                }
            else:
                return {"status": "error", "message": f"Unsupported model: {model}"}

            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )

            self.total_requests += 1

            # Parse response
            response_body = json.loads(response["body"].read())

            if "claude" in model_id:
                text = response_body.get("content", [{}])[0].get("text", "")
                usage = response_body.get("usage", {})
            elif "llama" in model_id:
                text = response_body.get("generation", "")
                usage = {}
            elif "titan" in model_id:
                text = response_body.get("results", [{}])[0].get("outputText", "")
                usage = {}
            else:
                text = str(response_body)
                usage = {}

            return {
                "status": "success",
                "response": text,
                "model": model_id,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise

    async def _complete(self, **kwargs) -> Dict[str, Any]:
        """Text completion"""
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "titan-text-express")
        max_tokens = kwargs.get("max_tokens", 512)
        temperature = kwargs.get("temperature", 0.7)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        model_id = self.models.get(model, self.models["titan-text-express"])

        try:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature
                }
            }

            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )

            self.total_requests += 1

            response_body = json.loads(response["body"].read())
            text = response_body.get("results", [{}])[0].get("outputText", "")

            return {
                "status": "success",
                "completion": text,
                "model": model_id
            }

        except Exception as e:
            logger.error(f"Completion error: {str(e)}")
            raise

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """Generate embeddings"""
        texts = kwargs.get("texts", [])
        model = kwargs.get("model", "titan-embed-text")

        if not texts:
            return {"status": "error", "message": "No texts provided"}

        if isinstance(texts, str):
            texts = [texts]

        model_id = self.models.get(model, self.models["titan-embed-text"])

        try:
            embeddings = []
            for text in texts:
                body = {"inputText": text}

                response = self.client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body)
                )

                response_body = json.loads(response["body"].read())
                embedding = response_body.get("embedding", [])
                embeddings.append(embedding)

            self.total_requests += len(texts)

            return {
                "status": "success",
                "embeddings": embeddings,
                "model": model_id,
                "dimensions": len(embeddings[0]) if embeddings else 0
            }

        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            raise

    async def _generate_image(self, **kwargs) -> Dict[str, Any]:
        """Generate image with Stable Diffusion"""
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt", "")
        model = kwargs.get("model", "stable-diffusion")
        width = kwargs.get("width", 512)
        height = kwargs.get("height", 512)
        cfg_scale = kwargs.get("cfg_scale", 7.0)
        steps = kwargs.get("steps", 50)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        model_id = self.models.get(model, self.models["stable-diffusion"])

        try:
            body = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": cfg_scale,
                "steps": steps,
                "width": width,
                "height": height
            }

            if negative_prompt:
                body["text_prompts"].append({"text": negative_prompt, "weight": -1.0})

            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )

            self.total_requests += 1

            response_body = json.loads(response["body"].read())
            artifacts = response_body.get("artifacts", [])

            images = []
            for artifact in artifacts:
                if artifact.get("base64"):
                    images.append(artifact["base64"])

            return {
                "status": "success",
                "images": images,
                "model": model_id
            }

        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            raise

    def _messages_to_llama_prompt(self, messages: List[Dict]) -> str:
        """Convert messages to Llama prompt format"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"[INST] {content} [/INST]")
            elif role == "assistant":
                prompt_parts.append(content)
        return " ".join(prompt_parts)

    def _list_models(self) -> Dict[str, Any]:
        """List available Bedrock models"""
        models = [
            {
                "id": "claude-3-opus",
                "name": "Claude 3 Opus",
                "description": "Most capable Claude model",
                "provider": "Anthropic"
            },
            {
                "id": "claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "description": "Balanced Claude model",
                "provider": "Anthropic"
            },
            {
                "id": "claude-3-haiku",
                "name": "Claude 3 Haiku",
                "description": "Fast Claude model",
                "provider": "Anthropic"
            },
            {
                "id": "titan-text-express",
                "name": "Titan Text Express",
                "description": "Amazon's text generation model",
                "provider": "Amazon"
            },
            {
                "id": "titan-embed-text",
                "name": "Titan Embeddings",
                "description": "Amazon's embedding model",
                "provider": "Amazon"
            },
            {
                "id": "llama2-70b",
                "name": "Llama 2 70B",
                "description": "Meta's large language model",
                "provider": "Meta"
            },
            {
                "id": "j2-ultra",
                "name": "Jurassic-2 Ultra",
                "description": "AI21's most capable model",
                "provider": "AI21 Labs"
            },
            {
                "id": "stable-diffusion",
                "name": "Stable Diffusion XL",
                "description": "Image generation",
                "provider": "Stability AI"
            }
        ]

        return {
            "status": "success",
            "models": models,
            "count": len(models)
        }

    def _get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "status": "success",
            "stats": {
                "total_requests": self.total_requests,
                "total_cost_usd": round(self.total_cost, 4),
                "timestamp": datetime.now().isoformat()
            }
        }
