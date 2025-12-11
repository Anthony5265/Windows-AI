"""
Integration tests for Model Management API endpoints.

Tests cover all model-related endpoints:
- GET /models - List available models
- GET /models/{model_id} - Get model info
- POST /models/{model_id}/download - Download a model
- DELETE /models/{model_id} - Delete a model
"""

import pytest
from httpx import AsyncClient
from tests.conftest import assert_valid_response


# ============================================================================
# Tests: GET /models
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_models(async_client):
    """GET /models should return list of models."""
    response = await async_client.get("/models")

    assert_valid_response(response, 200)
    data = response.json()

    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_models_with_category_filter(async_client):
    """Should filter models by category."""
    response = await async_client.get("/models?category=premium")

    assert_valid_response(response, 200)
    data = response.json()

    # All returned models should be premium category
    for model in data["models"]:
        assert model["category"] == "premium"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_models_all_category(async_client):
    """Should return all models when category=all."""
    response = await async_client.get("/models?category=all")

    assert_valid_response(response, 200)
    data = response.json()
    
    # Should return all models
    assert len(data["models"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_models_structure(async_client):
    """Each model should have required fields."""
    response = await async_client.get("/models")

    assert_valid_response(response, 200)
    data = response.json()
    
    assert "models" in data
    assert "total" in data
    models = data["models"]

    for model in models:
        assert "id" in model
        assert "name" in model
        assert "provider" in model
        assert "category" in model
        assert "description" in model


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_models_returns_totals(async_client):
    """Should return total and installed counts."""
    response = await async_client.get("/models")

    assert_valid_response(response, 200)
    data = response.json()
    
    assert "total" in data
    assert "installed" in data
    assert "available" in data
    assert data["total"] == len(data["models"])


# ============================================================================
# Tests: GET /models/{model_id}
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_model_info_success(async_client):
    """Should return model information for valid model ID."""
    # First get list of models
    list_response = await async_client.get("/models")
    models = list_response.json()["models"]
    
    if models:
        model_id = models[0]["id"]
        response = await async_client.get(f"/models/{model_id}")

        assert_valid_response(response, 200)
        data = response.json()
        assert data["id"] == model_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_model_info_not_found(async_client):
    """Should return 404 for non-existent model."""
    response = await async_client.get("/models/nonexistent-model-xyz")

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_model_info_has_fields(async_client):
    """Model info should have standard fields."""
    response = await async_client.get("/models/gpt-4")

    assert_valid_response(response, 200)
    data = response.json()
    
    assert "id" in data
    assert "name" in data
    assert "provider" in data
    assert "description" in data
    assert "category" in data


# ============================================================================
# Tests: POST /models/{model_id}/download
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_model_success(async_client):
    """Should initiate model download for valid model."""
    # Use a valid model from the catalog
    response = await async_client.post("/models/gpt-4/download")

    assert_valid_response(response, 200)
    data = response.json()

    assert data["success"] is True
    assert "message" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_model_not_found(async_client):
    """Should return 404 for non-existent model."""
    response = await async_client.post("/models/nonexistent-model/download")

    assert response.status_code == 404


# ============================================================================
# Tests: DELETE /models/{model_id}
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_model_success(async_client):
    """Should successfully delete a model."""
    # Use a valid model
    response = await async_client.delete("/models/gpt-4")

    assert_valid_response(response, 200)
    data = response.json()
    
    assert data["success"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_model_not_found(async_client):
    """Should return 404 for non-existent model."""
    response = await async_client.delete("/models/nonexistent-model")

    assert response.status_code == 404


# ============================================================================
# Integration Workflows
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_model_workflow(async_client):
    """Test complete model workflow: list -> get info -> download -> delete."""
    # 1. List models
    list_resp = await async_client.get("/models")
    assert_valid_response(list_resp, 200)
    models = list_resp.json()["models"]
    assert len(models) > 0

    # 2. Get info for first model
    model_id = models[0]["id"]
    info_resp = await async_client.get(f"/models/{model_id}")
    assert_valid_response(info_resp, 200)
    
    # 3. Download model
    download_resp = await async_client.post(f"/models/{model_id}/download")
    assert_valid_response(download_resp, 200)
    
    # 4. Delete model
    delete_resp = await async_client.delete(f"/models/{model_id}")
    assert_valid_response(delete_resp, 200)


# ============================================================================
# Error Handling
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_malformed_model_id(async_client):
    """Should handle malformed model IDs gracefully."""
    # Empty path segment would result in 404 for different route
    response = await async_client.get("/models/invalid-model-xyz")
    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    """Should handle concurrent requests correctly."""
    import asyncio

    # Make 10 concurrent requests to list models
    tasks = [
        async_client.get("/models")
        for _ in range(10)
    ]

    responses = await asyncio.gather(*tasks)

    # All should succeed
    for response in responses:
        assert_valid_response(response, 200)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_returns_json_content_type(async_client):
    """All responses should have JSON content type."""
    response = await async_client.get("/models")

    assert "application/json" in response.headers.get("content-type", "")
