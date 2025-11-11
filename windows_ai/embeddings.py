"""
Embedding Generation for RAG System
Supports multiple embedding models with caching
"""
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import json
import os
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingProvider(Enum):
    """Supported embedding providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    SENTENCE_TRANSFORMERS = "sentence_transformers"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    provider: EmbeddingProvider
    model_name: str
    dimension: int
    batch_size: int = 100
    cache_enabled: bool = True
    cache_directory: str = "./embedding_cache"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30


class EmbeddingCache:
    """Cache for storing and retrieving embeddings"""

    def __init__(self, cache_directory: str, enabled: bool = True):
        self.cache_directory = Path(cache_directory)
        self.enabled = enabled
        self._memory_cache = {}  # In-memory cache for speed
        self._max_memory_cache_size = 1000

        if self.enabled:
            self.cache_directory.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key from text and model name"""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        # Use first 2 chars for subdirectory to avoid too many files in one dir
        subdir = cache_key[:2]
        cache_dir = self.cache_directory / subdir
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / f"{cache_key}.json"

    def get(self, text: str, model_name: str) -> Optional[List[float]]:
        """Retrieve embedding from cache"""
        if not self.enabled:
            return None

        cache_key = self._get_cache_key(text, model_name)

        # Check memory cache first
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Check disk cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    embedding = data.get('embedding')

                    # Store in memory cache
                    if len(self._memory_cache) < self._max_memory_cache_size:
                        self._memory_cache[cache_key] = embedding

                    return embedding
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                return None

        return None

    def set(self, text: str, model_name: str, embedding: List[float]) -> None:
        """Store embedding in cache"""
        if not self.enabled:
            return

        cache_key = self._get_cache_key(text, model_name)

        # Store in memory cache
        if len(self._memory_cache) < self._max_memory_cache_size:
            self._memory_cache[cache_key] = embedding

        # Store in disk cache
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'text': text[:200],  # Store truncated text for debugging
                    'model': model_name,
                    'embedding': embedding
                }, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def clear(self) -> None:
        """Clear all caches"""
        self._memory_cache.clear()

        if self.enabled and self.cache_directory.exists():
            for cache_file in self.cache_directory.rglob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "memory_cache_size": len(self._memory_cache),
            "disk_cache_enabled": self.enabled
        }

        if self.enabled and self.cache_directory.exists():
            cache_files = list(self.cache_directory.rglob("*.json"))
            stats["disk_cache_files"] = len(cache_files)
            stats["cache_directory"] = str(self.cache_directory)

        return stats


class EmbeddingModel(ABC):
    """Abstract base class for embedding models"""

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.cache = EmbeddingCache(
            config.cache_directory,
            config.cache_enabled
        )
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass

    async def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for one or more texts.

        Args:
            texts: Single text string or list of texts

        Returns:
            Single embedding or list of embeddings
        """
        # Handle single text
        if isinstance(texts, str):
            return await self.embed_single(texts)

        # Handle list of texts with batching
        return await self.embed_batch(texts)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches"""
        all_embeddings = []
        batch_size = self.config.batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._embed_batch_internal(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _embed_batch_internal(self, texts: List[str]) -> List[List[float]]:
        """Internal method to embed a batch of texts"""
        embeddings = []

        # Check cache first
        uncached_texts = []
        uncached_indices = []

        for idx, text in enumerate(texts):
            cached_embedding = self.cache.get(text, self.config.model_name)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(idx)

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = await self._generate_embeddings(uncached_texts)

            # Store in cache and fill placeholders
            for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                self.cache.set(text, self.config.model_name, embedding)
                embeddings[idx] = embedding

        return embeddings

    @abstractmethod
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings without caching (to be implemented by subclasses)"""
        pass

    def validate_dimension(self, embedding: List[float]) -> bool:
        """Validate embedding dimension"""
        return len(embedding) == self.config.dimension


class OpenAIEmbedding(EmbeddingModel):
    """OpenAI embedding model"""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        if not config:
            # Default configuration for OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

            # Determine dimension based on model
            dimension_map = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536
            }

            config = EmbeddingConfig(
                provider=EmbeddingProvider.OPENAI,
                model_name=model_name,
                dimension=dimension_map.get(model_name, 1536),
                api_key=api_key
            )

        super().__init__(config)

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.config.api_key)
            self.available = True
        except ImportError:
            self.logger.error("OpenAI library not installed. Install with: pip install openai")
            self.available = False

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        results = await self._generate_embeddings([text])
        return results[0]

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        if not self.available:
            raise RuntimeError("OpenAI client not available")

        try:
            response = await self.client.embeddings.create(
                model=self.config.model_name,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            self.logger.error(f"OpenAI embedding error: {e}")
            raise


class OllamaEmbedding(EmbeddingModel):
    """Ollama embedding model for local embeddings"""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        if not config:
            model_name = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

            config = EmbeddingConfig(
                provider=EmbeddingProvider.OLLAMA,
                model_name=model_name,
                dimension=768,  # Default for nomic-embed-text
                base_url=base_url
            )

        super().__init__(config)

        try:
            import httpx
            self.client = httpx.AsyncClient(timeout=self.config.timeout)
            self.available = True
        except ImportError:
            self.logger.error("httpx library not installed. Install with: pip install httpx")
            self.available = False

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        results = await self._generate_embeddings([text])
        return results[0]

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama API"""
        if not self.available:
            raise RuntimeError("Ollama client not available")

        embeddings = []

        try:
            # Ollama processes one text at a time
            for text in texts:
                response = await self.client.post(
                    f"{self.config.base_url}/api/embeddings",
                    json={
                        "model": self.config.model_name,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"])

            return embeddings

        except Exception as e:
            self.logger.error(f"Ollama embedding error: {e}")
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.available:
            await self.client.aclose()


class SentenceTransformerEmbedding(EmbeddingModel):
    """Local sentence transformer embedding model"""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        if not config:
            model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

            # Common model dimensions
            dimension_map = {
                "all-MiniLM-L6-v2": 384,
                "all-mpnet-base-v2": 768,
                "paraphrase-multilingual-MiniLM-L12-v2": 384
            }

            config = EmbeddingConfig(
                provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
                model_name=model_name,
                dimension=dimension_map.get(model_name, 384)
            )

        super().__init__(config)

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.config.model_name)
            self.available = True
        except ImportError:
            self.logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.available = False

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        results = await self._generate_embeddings([text])
        return results[0]

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence transformers"""
        if not self.available:
            raise RuntimeError("SentenceTransformer model not available")

        try:
            # Run in thread pool since sentence_transformers is synchronous
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts, convert_to_numpy=True)
            )

            return embeddings.tolist()

        except Exception as e:
            self.logger.error(f"SentenceTransformer embedding error: {e}")
            raise


class EmbeddingManager:
    """Manager for creating and managing embedding models"""

    def __init__(self):
        self.models = {}

    def get_model(
        self,
        provider: Union[str, EmbeddingProvider],
        config: Optional[EmbeddingConfig] = None
    ) -> EmbeddingModel:
        """
        Get or create an embedding model.

        Args:
            provider: Provider name or enum
            config: Optional configuration

        Returns:
            Embedding model instance
        """
        if isinstance(provider, str):
            provider = EmbeddingProvider(provider)

        # Return cached model if available
        cache_key = f"{provider.value}:{config.model_name if config else 'default'}"
        if cache_key in self.models:
            return self.models[cache_key]

        # Create new model
        if provider == EmbeddingProvider.OPENAI:
            model = OpenAIEmbedding(config)
        elif provider == EmbeddingProvider.OLLAMA:
            model = OllamaEmbedding(config)
        elif provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            model = SentenceTransformerEmbedding(config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.models[cache_key] = model
        return model

    def list_models(self) -> List[str]:
        """List all cached models"""
        return list(self.models.keys())

    def clear_cache(self, provider: Optional[str] = None) -> None:
        """Clear embedding cache for all or specific provider"""
        if provider:
            for key, model in self.models.items():
                if key.startswith(provider):
                    model.cache.clear()
        else:
            for model in self.models.values():
                model.cache.clear()


# Global embedding manager instance
_embedding_manager = EmbeddingManager()


def get_embedding_model(
    provider: Union[str, EmbeddingProvider] = "openai",
    config: Optional[EmbeddingConfig] = None
) -> EmbeddingModel:
    """
    Convenience function to get an embedding model.

    Args:
        provider: Provider name (openai, ollama, sentence_transformers)
        config: Optional configuration

    Returns:
        Embedding model instance
    """
    return _embedding_manager.get_model(provider, config)
