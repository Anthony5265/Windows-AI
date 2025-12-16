"""Pytest configuration and fixtures"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing"""
    return "test_api_key_12345"


@pytest.fixture
def mock_credentials():
    """Provide mock credentials dictionary"""
    return {
        "api_key": "test_key",
        "api_secret": "test_secret",
        "endpoint": "https://test.example.com"
    }


@pytest.fixture
def plugin_manager():
    """Create plugin manager instance for testing."""
    from windows_ai.core.plugin_manager import PluginManager
    return PluginManager()


@pytest.fixture
async def async_client():
    """Create an async HTTP client for testing FastAPI endpoints."""
    from windows_ai.api.server import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def assert_valid_response(response, expected_status=200):
    """Helper to validate API responses"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
    if expected_status == 200:
        assert response.json() is not None
    return response


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
