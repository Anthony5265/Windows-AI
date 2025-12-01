"""
Cohere Plugin - Production Grade
Full integration with Cohere Command, Embed, Rerank models
"""
from typing import Dict, Any, List, Optional
import os
import logging
import json
from datetime import datetime

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

logger = logging.getLogger(__name__)

class Plugin:
    """
    Production-grade Cohere Plugin

    Supports:
    - Command R, Command R+, Command models (chat/generation)
    - Command Light (lightweight generation)
    - Embed models (multilingual embeddings)
    - Rerank models (search re-ranking)
    - Streaming responses
    - Token counting
    - Cost tracking
    """

    def __init__(self):
        self.name = "Cohere"
        self.version = "2.0.0"
        self.description = "Production Cohere integration with Command, Embed, Rerank models"

        # Configuration
        self.api_key = os.getenv("COHERE_API_KEY", "")
        self.timeout = int(os.getenv("COHERE_TIMEOUT", "120"))

        # Initialize client if available
        self.client = None
        if COHERE_AVAILABLE and self.api_key:
            self.client = cohere.Client(
                api_key=self.api_key,
                timeout=self.timeout
            )

        # Model pricing (per 1M tokens) - as of 2025
        self.pricing = {
            "command-r-plus": {"input": 3.00, "output": 15.00},
            "command-r": {"input": 0.50, "output": 1.50},
            "command": {"input": 1.00, "output": 2.00},
            "command-light": {"input": 0.30, "output": 0.60},
            "embed-english-v3.0": {"input": 0.10, "output": 0},
            "embed-multilingual-v3.0": {"input": 0.10, "output": 0},
            "rerank-english-v3.0": {"search": 2.00},
            "rerank-multilingual-v3.0": {"search": 2.00},
        }

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Cohere request

        Args:
            action (str): Action to perform
                - "chat": Chat completion
                - "generate": Text generation
                - "embed": Generate embeddings
                - "rerank": Rerank search results
                - "classify": Text classification
                - "summarize": Summarize text
                - "models": List available models
                - "stats": Get usage statistics
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not COHERE_AVAILABLE:
            return {
                "status": "error",
                "message": "Cohere SDK not installed. Install with: pip install cohere"
            }

        if not self.client:
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
            elif action == "models":
                return self._list_models()
            elif action == "stats":
                return self._get_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Cohere plugin error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _chat(self, **kwargs) -> Dict[str, Any]:
        """
        Chat with Cohere Command models

        Args:
            message (str): User message
            chat_history (List[Dict]): Conversation history
            model (str): Model to use (default: command-r)
            temperature (float): Sampling temperature 0-2
            max_tokens (int): Maximum tokens to generate
            stream (bool): Enable streaming responses
            preamble (str): System preamble/prompt
            connectors (List): RAG connectors for grounded generation
        """
        message = kwargs.get("message", "")
        chat_history = kwargs.get("chat_history", [])
        model = kwargs.get("model", "command-r")
        temperature = kwargs.get("temperature", 0.3)
        max_tokens = kwargs.get("max_tokens", None)
        stream = kwargs.get("stream", False)
        preamble = kwargs.get("preamble", None)
        connectors = kwargs.get("connectors", None)

        if not message:
            return {"status": "error", "message": "No message provided"}

        try:
            # Prepare request parameters
            request_params = {
                "message": message,
                "model": model,
                "temperature": temperature,
            }

            if chat_history:
                request_params["chat_history"] = chat_history
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            if preamble:
                request_params["preamble"] = preamble
            if connectors:
                request_params["connectors"] = connectors

            if stream:
                # Streaming response
                response_stream = self.client.chat_stream(**request_params)

                collected_text = []
                for event in response_stream:
                    if event.event_type == "text-generation":
                        collected_text.append(event.text)

                full_response = "".join(collected_text)

                return {
                    "status": "success",
                    "response": full_response,
                    "model": model,
                    "streaming": True
                }
            else:
                # Standard response
                response = self.client.chat(**request_params)

                # Track usage
                if hasattr(response, 'meta') and response.meta:
                    if hasattr(response.meta, 'billed_units'):
                        self.total_input_tokens += response.meta.billed_units.input_tokens or 0
                        self.total_output_tokens += response.meta.billed_units.output_tokens or 0

                        # Calculate cost
                        if model in self.pricing:
                            input_cost = (response.meta.billed_units.input_tokens / 1_000_000) * self.pricing[model]["input"]
                            output_cost = (response.meta.billed_units.output_tokens / 1_000_000) * self.pricing[model]["output"]
                            self.total_cost += (input_cost + output_cost)

                return {
                    "status": "success",
                    "response": response.text,
                    "model": model,
                    "finish_reason": response.finish_reason if hasattr(response, 'finish_reason') else None,
                    "citations": response.citations if hasattr(response, 'citations') else None,
                    "documents": response.documents if hasattr(response, 'documents') else None,
                    "usage": {
                        "input_tokens": response.meta.billed_units.input_tokens if hasattr(response, 'meta') and response.meta else 0,
                        "output_tokens": response.meta.billed_units.output_tokens if hasattr(response, 'meta') and response.meta else 0,
                    }
                }

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise

    async def _generate(self, **kwargs) -> Dict[str, Any]:
        """
        Generate text with Cohere

        Args:
            prompt (str): Prompt text
            model (str): Model to use
            temperature (float): Sampling temperature
            max_tokens (int): Maximum tokens
            k (int): Top-k sampling
            p (float): Top-p sampling
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "command")
        temperature = kwargs.get("temperature", 0.75)
        max_tokens = kwargs.get("max_tokens", 300)
        k = kwargs.get("k", 0)
        p = kwargs.get("p", 0.75)

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        try:
            response = self.client.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                k=k,
                p=p
            )

            # Track usage
            if hasattr(response, 'meta') and response.meta:
                if hasattr(response.meta, 'billed_units'):
                    self.total_input_tokens += response.meta.billed_units.input_tokens or 0
                    self.total_output_tokens += response.meta.billed_units.output_tokens or 0

            return {
                "status": "success",
                "text": response.generations[0].text if response.generations else "",
                "model": model
            }

        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            raise

    async def _embed(self, **kwargs) -> Dict[str, Any]:
        """
        Generate embeddings

        Args:
            texts (List[str]): Texts to embed
            model (str): Embedding model
            input_type (str): Type of input (search_document, search_query, classification, clustering)
        """
        texts = kwargs.get("texts", [])
        model = kwargs.get("model", "embed-english-v3.0")
        input_type = kwargs.get("input_type", "search_document")

        if not texts:
            return {"status": "error", "message": "No texts provided"}

        try:
            response = self.client.embed(
                texts=texts,
                model=model,
                input_type=input_type
            )

            # Track usage (embeddings are billed by input tokens)
            estimated_tokens = sum(len(text.split()) * 1.3 for text in texts)  # Rough estimate
            self.total_input_tokens += int(estimated_tokens)

            if model in self.pricing:
                cost = (estimated_tokens / 1_000_000) * self.pricing[model]["input"]
                self.total_cost += cost

            return {
                "status": "success",
                "embeddings": response.embeddings,
                "model": model,
                "dimensions": len(response.embeddings[0]) if response.embeddings else 0
            }

        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            raise

    async def _rerank(self, **kwargs) -> Dict[str, Any]:
        """
        Rerank search results

        Args:
            query (str): Search query
            documents (List[str|Dict]): Documents to rerank
            model (str): Rerank model
            top_n (int): Number of top results to return
        """
        query = kwargs.get("query", "")
        documents = kwargs.get("documents", [])
        model = kwargs.get("model", "rerank-english-v3.0")
        top_n = kwargs.get("top_n", None)

        if not query or not documents:
            return {"status": "error", "message": "Query and documents required"}

        try:
            response = self.client.rerank(
                query=query,
                documents=documents,
                model=model,
                top_n=top_n
            )

            # Track usage (rerank is billed per search)
            if model in self.pricing:
                cost = (len(documents) / 1000) * self.pricing[model]["search"]
                self.total_cost += cost

            return {
                "status": "success",
                "results": [
                    {
                        "index": result.index,
                        "relevance_score": result.relevance_score,
                        "document": result.document if hasattr(result, 'document') else None
                    }
                    for result in response.results
                ],
                "model": model
            }

        except Exception as e:
            logger.error(f"Rerank error: {str(e)}")
            raise

    async def _classify(self, **kwargs) -> Dict[str, Any]:
        """
        Classify text

        Args:
            inputs (List[str]): Texts to classify
            examples (List[Dict]): Training examples
            model (str): Model to use
        """
        inputs = kwargs.get("inputs", [])
        examples = kwargs.get("examples", [])
        model = kwargs.get("model", "embed-english-v3.0")

        if not inputs or not examples:
            return {"status": "error", "message": "Inputs and examples required"}

        try:
            response = self.client.classify(
                inputs=inputs,
                examples=examples,
                model=model
            )

            return {
                "status": "success",
                "classifications": [
                    {
                        "input": c.input,
                        "prediction": c.prediction,
                        "confidence": c.confidence
                    }
                    for c in response.classifications
                ]
            }

        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            raise

    async def _summarize(self, **kwargs) -> Dict[str, Any]:
        """
        Summarize text

        Args:
            text (str): Text to summarize
            length (str): Summary length (short, medium, long)
            format (str): Summary format (paragraph, bullets)
            model (str): Model to use
        """
        text = kwargs.get("text", "")
        length = kwargs.get("length", "medium")
        format_type = kwargs.get("format", "paragraph")
        model = kwargs.get("model", "command")

        if not text:
            return {"status": "error", "message": "No text provided"}

        try:
            response = self.client.summarize(
                text=text,
                length=length,
                format=format_type,
                model=model
            )

            return {
                "status": "success",
                "summary": response.summary,
                "model": model
            }

        except Exception as e:
            logger.error(f"Summarization error: {str(e)}")
            raise

    def _list_models(self) -> Dict[str, Any]:
        """List available Cohere models"""
        models = [
            {
                "id": "command-r-plus",
                "name": "Command R+",
                "description": "Most capable Command model for complex RAG and tool use",
                "type": "chat"
            },
            {
                "id": "command-r",
                "name": "Command R",
                "description": "Balanced Command model for RAG and conversational AI",
                "type": "chat"
            },
            {
                "id": "command",
                "name": "Command",
                "description": "Standard generation model",
                "type": "generation"
            },
            {
                "id": "command-light",
                "name": "Command Light",
                "description": "Lightweight, fast generation model",
                "type": "generation"
            },
            {
                "id": "embed-english-v3.0",
                "name": "Embed English v3",
                "description": "English embeddings with 1024 dimensions",
                "type": "embedding"
            },
            {
                "id": "embed-multilingual-v3.0",
                "name": "Embed Multilingual v3",
                "description": "Multilingual embeddings supporting 100+ languages",
                "type": "embedding"
            },
            {
                "id": "rerank-english-v3.0",
                "name": "Rerank English v3",
                "description": "English reranking model",
                "type": "rerank"
            },
            {
                "id": "rerank-multilingual-v3.0",
                "name": "Rerank Multilingual v3",
                "description": "Multilingual reranking model",
                "type": "rerank"
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
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_cost_usd": round(self.total_cost, 4),
                "timestamp": datetime.now().isoformat()
            }
        }
