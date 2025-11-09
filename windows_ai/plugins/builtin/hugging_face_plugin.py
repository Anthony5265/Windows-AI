"""
Hugging Face Plugin - Production Grade
Full integration with Hugging Face Inference API and Hub
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime

try:
    from huggingface_hub import InferenceClient, AsyncInferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Hugging Face Plugin

    Supports:
    - Text generation (Llama, Mistral, Falcon, etc.)
    - Chat completion
    - Text classification
    - Token classification (NER)
    - Question answering
    - Summarization
    - Translation
    - Text-to-image (Stable Diffusion, FLUX, etc.)
    - Image-to-text (image captioning)
    - Embeddings (sentence transformers)
    - Audio transcription
    """

    def __init__(self):
        self.name = "Hugging Face"
        self.version = "2.0.0"
        self.description = "Production Hugging Face integration with Inference API"

        # Configuration
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", "") or os.getenv("HF_TOKEN", "")
        self.timeout = int(os.getenv("HF_TIMEOUT", "120"))

        # Initialize client if available
        self.client = None
        if HF_AVAILABLE:
            self.client = AsyncInferenceClient(
                token=self.api_key if self.api_key else None,
                timeout=self.timeout
            )

        # Popular models by task
        self.default_models = {
            "text_generation": "meta-llama/Meta-Llama-3-8B-Instruct",
            "chat": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "text_to_image": "stabilityai/stable-diffusion-xl-base-1.0",
            "image_to_text": "Salesforce/blip-image-captioning-large",
            "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
            "summarization": "facebook/bart-large-cnn",
            "translation": "Helsinki-NLP/opus-mt-en-de",
            "question_answering": "deepset/roberta-base-squad2",
            "text_classification": "distilbert-base-uncased-finetuned-sst-2-english",
            "audio_transcription": "openai/whisper-large-v3"
        }

        # Usage tracking (Note: HF Inference API pricing varies by model)
        self.total_requests = 0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Hugging Face request

        Args:
            action (str): Action to perform
                - "text_generation": Generate text
                - "chat": Chat completion
                - "text_to_image": Generate image from text
                - "image_to_text": Caption/describe image
                - "embed": Generate embeddings
                - "summarize": Summarize text
                - "translate": Translate text
                - "qa": Question answering
                - "classify": Text classification
                - "transcribe": Audio transcription
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not HF_AVAILABLE:
            return {
                "status": "error",
                "message": "Hugging Face Hub not installed. Install with: pip install huggingface-hub"
            }

        try:
            action = kwargs.get("action", "text_generation")

            # Route to appropriate handler
            if action == "text_generation":
                return await self._text_generation(**kwargs)
            elif action == "chat":
                return await self._chat(**kwargs)
            elif action == "text_to_image":
                return await self._text_to_image(**kwargs)
            elif action == "image_to_text":
                return await self._image_to_text(**kwargs)
            elif action == "embed":
                return await self._embed(**kwargs)
            elif action == "summarize":
                return await self._summarize(**kwargs)
            elif action == "translate":
                return await self._translate(**kwargs)
            elif action == "qa":
                return await self._question_answering(**kwargs)
            elif action == "classify":
                return await self._classify(**kwargs)
            elif action == "transcribe":
                return await self._transcribe(**kwargs)
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Hugging Face plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _text_generation(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text

        Args:
            prompt (str): Input prompt
            model (str): Model to use
            max_tokens (int): Maximum tokens to generate
            temperature (float): Sampling temperature
            top_p (float): Nucleus sampling
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_models["text_generation"])
        max_tokens = kwargs.get("max_tokens", 500)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 0.95)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        try:
            response = await self.client.text_generation(
                prompt=prompt,
                model=model,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )

            self.total_requests += 1

            return {
                "status": "success",
                "text": response,
                "model": model
            }

        except Exception as e:
            logger.error(f"Text generation error: {str(e)}")
            raise

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat completion

        Args:
            messages (List[Dict]): Conversation messages
            model (str): Model to use
            max_tokens (int): Maximum tokens
            temperature (float): Sampling temperature
        """
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", self.default_models["chat"])
        max_tokens = kwargs.get("max_tokens", 500)
        temperature = kwargs.get("temperature", 0.7)

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        try:
            response = await self.client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )

            self.total_requests += 1

            return {
                "status": "success",
                "response": response.choices[0].message.content,
                "model": model,
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }

        except Exception as e:
            logger.error(f"Chat completion error: {str(e)}")
            raise

    async def _text_to_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate image from text

        Args:
            prompt (str): Image description
            model (str): Model to use
            negative_prompt (str): What to avoid
            num_inference_steps (int): Quality/speed tradeoff
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", self.default_models["text_to_image"])
        negative_prompt = kwargs.get("negative_prompt", None)
        num_inference_steps = kwargs.get("num_inference_steps", 30)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        try:
            image = await self.client.text_to_image(
                prompt=prompt,
                model=model,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps
            )

            self.total_requests += 1

            # Convert PIL Image to base64 for transmission
            import base64
            import io
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return {
                "status": "success",
                "image_base64": img_str,
                "model": model
            }

        except Exception as e:
            logger.error(f"Text-to-image error: {str(e)}")
            raise

    async def _image_to_text(self, **kwargs) -> Dict[str, Any]:
        """
        Generate caption for image

        Args:
            image_url (str): URL of image
            image_path (str): Local path to image
            model (str): Model to use
        """
        image_url = kwargs.get("image_url")
        image_path = kwargs.get("image_path")
        model = kwargs.get("model", self.default_models["image_to_text"])

        if not image_url and not image_path:
            return {"status": "error", "message": "No image provided"}

        try:
            if image_path:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                caption = await self.client.image_to_text(
                    image=image_data,
                    model=model
                )
            else:
                caption = await self.client.image_to_text(
                    image=image_url,
                    model=model
                )

            self.total_requests += 1

            return {
                "status": "success",
                "caption": caption,
                "model": model
            }

        except Exception as e:
            logger.error(f"Image-to-text error: {str(e)}")
            raise

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings

        Args:
            texts (List[str]): Texts to embed
            model (str): Embedding model
        """
        texts = kwargs.get("texts", [])
        model = kwargs.get("model", self.default_models["embeddings"])

        if not texts:
            return {"status": "error", "message": "No texts provided"}

        try:
            # Handle single string input
            if isinstance(texts, str):
                texts = [texts]

            embeddings = await self.client.feature_extraction(
                text=texts,
                model=model
            )

            self.total_requests += 1

            return {
                "status": "success",
                "embeddings": embeddings,
                "model": model,
                "dimensions": len(embeddings[0]) if embeddings else 0
            }

        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            raise

    async def _summarize(self, **kwargs) -> Dict[str, Any]:
        """
        Summarize text

        Args:
            text (str): Text to summarize
            model (str): Model to use
            max_length (int): Maximum summary length
            min_length (int): Minimum summary length
        """
        text = kwargs.get("text", "")
        model = kwargs.get("model", self.default_models["summarization"])
        max_length = kwargs.get("max_length", 130)
        min_length = kwargs.get("min_length", 30)

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            summary = await self.client.summarization(
                text=text,
                model=model,
                parameters={"max_length": max_length, "min_length": min_length}
            )

            self.total_requests += 1

            return {
                "status": "success",
                "summary": summary.summary_text if hasattr(summary, 'summary_text') else str(summary),
                "model": model
            }

        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            raise

    async def _translate(self, **kwargs) -> Dict[str, Any]:
        """
        Translate text

        Args:
            text (str): Text to translate
            model (str): Translation model (e.g., Helsinki-NLP/opus-mt-en-de)
        """
        text = kwargs.get("text", "")
        model = kwargs.get("model", self.default_models["translation"])

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            translation = await self.client.translation(
                text=text,
                model=model
            )

            self.total_requests += 1

            return {
                "status": "success",
                "translation": translation.translation_text if hasattr(translation, 'translation_text') else str(translation),
                "model": model
            }

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise

    async def _question_answering(self, **kwargs) -> Dict[str, Any]:
        """
        Answer questions based on context

        Args:
            question (str): Question to answer
            context (str): Context containing the answer
            model (str): Model to use
        """
        question = kwargs.get("question", "")
        context = kwargs.get("context", "")
        model = kwargs.get("model", self.default_models["question_answering"])

        if not question or not context:
            return {"status": "error", "message": "Question and context required"}

        try:
            answer = await self.client.question_answering(
                question=question,
                context=context,
                model=model
            )

            self.total_requests += 1

            return {
                "status": "success",
                "answer": answer.answer if hasattr(answer, 'answer') else str(answer),
                "score": answer.score if hasattr(answer, 'score') else None,
                "model": model
            }

        except Exception as e:
            logger.error(f"Question answering error: {str(e)}")
            raise

    async def _classify(self, **kwargs) -> Dict[str, Any]:
        """
        Classify text

        Args:
            text (str): Text to classify
            model (str): Classification model
        """
        text = kwargs.get("text", "")
        model = kwargs.get("model", self.default_models["text_classification"])

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            result = await self.client.text_classification(
                text=text,
                model=model
            )

            self.total_requests += 1

            return {
                "status": "success",
                "classifications": [
                    {
                        "label": item.label if hasattr(item, 'label') else item.get('label'),
                        "score": item.score if hasattr(item, 'score') else item.get('score')
                    }
                    for item in result
                ] if isinstance(result, list) else result,
                "model": model
            }

        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            raise

    async def _transcribe(self, **kwargs) -> Dict[str, Any]:
        """
        Transcribe audio

        Args:
            audio_path (str): Path to audio file
            model (str): Transcription model
        """
        audio_path = kwargs.get("audio_path", "")
        model = kwargs.get("model", self.default_models["audio_transcription"])

        if not audio_path:
            return {"status": "error", "message": "No audio file provided"}

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            transcription = await self.client.automatic_speech_recognition(
                audio=audio_data,
                model=model
            )

            self.total_requests += 1

            return {
                "status": "success",
                "transcription": transcription.text if hasattr(transcription, 'text') else str(transcription),
                "model": model
            }

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise

    def _get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "status": "success",
            "stats": {
                "total_requests": self.total_requests,
                "timestamp": datetime.now().isoformat()
            }
        }
