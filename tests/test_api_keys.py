import pytest
from installer import api_keys


def setup_dummy_keyring(monkeypatch):
    """Install a dummy in-memory keyring backend."""

    store = {}

    class DummyKeyring:
        def set_password(self, service, username, password):
            store[(service, username)] = password

        def get_password(self, service, username):
            return store.get((service, username))

        def delete_password(self, service, username):
            if (service, username) in store:
                del store[(service, username)]
            else:
                raise api_keys.KeyringError("not found")

    dummy = DummyKeyring()
    monkeypatch.setattr(api_keys, "keyring", dummy)
    monkeypatch.setattr(api_keys, "win32cred", None)
    return store


def test_save_list_load_delete_with_keyring(monkeypatch):
    store = setup_dummy_keyring(monkeypatch)
    monkeypatch.setenv("WINDOWS_AI_SERVICES", "svc")

    api_keys.save_key("svc", "secret")
    assert store[("svc", api_keys._USERNAME)] == "secret"
    assert api_keys.list_keys() == {"svc": "secret"}
    assert api_keys.load_key("svc") == "secret"
    assert api_keys.delete_key("svc") is True
    assert api_keys.list_keys() == {}
    assert api_keys.load_key("svc") is None


class DummyFernet:
    """Simple reversible "encryption" for tests."""

    def __init__(self, key: bytes):
        self.key = key

    @staticmethod
    def generate_key() -> bytes:
        return b"0" * 32

    def encrypt(self, data: bytes) -> bytes:
        return data[::-1]

    def decrypt(self, token: bytes) -> bytes:
        return token[::-1]


def test_file_backend_encrypted(tmp_path, monkeypatch):
    monkeypatch.setattr(api_keys, "win32cred", None)
    monkeypatch.setattr(api_keys, "keyring", None)
    monkeypatch.setattr(api_keys, "Fernet", DummyFernet)
    monkeypatch.setattr(api_keys, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(api_keys, "ENC_FILE", str(tmp_path / "keys.enc"))
    monkeypatch.setattr(api_keys, "FERNET_KEY_FILE", str(tmp_path / "fernet.key"))

    api_keys.save_key("svc", "secret")
    assert api_keys.load_key("svc") == "secret"
    assert api_keys.list_keys() == {"svc": "secret"}
    assert api_keys.delete_key("svc") is True
    assert api_keys.load_key("svc") is None

    with open(api_keys.ENC_FILE, "rb") as f:
        content = f.read()
    assert b"secret" not in content


def test_save_key_no_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(api_keys, "win32cred", None)
    monkeypatch.setattr(api_keys, "keyring", None)
    monkeypatch.setattr(api_keys, "Fernet", None)
    monkeypatch.setattr(api_keys, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(api_keys, "ENC_FILE", str(tmp_path / "keys.enc"))
    monkeypatch.setattr(api_keys, "FERNET_KEY_FILE", str(tmp_path / "fernet.key"))

    with pytest.raises(RuntimeError):
        api_keys.save_key("svc", "secret")


def test_load_key_no_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(api_keys, "win32cred", None)
    monkeypatch.setattr(api_keys, "keyring", None)
    monkeypatch.setattr(api_keys, "Fernet", None)
    monkeypatch.setattr(api_keys, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(api_keys, "ENC_FILE", str(tmp_path / "keys.enc"))
    monkeypatch.setattr(api_keys, "FERNET_KEY_FILE", str(tmp_path / "fernet.key"))

    assert api_keys.load_key("svc") is None
