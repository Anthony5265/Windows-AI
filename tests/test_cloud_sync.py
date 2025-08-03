import pytest
from cloud_sync import CloudSync, InMemoryProvider, encrypt


def test_sync_conflict_local(tmp_path):
    provider = InMemoryProvider()
    local = tmp_path / "data.txt"
    local.write_text("local")
    provider.upload("data", encrypt(b"remote", "pw"))
    sync = CloudSync(provider, "pw", conflict_resolution="local")
    action = sync.sync_file(local, "data")
    assert action == "uploaded"
    assert provider.download("data") == encrypt(b"local", "pw")


def test_sync_conflict_remote(tmp_path):
    provider = InMemoryProvider()
    local = tmp_path / "data.txt"
    local.write_text("local")
    provider.upload("data", encrypt(b"remote", "pw"))
    sync = CloudSync(provider, "pw", conflict_resolution="remote")
    action = sync.sync_file(local, "data")
    assert action == "downloaded"
    assert local.read_text() == "remote"


def test_sync_conflict_ask(tmp_path):
    provider = InMemoryProvider()
    local = tmp_path / "data.txt"
    local.write_text("local")
    provider.upload("data", encrypt(b"remote", "pw"))
    sync = CloudSync(provider, "pw", conflict_resolution="ask")
    with pytest.raises(RuntimeError):
        sync.sync_file(local, "data")
