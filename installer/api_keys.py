"""Simple API key storage helper backed by the system keyring.

API keys were previously stored in a JSON file under ``~/.windows_ai``.  On
import, this module migrates any existing keys from that file into the system
keyring (Windows Credential Manager on Windows).  After a successful
migration the legacy file is removed and all future reads and writes interact
solely with the keyring so secrets are no longer kept on disk.
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

from .logging_config import get_logger

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".windows_ai")
KEYS_FILE = os.path.join(CONFIG_DIR, "keys.json")
_USERNAME = "api_key"

logger = get_logger(__name__)


def _migrate_file_to_keyring() -> None:
    """Migrate keys from the legacy JSON file into the system keyring."""

    if keyring is None or not os.path.exists(KEYS_FILE):
        return

    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            data: Dict[str, str] = json.load(f)
    except Exception:
        logger.exception("Failed to read legacy keys file %s", KEYS_FILE)
        return

    for service, value in data.items():
        try:
            keyring.set_password(service, _USERNAME, value)
        except Exception:
            # If any write fails keep the file so migration can retry later.
            logger.exception(
                "Failed to store key for %s in system keyring", service
            )
            return

    try:
        os.remove(KEYS_FILE)
        if not os.listdir(CONFIG_DIR):
            os.rmdir(CONFIG_DIR)
    except OSError:
        logger.exception("Failed to clean up legacy key files")


# Run migration as soon as the module is imported.
_migrate_file_to_keyring()


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
        logger.exception("Failed to load key for %s", service)
        return None


def save_key(service: str, key: str) -> None:
    """Persist a new API key using the system keyring."""

    _migrate_file_to_keyring()

    if keyring is None:
        raise RuntimeError("No system keyring backend available")

    try:
        keyring.set_password(service, _USERNAME, key)
    except Exception:
        logger.exception("Failed to save key for %s", service)
        raise


def list_keys() -> Dict[str, str]:
    """Return a mapping of stored API keys from the system keyring.

    Because the ``keyring`` package does not expose a cross-platform API for
    enumerating stored secrets, callers can provide a comma-separated list of
    services through the ``WINDOWS_AI_SERVICES`` environment variable.  Any
    keys found for those services will be returned.  When the keyring backend
    is unavailable an empty mapping is returned.
    """

    _migrate_file_to_keyring()

    if keyring is None:
        return {}

    services_env = os.getenv("WINDOWS_AI_SERVICES", "")
    services = [s.strip() for s in services_env.split(",") if s.strip()]
    keys: Dict[str, str] = {}

    for svc in services:
        value = load_key(svc)
        if value:
            keys[svc] = value

    return keys


def delete_key(service: str) -> bool:
    """Remove a stored API key for ``service``.

    The function returns ``True`` when a key existed and was removed.  If the
    system keyring backend is unavailable ``False`` is returned.  The migration
    helper is invoked so callers always interact with the secure storage when
    possible.
    """

    _migrate_file_to_keyring()

    if keyring is None:
        return False

    try:
        keyring.delete_password(service, _USERNAME)
        return True
    except KeyringError:
        logger.exception("Failed to delete key for %s", service)
        return False


def prompt_and_save() -> None:
    """Interactively ask the user for an API key and save it."""

    try:
        service = input("Service name: ")
        key = getpass("API key: ")
    except Exception:
        logger.exception("Failed to read API key input")
        return
    try:
        save_key(service, key)
    except Exception:
        logger.exception("Failed to save key for %s", service)
        return
    print(f"Saved {service} key to the system keyring")
