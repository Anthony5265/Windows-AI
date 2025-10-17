import pytest
from cloud_sync import (
    CloudSync,
    InMemoryProvider,
    FilesystemProvider,
    encrypt,
    decrypt,
)


def test_sync_conflict_local(tmp_path):
    provider = InMemoryProvider()
    local = tmp_path / "data.txt"
    local.write_text("local")
    provider.upload("data", encrypt(b"remote", "pw"))
    sync = CloudSync(provider, "pw", conflict_resolution="local")
    action = sync.sync_file(local, "data")
    assert action == "uploaded"
    assert decrypt(provider.download("data"), "pw") == b"local"


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


def test_decrypt_integrity_failure():
    token = encrypt(b"secret", "pw")
    tampered = bytearray(token)
    tampered[-1] ^= 0x01
    with pytest.raises(ValueError):
        decrypt(bytes(tampered), "pw")


def test_filesystem_provider_round_trip(tmp_path):
    provider = FilesystemProvider(tmp_path / "storage")
    sync = CloudSync(provider, "pw")
    local = tmp_path / "data.txt"
    local.write_text("hello")
    sync.backup_file(local, "data")
    local.unlink()
    assert sync.restore_file(local, "data")
    assert local.read_text() == "hello"


def test_profile_and_model_helpers(tmp_path):
    provider = InMemoryProvider()
    sync = CloudSync(provider, "pw")
    profile = tmp_path / "profile.json"
    profile.write_text("p")
    sync.backup_profile(profile)
    profile.unlink()
    assert sync.restore_profile(profile)
    assert profile.read_text() == "p"

    model = tmp_path / "model.bin"
    model.write_text("m")
    sync.backup_model(model, "m.bin")
    model.unlink()
    assert sync.restore_model(model, "m.bin")
    assert model.read_text() == "m"
