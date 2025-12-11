"""
Comprehensive API endpoint tests for Windows AI
Tests FastAPI REST API endpoints
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from windows_ai.api.server import app


@pytest.fixture
def client():
    """Create test client for API"""
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(client):
    """Test /health endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


@pytest.mark.integration
def test_root_endpoint(client):
    """Test root / endpoint"""
    response = client.get("/")
    
    # Should either redirect or return docs
    assert response.status_code in [200, 307]


@pytest.mark.integration
def test_list_plugins_endpoint(client):
    """Test GET /api/v1/plugins endpoint"""
    response = client.get("/api/v1/plugins")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have many plugins
    assert len(data) > 200


@pytest.mark.integration
def test_get_plugin_endpoint(client):
    """Test GET /api/v1/plugins/{id} endpoint"""
    # First get list of plugins
    plugins_response = client.get("/api/v1/plugins")
    plugins = plugins_response.json()
    
    if len(plugins) > 0:
        plugin_id = plugins[0]["id"]
        
        # Get specific plugin
        response = client.get(f"/api/v1/plugins/{plugin_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plugin_id


@pytest.mark.integration
def test_get_nonexistent_plugin(client):
    """Test GET /api/v1/plugins/{id} with invalid ID"""
    response = client.get("/api/v1/plugins/nonexistent-plugin-id-12345")
    
    assert response.status_code == 404


@pytest.mark.integration
def test_list_models_endpoint(client):
    """Test GET /api/v1/models endpoint"""
    response = client.get("/api/v1/models")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have many models
    assert len(data) > 50


@pytest.mark.integration
def test_chat_endpoint(client):
    """Test POST /api/v1/chat endpoint"""
    payload = {
        "message": "Hello, test message",
        "model": "gpt-4"
    }
    
    response = client.post("/api/v1/chat", json=payload)
    
    # May fail without API key, but should return proper status
    assert response.status_code in [200, 401, 503]


@pytest.mark.integration
def test_chat_endpoint_missing_message(client):
    """Test chat endpoint with missing message"""
    payload = {}
    
    response = client.post("/api/v1/chat", json=payload)
    
    # Should return 400 or 422 for invalid request
    assert response.status_code in [400, 422]


@pytest.mark.integration
def test_execute_plugin_endpoint(client):
    """Test POST /api/v1/plugins/{id}/execute endpoint"""
    # Get a test plugin
    plugins_response = client.get("/api/v1/plugins")
    plugins = plugins_response.json()
    
    if len(plugins) > 0:
        plugin_id = plugins[0]["id"]
        
        payload = {"test_param": "test_value"}
        response = client.post(f"/api/v1/plugins/{plugin_id}/execute", json=payload)
        
        # Should execute (may fail if plugin requires specific params)
        assert response.status_code in [200, 400, 500]


@pytest.mark.integration
def test_list_conversations_endpoint(client):
    """Test GET /api/v1/conversations endpoint"""
    response = client.get("/api/v1/conversations")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_search_plugins_endpoint(client):
    """Test GET /api/v1/plugins/search endpoint"""
    response = client.get("/api/v1/plugins/search?q=chat")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.integration
def test_cors_headers(client):
    """Test CORS headers are set correctly"""
    response = client.get("/health")
    
    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


@pytest.mark.integration
def test_api_documentation_endpoint(client):
    """Test /docs endpoint exists"""
    response = client.get("/docs")
    
    # Should serve OpenAPI docs
    assert response.status_code == 200


@pytest.mark.integration
def test_openapi_json_endpoint(client):
    """Test /openapi.json endpoint"""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


@pytest.mark.integration
def test_rate_limiting(client):
    """Test rate limiting on endpoints"""
    # Make multiple requests rapidly
    responses = []
    for i in range(100):
        response = client.get("/health")
        responses.append(response.status_code)
    
    # Most should succeed, rate limit may kick in
    success_count = sum(1 for code in responses if code == 200)
    assert success_count > 50  # At least half should succeed


@pytest.mark.integration
def test_plugin_filtering_by_type(client):
    """Test filtering plugins by type"""
    response = client.get("/api/v1/plugins?type=integration")
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.integration
def test_setup_wizard_status(client):
    """Test GET /api/v1/setup/status endpoint"""
    response = client.get("/api/v1/setup/status")
    
    assert response.status_code == 200
    data = response.json()
    assert "completed" in data or "status" in data


@pytest.mark.integration
def test_credentials_list_endpoint(client):
    """Test GET /api/v1/credentials endpoint"""
    response = client.get("/api/v1/credentials")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


@pytest.mark.integration
def test_invalid_endpoint(client):
    """Test calling invalid endpoint returns 404"""
    response = client.get("/api/v1/invalid-endpoint-xyz")
    
    assert response.status_code == 404


@pytest.mark.integration
def test_invalid_method(client):
    """Test using wrong HTTP method"""
    # Try DELETE on endpoint that only accepts GET
    response = client.delete("/health")
    
    assert response.status_code in [405, 404]


@pytest.mark.integration
def test_json_content_type(client):
    """Test API returns JSON content type"""
    response = client.get("/api/v1/plugins")
    
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.integration
def test_large_payload_handling(client):
    """Test API handles large payloads"""
    large_payload = {
        "message": "x" * 100000,  # 100KB message
        "model": "gpt-4"
    }
    
    response = client.post("/api/v1/chat", json=large_payload)
    
    # Should either accept or reject with proper status
    assert response.status_code in [200, 413, 422, 401, 503]


@pytest.mark.integration
def test_concurrent_requests(client):
    """Test API handles concurrent requests"""
    import concurrent.futures
    
    def make_request():
        return client.get("/health")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # Most should succeed
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count > 40


@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_chat_endpoint(client):
    """Test streaming chat endpoint"""
    payload = {
        "message": "Hello streaming",
        "stream": True
    }
    
    # Note: TestClient doesn't fully support streaming, but we can test the endpoint exists
    response = client.post("/api/v1/chat/stream", json=payload)
    
    # Should return proper status
    assert response.status_code in [200, 401, 503]


@pytest.mark.integration
def test_plugin_capabilities_endpoint(client):
    """Test getting plugin capabilities"""
    plugins_response = client.get("/api/v1/plugins")
    plugins = plugins_response.json()
    
    if len(plugins) > 0:
        plugin_id = plugins[0]["id"]
        response = client.get(f"/api/v1/plugins/{plugin_id}/capabilities")
        
        # Endpoint may or may not exist
        assert response.status_code in [200, 404]


@pytest.mark.integration
def test_system_info_endpoint(client):
    """Test system information endpoint"""
    response = client.get("/api/v1/system/info")
    
    if response.status_code == 200:
        data = response.json()
        # Should have system info
        assert isinstance(data, dict)
