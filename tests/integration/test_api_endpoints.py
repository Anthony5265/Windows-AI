"""
Integration Tests for API Endpoints
Tests all major API routes

Note: Routes are at different prefixes:
- /health - root level health check
- /plugins, /models - frontend routes (root level)
- /chat, /conversations - chat routes (root level)
- /api/v1/plugins - plugin management API (requires initialization)
"""

import pytest
from fastapi.testclient import TestClient
from windows_ai.api.server import app

client = TestClient(app)

@pytest.mark.integration
def test_health_endpoint():
    """Test /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "ok"]  # Accept both

@pytest.mark.integration
def test_list_plugins_endpoint():
    """Test /plugins endpoint (frontend route)"""
    response = client.get("/plugins")
    assert response.status_code == 200
    data = response.json()
    # Response is dict with 'plugins' key
    assert isinstance(data, dict)
    assert "plugins" in data
    assert isinstance(data["plugins"], list)

@pytest.mark.integration
def test_list_models_endpoint():
    """Test /models endpoint (frontend route)"""
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    # Response is dict with 'models' key
    assert isinstance(data, dict)
    assert "models" in data
    assert isinstance(data["models"], list)

@pytest.mark.integration
def test_chat_endpoint_without_message():
    """Test /chat endpoint with invalid input"""
    response = client.post("/chat", json={})
    assert response.status_code == 422  # Validation error (missing 'message' field)

@pytest.mark.integration
def test_plugin_details_endpoint():
    """Test /plugins/{id} endpoint"""
    # First get plugins list
    plugins_response = client.get("/plugins")
    if plugins_response.status_code == 200:
        data = plugins_response.json()
        plugins = data.get("plugins", [])
        
        if isinstance(plugins, list) and len(plugins) > 0:
            plugin_id = plugins[0]["id"]
            response = client.get(f"/plugins/{plugin_id}")
            assert response.status_code == 200

@pytest.mark.integration
def test_conversations_endpoint():
    """Test /conversations endpoint"""
    response = client.get("/conversations")
    assert response.status_code == 200
    data = response.json()
    # Response is dict with 'conversations' key
    assert isinstance(data, dict)
    assert "conversations" in data
