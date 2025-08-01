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

    The keyring backend does not provide a portable way to list stored
    secrets, so this function returns an empty dictionary once keys have been
    migrated.  It is kept for backward compatibility with the original
    file-based implementation.
    """

    _migrate_file_to_keyring()

    if keyring is None and os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    return {}


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


def prompt_and_save() -> None:
    """Interactively ask the user for an API key and save it."""

    service = input("Service name: ")
    key = getpass("API key: ")
    save_key(service, key)
    print(f"Saved {service} key to the system keyring")
