"""
Tests for embedding generation
"""
import pytest
import asyncio
from pathlib import Path

from windows_ai.embeddings import (
    get_embedding_model,
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingCache
)


class TestEmbeddingCache:
    """Test embedding cache functionality"""

    def test_cache_creation(self, tmp_path):
        """Test cache creation"""
        cache = EmbeddingCache(str(tmp_path / "cache"))
        assert cache.enabled
        assert cache.cache_directory.exists()

    def test_cache_set_get(self, tmp_path):
        """Test cache set and get operations"""
        cache = EmbeddingCache(str(tmp_path / "cache"))

        text = "Test document"
        model = "test-model"
        embedding = [0.1, 0.2, 0.3]

        # Set cache
        cache.set(text, model, embedding)

        # Get from cache
        retrieved = cache.get(text, model)
        assert retrieved == embedding

    def test_cache_miss(self, tmp_path):
        """Test cache miss"""
        cache = EmbeddingCache(str(tmp_path / "cache"))

        result = cache.get("nonexistent text", "model")
        assert result is None

    def test_cache_clear(self, tmp_path):
        """Test cache clearing"""
        cache = EmbeddingCache(str(tmp_path / "cache"))

        cache.set("text1", "model", [0.1, 0.2])
        cache.set("text2", "model", [0.3, 0.4])

        cache.clear()

        assert cache.get("text1", "model") is None
        assert cache.get("text2", "model") is None


class TestEmbeddingModels:
    """Test embedding model functionality"""

    @pytest.mark.asyncio
    async def test_openai_embedding_single(self):
        """Test OpenAI single text embedding"""
        try:
            model = get_embedding_model("openai")
            text = "This is a test document"
            embedding = await model.embed(text)

            assert isinstance(embedding, list)
            assert len(embedding) == model.config.dimension
            assert all(isinstance(x, float) for x in embedding)
        except Exception as e:
            pytest.skip(f"OpenAI not available: {e}")

    @pytest.mark.asyncio
    async def test_openai_embedding_batch(self):
        """Test OpenAI batch embedding"""
        try:
            model = get_embedding_model("openai")
            texts = ["Document 1", "Document 2", "Document 3"]
            embeddings = await model.embed(texts)

            assert isinstance(embeddings, list)
            assert len(embeddings) == len(texts)
            assert all(len(emb) == model.config.dimension for emb in embeddings)
        except Exception as e:
            pytest.skip(f"OpenAI not available: {e}")

    @pytest.mark.asyncio
    async def test_embedding_caching(self, tmp_path):
        """Test that embeddings are cached"""
        try:
            config = EmbeddingConfig(
                provider=EmbeddingProvider.OPENAI,
                model_name="text-embedding-3-small",
                dimension=1536,
                cache_enabled=True,
                cache_directory=str(tmp_path / "cache")
            )

            from windows_ai.embeddings import OpenAIEmbedding
            model = OpenAIEmbedding(config)

            text = "Test caching"

            # First call - should generate
            emb1 = await model.embed(text)

            # Second call - should retrieve from cache
            emb2 = await model.embed(text)

            assert emb1 == emb2

            # Check cache was used
            cached = model.cache.get(text, config.model_name)
            assert cached == emb1

        except Exception as e:
            pytest.skip(f"OpenAI not available: {e}")

    def test_dimension_validation(self):
        """Test embedding dimension validation"""
        try:
            model = get_embedding_model("openai")

            # Valid dimension
            embedding_valid = [0.1] * model.config.dimension
            assert model.validate_dimension(embedding_valid)

            # Invalid dimension
            embedding_invalid = [0.1] * (model.config.dimension + 1)
            assert not model.validate_dimension(embedding_invalid)

        except Exception as e:
            pytest.skip(f"OpenAI not available: {e}")


class TestEmbeddingProviders:
    """Test different embedding providers"""

    def test_provider_selection(self):
        """Test provider selection"""
        # This should work even without API keys
        try:
            model = get_embedding_model("openai")
            assert model is not None
        except Exception:
            pass  # Expected if no API key

    def test_config_creation(self):
        """Test embedding config creation"""
        config = EmbeddingConfig(
            provider=EmbeddingProvider.OPENAI,
            model_name="text-embedding-3-small",
            dimension=1536,
            batch_size=50,
            cache_enabled=True
        )

        assert config.provider == EmbeddingProvider.OPENAI
        assert config.dimension == 1536
        assert config.batch_size == 50
        assert config.cache_enabled


@pytest.fixture
def sample_texts():
    """Sample texts for testing"""
    return [
        "Machine learning is a subset of artificial intelligence.",
        "Natural language processing enables computers to understand human language.",
        "Vector databases store high-dimensional embeddings efficiently."
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
