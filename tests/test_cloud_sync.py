import pytest
from cloud_sync import CloudSync, InMemoryProvider, FilesystemProvider, encrypt, decrypt


def test_sync_conflict_local(tmp_path):
    provider = InMemoryProvider()
    local = tmp_path / "data.txt"
    local.write_text("local")
    provider.upload("data", encrypt(b"remote", "pw"))
    sync = CloudSync(provider, "pw", conflict_resolution="local")
    action = sync.sync_file(local, "data")
    assert action == "uploaded"
    stored = provider.download("data")
    assert decrypt(stored, "pw") == b"local"


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


def test_encryption_integrity_failure():
    data = encrypt(b"secret", "pw")
    tampered = bytearray(data)
    tampered[10] ^= 0xFF
    with pytest.raises(ValueError):
        decrypt(bytes(tampered), "pw")


def test_filesystem_provider_round_trip(tmp_path):
    provider_dir = tmp_path / "provider"
    fs_provider = FilesystemProvider(provider_dir)
    sync = CloudSync(fs_provider, "pw")

    local = tmp_path / "file.txt"
    local.write_text("hello")
    sync.backup_file(local, "file.txt")

    local.unlink()
    restored = sync.restore_file(local, "file.txt")
    assert restored is True
    assert local.read_text() == "hello"
