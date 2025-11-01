import httpx

from search import SearchEngine, LocalBackend


def test_combines_local_and_remote(monkeypatch):
    """Search results merge local index with remote APIs."""

    # Fake remote API responses
    def fake_get(url, params=None, timeout=5.0):
        if "apps" in url:
            return httpx.Response(
                200, json={"results": ["Calculator"]}, request=httpx.Request("GET", url)
            )
        if "history" in url:
            return httpx.Response(
                200, json={"results": ["Opened file1"]}, request=httpx.Request("GET", url)
            )
        return httpx.Response(404, json={"results": []}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    engine = SearchEngine(
        LocalBackend(),
        remote_apis={
            "apps": "https://example.com/apps",
            "history": "https://example.com/history",
        },
    )
    engine.index({"file1": "open sesame"})

    results = engine.search("open")
    assert "file1" in results  # from local index
    assert "Calculator" in results  # from apps API
    assert "Opened file1" in results  # from history API


def test_local_index_only():
    engine = SearchEngine(LocalBackend())
    engine.index({"a": "hello world"})
    assert engine.search("hello") == ["a"]
