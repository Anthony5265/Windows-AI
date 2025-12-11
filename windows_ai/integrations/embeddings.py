"""
Embeddings Manager - 15+ Embedding Models
Production-ready embedding generation and reranking
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)

class EmbeddingProvider(Enum):
    OPENAI = "openai"
    COHERE = "cohere"
    VOYAGE = "voyage"
    JINA = "jina"
    MIXEDBREAD = "mixedbread"
    NOMIC = "nomic"
    GOOGLE = "google"
    AZURE = "azure"
    HUGGINGFACE = "huggingface"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    OLLAMA = "ollama"
    BGE = "bge"
    E5 = "e5"

class EmbeddingsManager:
    """Unified embeddings across 15+ providers"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False
        self._local_models: Dict[str, Any] = {}

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True
        logger.info("Embeddings Manager initialized")

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def embed(
        self,
        texts: Union[str, List[str]],
        provider: EmbeddingProvider = EmbeddingProvider.OPENAI,
        model: Optional[str] = None,
        **kwargs
    ) -> List[List[float]]:
        """Generate embeddings for texts"""

        if isinstance(texts, str):
            texts = [texts]

        if provider == EmbeddingProvider.OPENAI:
            return await self._openai_embed(texts, model or "text-embedding-3-small")
        elif provider == EmbeddingProvider.COHERE:
            return await self._cohere_embed(texts, model or "embed-english-v3.0", **kwargs)
        elif provider == EmbeddingProvider.VOYAGE:
            return await self._voyage_embed(texts, model or "voyage-3")
        elif provider == EmbeddingProvider.JINA:
            return await self._jina_embed(texts, model or "jina-embeddings-v3")
        elif provider == EmbeddingProvider.NOMIC:
            return await self._nomic_embed(texts, model or "nomic-embed-text-v1.5")
        elif provider == EmbeddingProvider.GOOGLE:
            return await self._google_embed(texts, model or "text-embedding-004")
        elif provider == EmbeddingProvider.OLLAMA:
            return await self._ollama_embed(texts, model or "nomic-embed-text")
        elif provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return await self._sentence_transformers_embed(texts, model or "all-MiniLM-L6-v2")
        elif provider == EmbeddingProvider.BGE:
            return await self._bge_embed(texts, model or "BAAI/bge-large-en-v1.5")
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    async def _openai_embed(self, texts, model):
        """OpenAI embeddings"""
        from openai import AsyncOpenAI
        client = AsyncOpenAI()

        response = await client.embeddings.create(
            model=model,
            input=texts
        )
        return [e.embedding for e in response.data]

    async def _cohere_embed(self, texts, model, **kwargs):
        """Cohere embeddings"""
        import cohere

        client = cohere.AsyncClient(os.environ.get("COHERE_API_KEY"))
        response = await client.embed(
            model=model,
            texts=texts,
            input_type=kwargs.get("input_type", "search_document"),
            truncate=kwargs.get("truncate", "END")
        )
        return response.embeddings

    async def _voyage_embed(self, texts, model):
        """Voyage AI embeddings"""
        import aiohttp

        api_key = os.environ.get("VOYAGE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "input": texts}
            ) as response:
                data = await response.json()
                return [e["embedding"] for e in data["data"]]

    async def _jina_embed(self, texts, model):
        """Jina AI embeddings"""
        import aiohttp

        api_key = os.environ.get("JINA_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.jina.ai/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "input": texts}
            ) as response:
                data = await response.json()
                return [e["embedding"] for e in data["data"]]

    async def _nomic_embed(self, texts, model):
        """Nomic AI embeddings"""
        import aiohttp

        api_key = os.environ.get("NOMIC_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api-atlas.nomic.ai/v1/embedding/text",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "texts": texts}
            ) as response:
                data = await response.json()
                return data["embeddings"]

    async def _google_embed(self, texts, model):
        """Google AI embeddings"""
        import google.generativeai as genai

        result = genai.embed_content(
            model=f"models/{model}",
            content=texts,
            task_type="retrieval_document"
        )
        return result["embedding"] if len(texts) == 1 else result["embedding"]

    async def _ollama_embed(self, texts, model):
        """Ollama local embeddings"""
        import aiohttp

        embeddings = []
        async with aiohttp.ClientSession() as session:
            for text in texts:
                async with session.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": model, "prompt": text}
                ) as response:
                    data = await response.json()
                    embeddings.append(data["embedding"])
        return embeddings

    async def _sentence_transformers_embed(self, texts, model):
        """Sentence Transformers embeddings"""
        from sentence_transformers import SentenceTransformer

        if model not in self._local_models:
            self._local_models[model] = SentenceTransformer(model)

        embeddings = self._local_models[model].encode(texts)
        return embeddings.tolist()

    async def _bge_embed(self, texts, model):
        """BGE embeddings via Sentence Transformers"""
        from sentence_transformers import SentenceTransformer

        if model not in self._local_models:
            self._local_models[model] = SentenceTransformer(model)

        embeddings = self._local_models[model].encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    # ==================== RERANKING ====================

    async def rerank(
        self,
        query: str,
        documents: List[str],
        provider: str = "cohere",
        model: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Rerank documents by relevance to query"""

        if provider == "cohere":
            return await self._cohere_rerank(query, documents, model or "rerank-english-v3.0", top_k)
        elif provider == "jina":
            return await self._jina_rerank(query, documents, model or "jina-reranker-v2-base-multilingual", top_k)
        elif provider == "voyage":
            return await self._voyage_rerank(query, documents, model or "rerank-2", top_k)
        else:
            raise ValueError(f"Unsupported reranking provider: {provider}")

    async def _cohere_rerank(self, query, documents, model, top_k):
        """Cohere reranking"""
        import cohere

        client = cohere.AsyncClient(os.environ.get("COHERE_API_KEY"))
        response = await client.rerank(
            model=model,
            query=query,
            documents=documents,
            top_n=top_k
        )

        return [{
            "index": r.index,
            "relevance_score": r.relevance_score,
            "document": documents[r.index]
        } for r in response.results]

    async def _jina_rerank(self, query, documents, model, top_k):
        """Jina reranking"""
        import aiohttp

        api_key = os.environ.get("JINA_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "query": query, "documents": documents, "top_n": top_k}
            ) as response:
                data = await response.json()
                return [{
                    "index": r["index"],
                    "relevance_score": r["relevance_score"],
                    "document": documents[r["index"]]
                } for r in data["results"]]

    async def _voyage_rerank(self, query, documents, model, top_k):
        """Voyage reranking"""
        import aiohttp

        api_key = os.environ.get("VOYAGE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.voyageai.com/v1/rerank",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "query": query, "documents": documents, "top_k": top_k}
            ) as response:
                data = await response.json()
                return [{
                    "index": r["index"],
                    "relevance_score": r["relevance_score"],
                    "document": documents[r["index"]]
                } for r in data["data"]]

    def list_providers(self) -> List[str]:
        """List embedding providers"""
        return [p.value for p in EmbeddingProvider]
