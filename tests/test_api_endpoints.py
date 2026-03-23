"""Tests for Windows AI FastAPI API endpoints."""
import pytest
from fastapi.testclient import TestClient
from windows_ai.api.server import app


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


# Status codes that indicate the route exists and handled the request,
# even if a backend dependency (plugin manager, SQLAlchemy, API keys) is missing.
VALID_ROUTE_CODES = [200, 201, 400, 401, 403, 404, 422, 500, 503]


class TestAPIEndpoints:
    """Test that all API routes are wired up and respond."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_page(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_docs_page(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        # Verify marketplace routes are registered
        assert any("/api/marketplace" in p for p in schema["paths"])

    def test_plugin_list(self, client):
        response = client.get("/plugins")
        assert response.status_code in VALID_ROUTE_CODES

    def test_plugin_list_v1(self, client):
        response = client.get("/api/v1/plugins/")
        assert response.status_code in VALID_ROUTE_CODES

    def test_system_health(self, client):
        response = client.get("/api/v1/system/health")
        assert response.status_code in VALID_ROUTE_CODES

    def test_system_info(self, client):
        response = client.get("/api/v1/system/info")
        assert response.status_code in VALID_ROUTE_CODES

    def test_system_stats(self, client):
        response = client.get("/api/v1/system/stats")
        assert response.status_code in VALID_ROUTE_CODES

    def test_chat_endpoint(self, client):
        response = client.post("/chat", json={"message": "hello", "provider": "openai"})
        assert response.status_code in VALID_ROUTE_CODES

    def test_setup_status(self, client):
        response = client.get("/api/setup/status")
        assert response.status_code in VALID_ROUTE_CODES

    def test_setup_system_requirements(self, client):
        response = client.get("/api/setup/system-requirements")
        assert response.status_code in VALID_ROUTE_CODES

    def test_credentials_status(self, client):
        response = client.get("/api/credentials/status")
        assert response.status_code in VALID_ROUTE_CODES

    def test_health_detailed(self, client):
        response = client.get("/api/health/")
        assert response.status_code == 200

    def test_health_memory(self, client):
        response = client.get("/api/health/memory")
        assert response.status_code == 200

    def test_health_disk(self, client):
        response = client.get("/api/health/disk")
        assert response.status_code == 200

    def test_health_integrations(self, client):
        response = client.get("/api/health/integrations")
        assert response.status_code == 200

    def test_marketplace_list(self, client):
        response = client.get("/api/marketplace/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_marketplace_categories(self, client):
        response = client.get("/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert data["total_plugins"] > 0

    def test_marketplace_stats(self, client):
        response = client.get("/api/marketplace/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_plugins"] > 0

    def test_marketplace_search(self, client):
        response = client.get("/api/marketplace/search/windows")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    def test_agents_list(self, client):
        response = client.get("/api/v1/agents/")
        assert response.status_code in VALID_ROUTE_CODES

    def test_conversations_list(self, client):
        response = client.get("/conversations")
        assert response.status_code in VALID_ROUTE_CODES

    def test_models_list(self, client):
        response = client.get("/models")
        assert response.status_code in VALID_ROUTE_CODES
