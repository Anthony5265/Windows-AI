import pytest
import requests

from search.backends import CloudBackend


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")

    def json(self):
        return self._data


def test_cloud_backend_index_and_search(monkeypatch):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append((url, json))
        if url.endswith("/search"):
            return DummyResponse({"results": ["a", "b"]})
        return DummyResponse({})

    monkeypatch.setattr(requests, "post", fake_post)

    backend = CloudBackend("http://api.test")
    backend.index({"a": "foo"})
    results = backend.search("bar", top_k=2)

    assert calls[0][0] == "http://api.test/index"
    assert calls[0][1] == {"a": "foo"}
    assert results == ["a", "b"]


def test_cloud_backend_timeout(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise requests.Timeout("boom")

    monkeypatch.setattr(requests, "post", fake_post)

    backend = CloudBackend("http://api.test")
    with pytest.raises(TimeoutError):
        backend.search("baz")
