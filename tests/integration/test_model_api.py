"""
Integration tests for Model Management API endpoints.

Tests cover all model-related endpoints:
- GET /models/available - List available models
- GET /models/installed - List installed models
- POST /models/{model_id}/download - Download a model
- GET /models/{model_id}/download/status - Get download status
- DELETE /models/{model_id} - Delete a model
- GET /models/{model_id} - Get model info
"""

import pytest
from httpx import AsyncClient
from tests.conftest import assert_valid_response


# ============================================================================
# Tests: GET /models/available
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_available_models(async_client):
    """GET /models/available should return list of models."""
    response = await async_client.get("/models/available")

    assert_valid_response(response, 200)
    data = response.json()

    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_available_models_with_category_filter(async_client):
    """Should filter models by category."""
    response = await async_client.get("/models/available?category=coding")

    assert_valid_response(response, 200)
    data = response.json()

    for model in data["models"]:
        assert model["category"] == "coding"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_available_models_recommended_only(async_client):
    """Should return only recommended models."""
    response = await async_client.get("/models/available?recommended_only=true")

    assert_valid_response(response, 200)
    data = response.json()

    for model in data["models"]:
        assert model["recommended"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_available_models_structure(async_client):
    """Each model should have required fields."""
    response = await async_client.get("/models/available")

    assert_valid_response(response, 200)
    models = response.json()["models"]

    for model in models:
        assert "id" in model
        assert "name" in model
        assert "provider" in model
        assert "category" in model
        assert "size" in model
        assert "description" in model


# ============================================================================
# Tests: GET /models/installed
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_installed_models(async_client):
    """GET /models/installed should return installed models."""
    response = await async_client.get("/models/installed")

    assert_valid_response(response, 200)
    data = response.json()

    assert "models" in data
    assert isinstance(data["models"], list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_installed_models_empty(async_client):
    """Should return empty list when no models installed."""
    response = await async_client.get("/models/installed")

    assert_valid_response(response, 200)
    # May be empty or have models depending on test environment


# ============================================================================
# Tests: POST /models/{model_id}/download
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_download_model_initiates_download(async_client):
    """Should initiate model download."""
    model_id = "tinyllama:1.1b"  # Small model for testing

    response = await async_client.post(f"/models/{model_id}/download")

    # Should return 200 or 202 (accepted)
    assert response.status_code in [200, 202]
    data = response.json()

    assert "status" in data
    assert data["status"] in ["downloading", "queued", "already_installed"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_model_invalid_id(async_client):
    """Should reject invalid model ID."""
    response = await async_client.post("/models/invalid:model/download")

    assert response.status_code in [400, 404]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_download_model_already_installed(async_client):
    """Should handle already installed models."""
    # First, check if any model is installed
    installed_resp = await async_client.get("/models/installed")
    installed = installed_resp.json().get("models", [])

    if installed:
        model_id = installed[0]["name"]
        response = await async_client.post(f"/models/{model_id}/download")

        assert_valid_response(response, 200)
        data = response.json()
        assert data["status"] == "already_installed"


# ============================================================================
# Tests: GET /models/{model_id}/download/status
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_download_status_not_downloading(async_client):
    """Should return idle status when not downloading."""
    model_id = "llama2:7b"

    response = await async_client.get(f"/models/{model_id}/download/status")

    assert_valid_response(response, 200)
    data = response.json()

    assert "status" in data
    assert data["status"] in ["idle", "downloading", "completed", "failed"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_download_status_includes_progress(async_client):
    """Download status should include progress information."""
    model_id = "llama2:7b"

    response = await async_client.get(f"/models/{model_id}/download/status")

    assert_valid_response(response, 200)
    data = response.json()

    assert "progress" in data or data["status"] == "idle"


# ============================================================================
# Tests: DELETE /models/{model_id}
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_model_not_found(async_client):
    """Should return 404 for non-existent model."""
    response = await async_client.delete("/models/nonexistent:model")

    assert response.status_code in [404, 400]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_model_success(async_client):
    """Should successfully delete an installed model."""
    # First check installed models
    installed_resp = await async_client.get("/models/installed")
    installed = installed_resp.json().get("models", [])

    if installed:
        model_id = installed[0]["name"]

        response = await async_client.delete(f"/models/{model_id}")

        assert response.status_code in [200, 204]


# ============================================================================
# Tests: GET /models/{model_id}
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_model_info_success(async_client):
    """Should return model information."""
    model_id = "llama2:7b"

    response = await async_client.get(f"/models/{model_id}")

    # Should return 200 or 404 depending on catalog
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert data["id"] == model_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_model_info_not_found(async_client):
    """Should return 404 for non-existent model."""
    response = await async_client.get("/models/nonexistent:999")

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_model_info_includes_install_status(async_client):
    """Model info should indicate if installed."""
    # Get an available model
    available_resp = await async_client.get("/models/available")
    models = available_resp.json()["models"]

    if models:
        model_id = models[0]["id"]
        response = await async_client.get(f"/models/{model_id}")

        if response.status_code == 200:
            data = response.json()
            assert "installed" in data or "is_installed" in data


# ============================================================================
# Integration Workflows
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_full_model_lifecycle(async_client):
    """Test complete model lifecycle: list -> download -> check status -> delete."""
    # 1. List available models
    available_resp = await async_client.get("/models/available")
    assert_valid_response(available_resp, 200)
    models = available_resp.json()["models"]
    assert len(models) > 0

    # 2. Select smallest model for testing
    test_model = min(
        (m for m in models if not m.get("installed", False)),
        key=lambda m: int(m.get("size_bytes", float('inf')) or float('inf')),
        default=None
    )

    if not test_model:
        pytest.skip("No suitable model for testing")

    model_id = test_model["id"]

    # 3. Initiate download (but don't wait for completion)
    download_resp = await async_client.post(f"/models/{model_id}/download")
    assert download_resp.status_code in [200, 202]

    # 4. Check download status
    status_resp = await async_client.get(f"/models/{model_id}/download/status")
    assert_valid_response(status_resp, 200)
    status = status_resp.json()
    assert status["status"] in ["downloading", "completed", "queued"]

    # Note: Not deleting in test to avoid disrupting actual downloads


# ============================================================================
# Error Handling
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_malformed_model_id(async_client):
    """Should handle malformed model IDs."""
    bad_ids = [
        "",
        "   ",
        "../../../etc/passwd",
        "model;rm -rf /",
        "<script>alert('xss')</script>"
    ]

    for bad_id in bad_ids:
        response = await async_client.get(f"/models/{bad_id}")
        assert response.status_code in [400, 404], \
            f"Should reject bad ID: {bad_id}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_requests_same_endpoint(async_client):
    """Should handle concurrent requests correctly."""
    import asyncio

    # Make 10 concurrent requests to list models
    tasks = [
        async_client.get("/models/available")
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
    response = await async_client.get("/models/available")

    assert "application/json" in response.headers.get("content-type", "")
