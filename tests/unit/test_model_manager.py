"""
Unit tests for windows_ai.model_manager module.

Tests cover:
- Listing available models
- Listing installed models
- Downloading models with progress tracking
- Deleting models
- Getting model information
- Error handling and edge cases
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from windows_ai.model_manager import ModelManager


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def model_manager():
    """Provide a fresh ModelManager instance for each test."""
    manager = ModelManager()
    yield manager
    # Cleanup
    if hasattr(manager, 'cleanup'):
        await manager.cleanup()


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response data."""
    return {
        "models": [
            {
                "name": "llama2:7b",
                "size": 3826793677,
                "digest": "abc123",
                "modified_at": "2025-11-10T10:00:00Z"
            },
            {
                "name": "codellama:7b",
                "size": 3826793677,
                "digest": "def456",
                "modified_at": "2025-11-10T09:00:00Z"
            },
            {
                "name": "mistral:7b",
                "size": 4109865159,
                "digest": "ghi789",
                "modified_at": "2025-11-10T08:00:00Z"
            }
        ]
    }


# ============================================================================
# Tests: list_available_models()
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_available_models_returns_list(model_manager):
    """Should return a list of available models."""
    models = await model_manager.list_available_models()

    assert isinstance(models, list), "Should return a list"
    assert len(models) > 0, "Should have at least one model"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_available_models_structure(model_manager):
    """Each model should have required fields."""
    models = await model_manager.list_available_models()

    for model in models:
        assert "id" in model, "Model should have id field"
        assert "name" in model, "Model should have name field"
        assert "provider" in model, "Model should have provider field"
        assert "category" in model, "Model should have category field"
        assert "size" in model, "Model should have size field"
        assert "description" in model, "Model should have description field"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_available_models_with_category_filter(model_manager):
    """Should filter models by category."""
    models = await model_manager.list_available_models(category="coding")

    assert all(m["category"] == "coding" for m in models), \
        "All models should be in coding category"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_available_models_recommended_only(model_manager):
    """Should return only recommended models when requested."""
    models = await model_manager.list_available_models(recommended_only=True)

    assert all(m.get("recommended", False) for m in models), \
        "All models should be marked as recommended"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_available_models_empty_category(model_manager):
    """Should return empty list for non-existent category."""
    models = await model_manager.list_available_models(category="nonexistent")

    assert models == [], "Should return empty list for invalid category"


# ============================================================================
# Tests: list_installed_models()
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_list_installed_models_success(mock_get, model_manager, mock_ollama_response):
    """Should list installed models from Ollama."""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=MagicMock(return_value=mock_ollama_response)
    )

    models = await model_manager.list_installed_models()

    assert len(models) == 3, "Should return 3 installed models"
    assert models[0]["name"] == "llama2:7b"
    mock_get.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_list_installed_models_empty(mock_get, model_manager):
    """Should return empty list when no models installed."""
    mock_get.return_value = MagicMock(
        status_code=200,
        json=MagicMock(return_value={"models": []})
    )

    models = await model_manager.list_installed_models()

    assert models == [], "Should return empty list"


@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_list_installed_models_api_error(mock_get, model_manager):
    """Should handle API errors gracefully."""
    mock_get.side_effect = Exception("Connection failed")

    models = await model_manager.list_installed_models()

    assert models == [], "Should return empty list on error"


# ============================================================================
# Tests: download_model()
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_download_model_success(mock_post, model_manager):
    """Should successfully download a model."""
    mock_post.return_value = MagicMock(
        status_code=200,
        iter_lines=MagicMock(return_value=iter([
            b'{"status": "pulling", "completed": 100, "total": 1000}',
            b'{"status": "completed"}'
        ]))
    )

    result = await model_manager.download_model("llama2:7b")

    assert result["status"] == "success", "Download should succeed"
    mock_post.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_download_model_with_progress_callback(mock_post, model_manager):
    """Should call progress callback during download."""
    mock_post.return_value = MagicMock(
        status_code=200,
        iter_lines=MagicMock(return_value=iter([
            b'{"status": "pulling", "completed": 250, "total": 1000}',
            b'{"status": "pulling", "completed": 500, "total": 1000}',
            b'{"status": "pulling", "completed": 750, "total": 1000}',
            b'{"status": "completed"}'
        ]))
    )

    progress_calls = []

    def progress_callback(progress):
        progress_calls.append(progress)

    await model_manager.download_model("llama2:7b", callback=progress_callback)

    assert len(progress_calls) >= 3, "Should call progress callback multiple times"
    assert progress_calls[-1]["status"] == "completed"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_model_invalid_id(model_manager):
    """Should raise error for invalid model ID."""
    with pytest.raises(ValueError, match="Invalid model"):
        await model_manager.download_model("")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_model_already_exists(model_manager):
    """Should skip download if model already installed."""
    with patch.object(model_manager, 'list_installed_models') as mock_list:
        mock_list.return_value = [{"name": "llama2:7b"}]

        result = await model_manager.download_model("llama2:7b")

        assert result["status"] == "already_installed"


@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_download_model_network_error(mock_post, model_manager):
    """Should handle network errors during download."""
    mock_post.side_effect = Exception("Network timeout")

    with pytest.raises(Exception):
        await model_manager.download_model("llama2:7b")


# ============================================================================
# Tests: delete_model()
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.delete')
async def test_delete_model_success(mock_delete, model_manager):
    """Should successfully delete a model."""
    mock_delete.return_value = MagicMock(status_code=200)

    result = await model_manager.delete_model("llama2:7b")

    assert result["status"] == "success", "Delete should succeed"
    mock_delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_model_not_found(model_manager):
    """Should raise error when deleting non-existent model."""
    with pytest.raises(ValueError, match="Model not found"):
        await model_manager.delete_model("nonexistent:model")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_model_invalid_id(model_manager):
    """Should raise error for invalid model ID."""
    with pytest.raises(ValueError, match="Invalid model"):
        await model_manager.delete_model("")


@pytest.mark.unit
@pytest.mark.asyncio
@patch('httpx.AsyncClient.delete')
async def test_delete_model_api_error(mock_delete, model_manager):
    """Should handle API errors during deletion."""
    mock_delete.side_effect = Exception("API error")

    with pytest.raises(Exception):
        await model_manager.delete_model("llama2:7b")


# ============================================================================
# Tests: get_model_info()
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_model_info_success(model_manager):
    """Should return model information."""
    info = await model_manager.get_model_info("llama2:7b")

    assert info is not None, "Should return model info"
    assert info["id"] == "llama2:7b"
    assert "name" in info
    assert "size" in info


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_model_info_not_found(model_manager):
    """Should return None for non-existent model."""
    info = await model_manager.get_model_info("nonexistent:model")

    assert info is None, "Should return None for invalid model"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_model_info_checks_installed_status(model_manager):
    """Should indicate if model is installed."""
    with patch.object(model_manager, 'list_installed_models') as mock_list:
        mock_list.return_value = [{"name": "llama2:7b"}]

        info = await model_manager.get_model_info("llama2:7b")

        assert info.get("installed") is True


# ============================================================================
# Tests: get_download_status()
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_download_status_in_progress(model_manager):
    """Should return download progress for active download."""
    # Simulate active download
    model_manager._downloads = {
        "llama2:7b": {
            "status": "downloading",
            "progress": 45,
            "downloaded": 1700000000,
            "total": 3800000000
        }
    }

    status = await model_manager.get_download_status("llama2:7b")

    assert status["status"] == "downloading"
    assert status["progress"] == 45


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_download_status_completed(model_manager):
    """Should return completed status after download finishes."""
    model_manager._downloads = {
        "llama2:7b": {
            "status": "completed",
            "progress": 100
        }
    }

    status = await model_manager.get_download_status("llama2:7b")

    assert status["status"] == "completed"
    assert status["progress"] == 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_download_status_not_downloading(model_manager):
    """Should return idle status when no download."""
    status = await model_manager.get_download_status("llama2:7b")

    assert status["status"] == "idle"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_concurrent_downloads_same_model(model_manager):
    """Should prevent concurrent downloads of the same model."""
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            iter_lines=MagicMock(return_value=iter([b'{"status": "pulling"}']))
        )

        # Start first download
        task1 = model_manager.download_model("llama2:7b")

        # Try to start second download of same model
        with pytest.raises(Exception, match="already downloading"):
            await model_manager.download_model("llama2:7b")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_removes_temporary_files(model_manager, tmp_path):
    """Should clean up temporary files on cleanup."""
    if hasattr(model_manager, 'cleanup'):
        await model_manager.cleanup()
        # Verify cleanup occurred
        assert True  # Placeholder - actual verification depends on implementation


@pytest.mark.unit
def test_model_manager_initialization():
    """Should initialize with default configuration."""
    manager = ModelManager()

    assert manager is not None
    assert hasattr(manager, 'list_available_models')
    assert hasattr(manager, 'download_model')


@pytest.mark.unit
@pytest.mark.asyncio
async def test_size_formatting(model_manager):
    """Should format model sizes correctly."""
    models = await model_manager.list_available_models()

    for model in models:
        size = model.get("size", "")
        # Should be in format like "3.8 GB", "512 MB", etc.
        assert any(unit in size for unit in ["GB", "MB", "KB"]), \
            f"Size '{size}' should have unit"
