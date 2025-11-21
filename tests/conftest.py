"""Pytest configuration and fixtures"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
