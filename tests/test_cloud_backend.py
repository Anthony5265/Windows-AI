import json

import httpx
import respx

from search.backends import CloudBackend


@respx.mock
def test_cloud_backend_remote_calls():
    endpoint = "https://api.example.com"
    backend = CloudBackend(endpoint)

    # Mock indexing endpoint
    index_route = respx.post(f"{endpoint}/index").mock(
        return_value=httpx.Response(200)
    )
    backend.index({"a": "hello"})
    assert index_route.called
    # Ensure the correct payload was sent
    sent = json.loads(index_route.calls[0].request.content.decode())
    assert sent == {"a": "hello"}

    # Mock search endpoint
    search_route = respx.get(f"{endpoint}/search").mock(
        return_value=httpx.Response(200, json={"results": ["a", "b"]})
    )
    results = backend.search("hello", top_k=2)
    assert search_route.called
    # Verify query parameters were passed through
    request = search_route.calls[0].request
    assert request.url.params["q"] == "hello"
    assert request.url.params["top_k"] == "2"
    assert results == ["a", "b"]


@respx.mock
def test_cloud_backend_fallback_on_error():
    endpoint = "https://api.example.com"
    backend = CloudBackend(endpoint)

    # Simulate network failure when indexing
    respx.post(f"{endpoint}/index").mock(side_effect=httpx.ReadTimeout("boom"))
    backend.index({"x": "foo", "y": "bar"})

    # Simulate network failure when searching; should fall back to local index
    respx.get(f"{endpoint}/search").mock(side_effect=httpx.ReadTimeout("boom"))
    assert backend.search("foo", top_k=5) == ["x", "y"]
