"""
Cohere AI Plugin (Official SDK)
Production-grade integration with Cohere's official Python SDK
"""
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logger.warning("cohere package not installed. Install with: pip install cohere")


class Plugin:
    """Plugin for Cohere AI using official SDK"""

    def __init__(self):
        self.name = "Cohere Official"
        self.version = "2.0.0"
        self.description = "Cohere AI integration using official SDK with Command, Embed, and Rerank"

        # Configuration
        self.api_key = os.getenv("COHERE_API_KEY", "")
        self.client: Optional[cohere.Client] = None

        # Initialize client if API key is available
        if COHERE_AVAILABLE and self.api_key:
            try:
                self.client = cohere.Client(api_key=self.api_key)
                logger.info("Cohere client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {e}")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Cohere AI request

        Args:
            action (str): Action to perform (chat, generate, embed, rerank, classify)
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not COHERE_AVAILABLE:
            return {
                "status": "error",
                "message": "Cohere SDK not installed. Install with: pip install cohere"
            }

        if not self.api_key or not self.client:
            return {
                "status": "error",
                "message": "Cohere API key not configured. Set COHERE_API_KEY environment variable."
            }

        try:
            action = kwargs.get("action", "chat")

            # Route to appropriate handler
            if action == "chat":
                return await self._chat(**kwargs)
            elif action == "generate":
                return await self._generate(**kwargs)
            elif action == "embed":
                return await self._embed(**kwargs)
            elif action == "rerank":
                return await self._rerank(**kwargs)
            elif action == "classify":
                return await self._classify(**kwargs)
            elif action == "summarize":
                return await self._summarize(**kwargs)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Cohere error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat with Cohere Command models

        Supports streaming and conversation history
        """
        try:
            message = kwargs.get("message", kwargs.get("prompt", ""))
            model = kwargs.get("model", "command")
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            chat_history = kwargs.get("chat_history", [])

            # Prepare chat history in Cohere format
            cohere_history = []
            for msg in chat_history:
                cohere_history.append({
                    "role": msg.get("role", "USER"),
                    "message": msg.get("content", msg.get("message", ""))
                })

            response = self.client.chat(
                message=message,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                chat_history=cohere_history if cohere_history else None,
                prompt_truncation="AUTO"
            )

            return {
                "status": "success",
                "response": response.text,
                "citations": response.citations if hasattr(response, 'citations') else [],
                "documents": response.documents if hasattr(response, 'documents') else [],
                "generation_id": response.generation_id,
                "token_count": {
                    "prompt_tokens": response.meta.billed_units.input_tokens if hasattr(response, 'meta') else 0,
                    "completion_tokens": response.meta.billed_units.output_tokens if hasattr(response, 'meta') else 0
                }
            }

        except Exception as e:
            logger.error(f"Cohere chat error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _generate(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text using Cohere's generation API

        Legacy generation endpoint, use chat for modern applications
        """
        try:
            prompt = kwargs.get("prompt", "")
            model = kwargs.get("model", "command")
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1000)
            k = kwargs.get("k", 0)  # Top-k sampling
            p = kwargs.get("p", 0.75)  # Top-p sampling
            frequency_penalty = kwargs.get("frequency_penalty", 0.0)
            presence_penalty = kwargs.get("presence_penalty", 0.0)

            response = self.client.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                k=k,
                p=p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )

            return {
                "status": "success",
                "text": response.generations[0].text,
                "generation_id": response.generations[0].id,
                "likelihood": response.generations[0].likelihood if hasattr(response.generations[0], 'likelihood') else None
            }

        except Exception as e:
            logger.error(f"Cohere generate error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings for texts

        Supports both text and image embeddings
        """
        try:
            texts = kwargs.get("texts", kwargs.get("text", []))
            if isinstance(texts, str):
                texts = [texts]

            model = kwargs.get("model", "embed-english-v3.0")
            input_type = kwargs.get("input_type", "search_document")
            embedding_types = kwargs.get("embedding_types", ["float"])

            response = self.client.embed(
                texts=texts,
                model=model,
                input_type=input_type,
                embedding_types=embedding_types
            )

            return {
                "status": "success",
                "embeddings": response.embeddings.float if hasattr(response.embeddings, 'float') else response.embeddings,
                "embedding_type": embedding_types[0],
                "model": model,
                "num_embeddings": len(texts)
            }

        except Exception as e:
            logger.error(f"Cohere embed error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _rerank(self, **kwargs) -> Dict[str, Any]:
        """
        Rerank documents based on relevance to a query

        Useful for search and retrieval applications
        """
        try:
            query = kwargs.get("query", "")
            documents = kwargs.get("documents", [])
            model = kwargs.get("model", "rerank-english-v3.0")
            top_n = kwargs.get("top_n", len(documents))

            response = self.client.rerank(
                query=query,
                documents=documents,
                model=model,
                top_n=top_n
            )

            results = []
            for result in response.results:
                results.append({
                    "index": result.index,
                    "relevance_score": result.relevance_score,
                    "document": documents[result.index] if result.index < len(documents) else None
                })

            return {
                "status": "success",
                "results": results,
                "model": model
            }

        except Exception as e:
            logger.error(f"Cohere rerank error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _classify(self, **kwargs) -> Dict[str, Any]:
        """
        Classify text into categories

        Requires examples for training
        """
        try:
            inputs = kwargs.get("inputs", kwargs.get("text", []))
            if isinstance(inputs, str):
                inputs = [inputs]

            examples = kwargs.get("examples", [])
            model = kwargs.get("model", "embed-english-v3.0")

            if not examples:
                return {
                    "status": "error",
                    "message": "Examples required for classification. Provide list of {text, label} dicts."
                }

            response = self.client.classify(
                inputs=inputs,
                examples=examples,
                model=model
            )

            results = []
            for classification in response.classifications:
                results.append({
                    "input": classification.input,
                    "prediction": classification.prediction,
                    "confidence": classification.confidence,
                    "labels": classification.labels if hasattr(classification, 'labels') else {}
                })

            return {
                "status": "success",
                "classifications": results,
                "model": model
            }

        except Exception as e:
            logger.error(f"Cohere classify error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _summarize(self, **kwargs) -> Dict[str, Any]:
        """
        Summarize text

        Uses Cohere's summarization model
        """
        try:
            text = kwargs.get("text", kwargs.get("prompt", ""))
            length = kwargs.get("length", "medium")  # short, medium, long
            format = kwargs.get("format", "paragraph")  # paragraph, bullets
            model = kwargs.get("model", "command")
            temperature = kwargs.get("temperature", 0.3)

            response = self.client.summarize(
                text=text,
                length=length,
                format=format,
                model=model,
                temperature=temperature
            )

            return {
                "status": "success",
                "summary": response.summary,
                "generation_id": response.id
            }

        except Exception as e:
            logger.error(f"Cohere summarize error: {str(e)}")
            return {"status": "error", "message": str(e)}
