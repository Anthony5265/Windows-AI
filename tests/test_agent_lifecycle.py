import importlib

from fastapi.testclient import TestClient


def get_main():
    import apps.agenthub.main as main
    importlib.reload(main)
    return main


def test_registration_and_execution():
    main = get_main()
    client = TestClient(main.app)

    resp = client.post("/agents/demo?domain=nlp")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    resp = client.post("/agents/demo/train", json={"data": "hello"})
    assert resp.status_code == 200
    assert resp.json()["result"] == {"plan": []}

    resp = client.post("/agents/demo/run", json={"task": "hi"})
    assert resp.status_code == 200
    assert resp.json()["result"] == {"results": []}
