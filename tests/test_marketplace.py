"""Tests for plugin marketplace API endpoints."""
import pytest
from fastapi.testclient import TestClient
from windows_ai.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


class TestMarketplaceAPI:
    """Test plugin marketplace endpoints."""

    def test_list_plugins(self, client):
        """GET /api/marketplace/ returns plugin list."""
        response = client.get("/api/marketplace/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_plugins_pagination(self, client):
        """Pagination works correctly."""
        response = client.get("/api/marketplace/?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_list_plugins_category_filter(self, client):
        """Category filter works."""
        response = client.get("/api/marketplace/?category=windows")
        assert response.status_code == 200
        data = response.json()
        for plugin in data:
            assert plugin["category"] == "windows"

    def test_list_plugins_search(self, client):
        """Search filter works."""
        response = client.get("/api/marketplace/?search=plugin")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_categories(self, client):
        """GET /api/marketplace/categories returns category list."""
        response = client.get("/api/marketplace/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "total_categories" in data
        assert "total_plugins" in data
        assert data["total_categories"] > 0
        assert data["total_plugins"] > 0

    def test_stats(self, client):
        """GET /api/marketplace/stats returns stats."""
        response = client.get("/api/marketplace/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_plugins" in data
        assert "total_categories" in data
        assert data["total_plugins"] > 0

    def test_search_plugins(self, client):
        """GET /api/marketplace/search/{query} returns results."""
        response = client.get("/api/marketplace/search/windows")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "total" in data
        assert "results" in data
        assert data["total"] > 0

    def test_install_plugin(self, client):
        """POST /api/marketplace/install installs plugin."""
        # First get a plugin ID
        list_response = client.get("/api/marketplace/?per_page=1")
        plugins = list_response.json()
        assert len(plugins) > 0

        plugin_id = plugins[0]["id"]
        response = client.post(
            "/api/marketplace/install",
            json={"plugin_id": plugin_id},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["plugin_id"] == plugin_id

    def test_install_nonexistent_plugin(self, client):
        """Installing nonexistent plugin returns 404."""
        response = client.post(
            "/api/marketplace/install",
            json={"plugin_id": "nonexistent/plugin"},
        )
        assert response.status_code == 404

    def test_get_plugin_details(self, client):
        """GET /api/marketplace/{id} returns plugin details."""
        list_response = client.get("/api/marketplace/?per_page=1")
        plugins = list_response.json()
        assert len(plugins) > 0

        plugin_id = plugins[0]["id"]
        response = client.get(f"/api/marketplace/{plugin_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plugin_id
        assert "name" in data
        assert "description" in data

    def test_get_nonexistent_plugin(self, client):
        """GET /api/marketplace/{id} returns 404 for unknown plugin."""
        response = client.get("/api/marketplace/nonexistent/plugin")
        assert response.status_code == 404
