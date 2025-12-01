"""
API Testing Helpers
Utilities for testing FastAPI endpoints
"""

from typing import Dict, Any, Optional
from fastapi.testclient import TestClient
import httpx


def create_test_client(app):
    """Create a test client for FastAPI app"""
    return TestClient(app)


async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs
) -> httpx.Response:
    """Make an async HTTP request"""
    method = method.upper()

    if method == "GET":
        return await client.get(url, **kwargs)
    elif method == "POST":
        return await client.post(url, **kwargs)
    elif method == "PUT":
        return await client.put(url, **kwargs)
    elif method == "DELETE":
        return await client.delete(url, **kwargs)
    elif method == "PATCH":
        return await client.patch(url, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


def assert_response_ok(response: httpx.Response, expected_status: int = 200):
    """Assert that response is successful"""
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}. Body: {response.text}"


def assert_response_json(response: httpx.Response, expected_keys: list):
    """Assert response contains expected JSON keys"""
    assert response.headers.get("content-type") == "application/json"
    data = response.json()

    for key in expected_keys:
        assert key in data, f"Expected key '{key}' not found in response: {data}"


def assert_error_response(
    response: httpx.Response,
    expected_status: int,
    expected_error: Optional[str] = None
):
    """Assert that response is an error with expected status"""
    assert response.status_code == expected_status

    if expected_error:
        data = response.json()
        assert "error" in data or "detail" in data
        error_msg = data.get("error") or data.get("detail")
        assert expected_error in str(error_msg)
