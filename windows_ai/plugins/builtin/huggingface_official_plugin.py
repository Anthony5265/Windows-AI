"""
Hugging Face Plugin (Official SDK)
Production-grade integration with Hugging Face Inference API and Hub
"""
from typing import Dict, Any, List, Optional, Union
import os
import logging

logger = logging.getLogger(__name__)

try:
    from huggingface_hub import InferenceClient, HfApi, hf_hub_download
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    logger.warning("huggingface_hub not installed. Install with: pip install huggingface_hub")


class Plugin:
    """Plugin for Hugging Face using official SDK"""

    def __init__(self):
        self.name = "Hugging Face Official"
        self.version = "2.0.0"
        self.description = "Hugging Face integration with Inference API and Hub access"

        # Configuration
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", os.getenv("HF_TOKEN", ""))
        self.client: Optional[InferenceClient] = None
        self.api: Optional[HfApi] = None

        # Initialize clients if API key is available
        if HUGGINGFACE_AVAILABLE:
            try:
                self.client = InferenceClient(token=self.api_key if self.api_key else None)
                self.api = HfApi(token=self.api_key if self.api_key else None)
                logger.info("Hugging Face clients initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Hugging Face clients: {e}")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Hugging Face request

        Args:
            action (str): Action to perform (chat, text_generation, embedding, etc.)
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not HUGGINGFACE_AVAILABLE:
            return {
                "status": "error",
                "message": "Hugging Face SDK not installed. Install with: pip install huggingface_hub"
            }

        try:
            action = kwargs.get("action", "text_generation")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "text_generation":
                return await self._text_generation(**kwargs)
            elif action == "embedding":
                return await self._embedding(**kwargs)
            elif action == "image_to_text":
                return await self._image_to_text(**kwargs)
            elif action == "text_to_image":
                return await self._text_to_image(**kwargs)
            elif action == "speech_to_text":
                return await self._speech_to_text(**kwargs)
            elif action == "text_to_speech":
                return await self._text_to_speech(**kwargs)
            elif action == "translation":
                return await self._translation(**kwargs)
            elif action == "summarization":
                return await self._summarization(**kwargs)
            elif action == "question_answering":
                return await self._question_answering(**kwargs)
            elif action == "zero_shot_classification":
                return await self._zero_shot_classification(**kwargs)
            elif action == "download_model":
                return await self._download_model(**kwargs)
            elif action == "list_models":
                return await self._list_models(**kwargs)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Hugging Face error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion using Hugging Face models

        Supports conversational models
        """
        try:
            messages = kwargs.get("messages", [])
            model = kwargs.get("model", "meta-llama/Meta-Llama-3-8B-Instruct")
            max_tokens = kwargs.get("max_tokens", 500)
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.95)

            # If single message, convert to messages format
            if "prompt" in kwargs and not messages:
                messages = [{"role": "user", "content": kwargs["prompt"]}]

            response = self.client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )

            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "model": model,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Hugging Face chat error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _text_generation(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text using causal language models
        """
        try:
            prompt = kwargs.get("prompt", "")
            model = kwargs.get("model", "gpt2")
            max_new_tokens = kwargs.get("max_new_tokens", kwargs.get("max_tokens", 100))
            temperature = kwargs.get("temperature", 0.7)
            top_k = kwargs.get("top_k", 50)
            top_p = kwargs.get("top_p", 0.95)
            do_sample = kwargs.get("do_sample", True)

            response = self.client.text_generation(
                prompt=prompt,
                model=model,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                do_sample=do_sample,
                return_full_text=False
            )

            return {
                "status": "success",
                "generated_text": response,
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face text generation error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _embedding(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings for text
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))
            model = kwargs.get("model", "sentence-transformers/all-MiniLM-L6-v2")

            response = self.client.feature_extraction(
                text=text,
                model=model
            )

            return {
                "status": "success",
                "embedding": response,
                "model": model,
                "dimensions": len(response) if isinstance(response, list) else None
            }

        except Exception as e:
            logger.error(f"Hugging Face embedding error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _image_to_text(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text description from image
        """
        try:
            image = kwargs.get("image", "")  # URL or bytes
            model = kwargs.get("model", "Salesforce/blip-image-captioning-large")

            response = self.client.image_to_text(
                image=image,
                model=model
            )

            return {
                "status": "success",
                "generated_text": response,
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face image to text error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _text_to_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image from text prompt
        """
        try:
            prompt = kwargs.get("prompt", "")
            model = kwargs.get("model", "stabilityai/stable-diffusion-2-1")
            negative_prompt = kwargs.get("negative_prompt", None)
            height = kwargs.get("height", 512)
            width = kwargs.get("width", 512)
            num_inference_steps = kwargs.get("num_inference_steps", 50)
            guidance_scale = kwargs.get("guidance_scale", 7.5)

            image = self.client.text_to_image(
                prompt=prompt,
                model=model,
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale
            )

            return {
                "status": "success",
                "image": image,  # PIL Image object
                "model": model,
                "size": f"{width}x{height}"
            }

        except Exception as e:
            logger.error(f"Hugging Face text to image error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _speech_to_text(self, **kwargs) -> Dict[str, Any]:
        """
        Transcribe audio to text
        """
        try:
            audio = kwargs.get("audio", "")  # bytes or file path
            model = kwargs.get("model", "openai/whisper-large-v3")

            response = self.client.automatic_speech_recognition(
                audio=audio,
                model=model
            )

            return {
                "status": "success",
                "text": response.get("text", response),
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face speech to text error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _text_to_speech(self, **kwargs) -> Dict[str, Any]:
        """
        Generate speech from text
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))
            model = kwargs.get("model", "facebook/fastspeech2-en-ljspeech")

            response = self.client.text_to_speech(
                text=text,
                model=model
            )

            return {
                "status": "success",
                "audio": response,  # bytes
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face text to speech error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _translation(self, **kwargs) -> Dict[str, Any]:
        """
        Translate text between languages
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))
            model = kwargs.get("model", "Helsinki-NLP/opus-mt-en-de")

            response = self.client.translation(
                text=text,
                model=model
            )

            return {
                "status": "success",
                "translation_text": response.get("translation_text", response),
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face translation error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _summarization(self, **kwargs) -> Dict[str, Any]:
        """
        Summarize text
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))
            model = kwargs.get("model", "facebook/bart-large-cnn")
            max_length = kwargs.get("max_length", 130)
            min_length = kwargs.get("min_length", 30)

            response = self.client.summarization(
                text=text,
                model=model,
                max_length=max_length,
                min_length=min_length
            )

            return {
                "status": "success",
                "summary_text": response.get("summary_text", response),
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face summarization error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _question_answering(self, **kwargs) -> Dict[str, Any]:
        """
        Answer questions based on context
        """
        try:
            question = kwargs.get("question", "")
            context = kwargs.get("context", "")
            model = kwargs.get("model", "deepset/roberta-base-squad2")

            response = self.client.question_answering(
                question=question,
                context=context,
                model=model
            )

            return {
                "status": "success",
                "answer": response.get("answer", response),
                "score": response.get("score", None),
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face question answering error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _zero_shot_classification(self, **kwargs) -> Dict[str, Any]:
        """
        Classify text without training
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))
            labels = kwargs.get("labels", [])
            model = kwargs.get("model", "facebook/bart-large-mnli")
            multi_label = kwargs.get("multi_label", False)

            response = self.client.zero_shot_classification(
                text=text,
                labels=labels,
                model=model,
                multi_label=multi_label
            )

            return {
                "status": "success",
                "labels": response.get("labels", []),
                "scores": response.get("scores", []),
                "model": model
            }

        except Exception as e:
            logger.error(f"Hugging Face zero-shot classification error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _download_model(self, **kwargs) -> Dict[str, Any]:
        """
        Download model files from Hugging Face Hub
        """
        try:
            repo_id = kwargs.get("repo_id", kwargs.get("model", ""))
            filename = kwargs.get("filename", "pytorch_model.bin")
            cache_dir = kwargs.get("cache_dir", None)

            if not repo_id:
                return {"status": "error", "message": "repo_id required"}

            file_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=cache_dir,
                token=self.api_key if self.api_key else None
            )

            return {
                "status": "success",
                "file_path": file_path,
                "repo_id": repo_id,
                "filename": filename
            }

        except Exception as e:
            logger.error(f"Hugging Face download error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _list_models(self, **kwargs) -> Dict[str, Any]:
        """
        List models from Hugging Face Hub
        """
        try:
            task = kwargs.get("task", None)
            library = kwargs.get("library", None)
            limit = kwargs.get("limit", 20)
            sort = kwargs.get("sort", "downloads")

            models = self.api.list_models(
                task=task,
                library=library,
                limit=limit,
                sort=sort
            )

            model_list = []
            for model in models:
                model_list.append({
                    "id": model.modelId,
                    "downloads": model.downloads if hasattr(model, 'downloads') else 0,
                    "likes": model.likes if hasattr(model, 'likes') else 0,
                    "tags": model.tags if hasattr(model, 'tags') else []
                })

            return {
                "status": "success",
                "models": model_list,
                "count": len(model_list)
            }

        except Exception as e:
            logger.error(f"Hugging Face list models error: {str(e)}")
            return {"status": "error", "message": str(e)}
