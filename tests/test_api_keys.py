import types
import pytest
from installer import api_keys


def setup_dummy_keyring(monkeypatch):
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
    return store


def test_save_load_delete_key(monkeypatch):
    monkeypatch.setattr(api_keys, "_migrate_file_to_keyring", lambda: None)
    store = setup_dummy_keyring(monkeypatch)

    api_keys.save_key("svc", "secret")
    assert store[("svc", api_keys._USERNAME)] == "secret"
    assert api_keys.load_key("svc") == "secret"
    assert api_keys.delete_key("svc") is True
    assert api_keys.load_key("svc") is None


def test_save_key_no_keyring(monkeypatch):
    monkeypatch.setattr(api_keys, "keyring", None)
    monkeypatch.setattr(api_keys, "_migrate_file_to_keyring", lambda: None)
    with pytest.raises(RuntimeError):
        api_keys.save_key("svc", "secret")


def test_load_key_no_keyring(monkeypatch):
    monkeypatch.setattr(api_keys, "keyring", None)
    monkeypatch.setattr(api_keys, "_migrate_file_to_keyring", lambda: None)
    assert api_keys.load_key("svc") is None
