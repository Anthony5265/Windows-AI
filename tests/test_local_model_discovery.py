"""Tests for local model discovery module."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

from windows_ai.integrations.local_model_discovery import (
    LocalModelDiscovery,
    LocalModel,
)


class TestLocalModelDiscovery:
    """Test local model discovery functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Discovery initializes correctly."""
        discovery = LocalModelDiscovery()
        assert not discovery._initialized
        await discovery.initialize()
        assert discovery._initialized

    @pytest.mark.asyncio
    async def test_list_models_empty(self):
        """List models returns list when no providers available."""
        discovery = LocalModelDiscovery()
        await discovery.initialize()
        models = discovery.list_models()
        assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_list_providers(self):
        """List providers returns dict of provider availability."""
        discovery = LocalModelDiscovery()
        await discovery.initialize()
        providers = discovery.list_providers()
        assert isinstance(providers, dict)
        # Should have checked these providers
        expected_providers = {"ollama", "lm_studio", "text_generation_webui", "vllm", "llama_cpp"}
        assert set(providers.keys()).issubset(expected_providers)

    @pytest.mark.asyncio
    async def test_get_model_not_found(self):
        """Get model returns None for unknown model."""
        discovery = LocalModelDiscovery()
        await discovery.initialize()
        result = discovery.get_model("nonexistent_model")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_models_by_provider(self):
        """Get models by provider returns list."""
        discovery = LocalModelDiscovery()
        await discovery.initialize()
        models = discovery.get_models_by_provider("ollama")
        assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_ollama_discovery_with_mock(self):
        """Ollama discovery parses output correctly."""
        discovery = LocalModelDiscovery()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(
                b"NAME              ID          SIZE    MODIFIED\n"
                b"llama3:latest     abc123      4.7 GB  2 days ago\n"
                b"codellama:7b      def456      3.8 GB  1 week ago\n",
                b"",
            )
        )

        with patch("shutil.which", return_value="/usr/bin/ollama"):
            with patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ):
                models = await discovery._discover_ollama()

        assert len(models) == 2
        assert models[0].name == "llama3:latest"
        assert models[0].provider == "ollama"
        assert models[1].name == "codellama:7b"

    @pytest.mark.asyncio
    async def test_ollama_not_installed(self):
        """Returns empty when ollama is not installed."""
        discovery = LocalModelDiscovery()

        with patch("shutil.which", return_value=None):
            models = await discovery._discover_ollama()

        assert models == []
        assert discovery._providers.get("ollama") is False

    @pytest.mark.asyncio
    async def test_lm_studio_discovery_with_mock(self):
        """LM Studio discovery scans model files."""
        discovery = LocalModelDiscovery()

        with patch("pathlib.Path.exists", return_value=False):
            models = await discovery._discover_lm_studio()
            assert models == []

    def test_local_model_to_dict(self):
        """LocalModel serializes to dict correctly."""
        model = LocalModel(
            name="test-model",
            provider="ollama",
            size="4.7 GB",
            endpoint="http://localhost:11434",
        )
        d = model.to_dict()
        assert d["name"] == "test-model"
        assert d["provider"] == "ollama"
        assert d["size"] == "4.7 GB"
        assert d["endpoint"] == "http://localhost:11434"
        assert d["running"] is False

    @pytest.mark.asyncio
    async def test_discover_all_handles_errors(self):
        """discover_all gracefully handles provider errors."""
        discovery = LocalModelDiscovery()

        # Make one provider raise an exception
        with patch.object(
            discovery, "_discover_ollama", side_effect=Exception("Connection refused")
        ):
            models = await discovery.discover_all()
            # Should not raise, just log and continue
            assert isinstance(models, list)
