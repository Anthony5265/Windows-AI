import importlib

import httpx
from fastapi.testclient import TestClient


def get_app(monkeypatch, actions_url=None, proxy_url=None):
    if actions_url is not None:
        monkeypatch.setenv("ACTIONS_URL", actions_url)
    else:
        monkeypatch.delenv("ACTIONS_URL", raising=False)
    if proxy_url is not None:
        monkeypatch.setenv("PROXY_URL", proxy_url)
    else:
        monkeypatch.delenv("PROXY_URL", raising=False)
    import apps.agenthub.main as main
    importlib.reload(main)
    return main


def test_custom_urls(monkeypatch):
    main = get_app(
        monkeypatch,
        actions_url="http://example.com/actions",
        proxy_url="http://example.com/proxy",
    )
    urls = []

    async def mock_post(self, url, *args, **kwargs):
        urls.append(url)
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    client = TestClient(main.app)
    resp = client.post("/pipeline/sample")
    assert resp.status_code == 200
    assert urls == ["http://example.com/actions", "http://example.com/proxy"]


def test_action_service_unreachable(monkeypatch):
    main = get_app(monkeypatch)

    async def mock_post(self, url, *args, **kwargs):
        raise httpx.RequestError("boom", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    client = TestClient(main.app)
    resp = client.post("/pipeline/sample")
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"].startswith("Action service unreachable")


def test_proxy_service_unreachable(monkeypatch):
    main = get_app(monkeypatch)

    async def mock_post(self, url, *args, **kwargs):
        if url == main.ACTIONS_URL:
            return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))
        raise httpx.RequestError("boom", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    client = TestClient(main.app)
    resp = client.post("/pipeline/sample")
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == {"ok": True}
    assert data["error"].startswith("Proxy service unreachable")


def test_action_service_http_error(monkeypatch):
    main = get_app(monkeypatch)

    async def mock_post(self, url, *args, **kwargs):
        if url == main.ACTIONS_URL:
            return httpx.Response(500, request=httpx.Request("POST", url))
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    client = TestClient(main.app)
    resp = client.post("/pipeline/sample")
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"].startswith("Action service error")


def test_proxy_service_http_error(monkeypatch):
    main = get_app(monkeypatch)

    async def mock_post(self, url, *args, **kwargs):
        if url == main.ACTIONS_URL:
            return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))
        return httpx.Response(502, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    client = TestClient(main.app)
    resp = client.post("/pipeline/sample")
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == {"ok": True}
    assert data["error"].startswith("Proxy service error")
