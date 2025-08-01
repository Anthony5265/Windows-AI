"""Simple API key storage helper backed by the system keyring.

API keys were previously stored in a JSON file under ``~/.windows_ai``.  On
import, this module migrates any existing keys from that file into the system
keyring (Windows Credential Manager on Windows).  Future reads and writes use
the keyring directly so secrets are no longer kept on disk.
"""
from __future__ import annotations

import json
import os
from getpass import getpass
from typing import Dict, Optional

try:
    import keyring
    from keyring.errors import KeyringError
except Exception:  # pragma: no cover - keyring not installed
    keyring = None  # type: ignore[assignment]
    KeyringError = Exception  # type: ignore[misc]


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".windows_ai")
KEYS_FILE = os.path.join(CONFIG_DIR, "keys.json")
_USERNAME = "api_key"


def _migrate_file_to_keyring() -> None:
    """Migrate keys from the legacy JSON file into the system keyring."""

    if keyring is None or not os.path.exists(KEYS_FILE):
        return

    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data: Dict[str, str] = json.load(f)
    except Exception:
        return

    for service, value in data.items():
        try:
            keyring.set_password(service, _USERNAME, value)
        except Exception:
            # If any write fails keep the file so migration can retry later.
            return

    try:
        os.remove(KEYS_FILE)
        if not os.listdir(CONFIG_DIR):
            os.rmdir(CONFIG_DIR)
    except OSError:
        pass


# Run migration as soon as the module is imported.
_migrate_file_to_keyring()


def load_keys() -> Dict[str, str]:
    """Best-effort retrieval of all stored API keys.

    Because the `keyring` module does not offer a cross-platform way to
    enumerate stored secrets, callers can provide a comma-separated list of
    services through the ``WINDOWS_AI_SERVICES`` environment variable.  Any
    keys found for those services will be returned.  If no services are
    specified, or if the keyring backend is unavailable, the legacy JSON file
    is used as a fallback when present.
    """

    _migrate_file_to_keyring()

    services_env = os.getenv("WINDOWS_AI_SERVICES", "")
    services = [s.strip() for s in services_env.split(",") if s.strip()]
    keys: Dict[str, str] = {}

    if keyring is not None and services:
        for svc in services:
            try:
                value = keyring.get_password(svc, _USERNAME)
            except KeyringError:
                value = None
            if value:
                keys[svc] = value
        if keys:
            return keys

    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    return keys


def load_key(service: str) -> Optional[str]:
    """Retrieve a stored API key for ``service``.

    Returns ``None`` if the key is not set or no suitable keyring backend is
    available.
    """

    _migrate_file_to_keyring()

    if keyring is None:
        return None

    try:
        return keyring.get_password(service, _USERNAME)
    except KeyringError:
        return None


def save_key(service: str, key: str) -> None:
    """Persist a new API key using the system keyring."""

    _migrate_file_to_keyring()

    if keyring is None:
        raise RuntimeError("No system keyring backend available")

    keyring.set_password(service, _USERNAME, key)


def list_keys() -> Dict[str, str]:
    """Return a mapping of stored API keys.

    The ``keyring`` package does not expose a cross-platform API for
    enumerating stored secrets.  To keep behaviour consistent across storage
    backends we simply delegate to :func:`load_keys`, which relies on the
    ``WINDOWS_AI_SERVICES`` environment variable to know which services to
    query from the secure storage.  When using the legacy JSON file backend the
    contents of that file are returned.
    """

    # ``load_keys`` already handles migration from the legacy file backend and
    # queries the system keyring when available.
    return load_keys()


def delete_key(service: str) -> bool:
    """Remove a stored API key for ``service``.

    The function returns ``True`` when a key existed and was removed.  When the
    system keyring backend is unavailable the legacy JSON file is used as a
    fallback.  The migration helper is invoked so callers always interact with
    the secure storage when possible.
    """

    _migrate_file_to_keyring()

    if keyring is not None:
        try:
            keyring.delete_password(service, _USERNAME)
            return True
        except KeyringError:
            return False

    # Fallback to file-based storage
    if not os.path.exists(KEYS_FILE):
        return False

    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data: Dict[str, str] = json.load(f)
    except Exception:
        return False

    if service not in data:
        return False

    del data[service]

    if data:
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    else:
        try:
            os.remove(KEYS_FILE)
            if not os.listdir(CONFIG_DIR):
                os.rmdir(CONFIG_DIR)
        except OSError:
            pass
    return True


def prompt_and_save() -> None:
    """Interactively ask the user for an API key and save it."""

    service = input("Service name: ")
    key = getpass("API key: ")
    save_key(service, key)
    print(f"Saved {service} key to the system keyring")
