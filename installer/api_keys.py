"""API key storage helpers with Windows-specific secure backend.

The module exposes a small API for persisting secrets used by the
application.  When running on Windows the preferred backend is the
Windows Credential Manager accessed through ``win32cred``.  If that
module is unavailable the ``keyring`` package is used as a generic
fallback.  For non-Windows platforms where no keyring backend is
available an encrypted JSON file stored under ``~/.windows_ai`` is used.

The encrypted file backend relies on ``cryptography.fernet``.  When that
package is missing attempts to save a key will raise ``RuntimeError``.
This keeps plaintext API keys off disk while still permitting basic
functionality in minimal environments.
"""

from __future__ import annotations

import json
import os
from getpass import getpass
from typing import Dict, Optional

from .logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional backend imports
# ---------------------------------------------------------------------------

IS_WINDOWS = os.name == "nt"

try:  # pragma: no cover - windows specific import
    if IS_WINDOWS:
        import win32cred  # type: ignore
    else:  # pragma: no cover - executed only on Windows
        win32cred = None  # type: ignore[assignment]
except Exception:  # pragma: no cover - win32cred not installed
    win32cred = None  # type: ignore[assignment]

try:
    import keyring
    from keyring.errors import KeyringError
except Exception:  # pragma: no cover - keyring not installed
    keyring = None  # type: ignore[assignment]
    KeyringError = Exception  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - cryptography not installed
    Fernet = None  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Paths used by the file based backend
# ---------------------------------------------------------------------------

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".windows_ai")
ENC_FILE = os.path.join(CONFIG_DIR, "keys.enc")
FERNET_KEY_FILE = os.path.join(CONFIG_DIR, "fernet.key")
_USERNAME = "api_key"


# ---------------------------------------------------------------------------
# Helper functions for the encrypted file backend
# ---------------------------------------------------------------------------

def _ensure_config_dir() -> None:
    """Create the configuration directory when needed."""

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
    except OSError:  # pragma: no cover - unlikely failure
        logger.exception("Failed to create config directory %s", CONFIG_DIR)


def _load_fernet() -> Optional["Fernet"]:
    """Return a ``Fernet`` instance initialised with the stored key."""

    if Fernet is None:
        return None

    _ensure_config_dir()

    key: bytes
    if not os.path.exists(FERNET_KEY_FILE):
        key = Fernet.generate_key()
        try:
            with open(FERNET_KEY_FILE, "wb") as kf:
                os.chmod(FERNET_KEY_FILE, 0o600)
                kf.write(key)
        except OSError:  # pragma: no cover - filesystem errors
            logger.exception("Failed to write key file %s", FERNET_KEY_FILE)
            return None
    else:
        try:
            with open(FERNET_KEY_FILE, "rb") as kf:
                key = kf.read()
        except OSError:  # pragma: no cover - filesystem errors
            logger.exception("Failed to read key file %s", FERNET_KEY_FILE)
            return None

    try:
        return Fernet(key)
    except Exception:  # pragma: no cover - invalid key
        logger.exception("Failed to initialise Fernet with key file")
        return None


def _load_file_store() -> Dict[str, str]:
    """Decrypt the on-disk store and return the mapping."""

    fernet = _load_fernet()
    if fernet is None or not os.path.exists(ENC_FILE):
        return {}

    try:
        with open(ENC_FILE, "rb") as f:
            data = f.read()
        decrypted = fernet.decrypt(data)
        return json.loads(decrypted.decode("utf-8"))
    except Exception:  # pragma: no cover - corrupt file or key
        logger.exception("Failed to read encrypted keys file")
        return {}


def _save_file_store(store: Dict[str, str]) -> None:
    """Write the mapping to disk using the encrypted backend."""

    fernet = _load_fernet()
    if fernet is None:
        raise RuntimeError("Encryption backend not available")

    data = json.dumps(store).encode("utf-8")
    encrypted = fernet.encrypt(data)

    _ensure_config_dir()
    try:
        with open(ENC_FILE, "wb") as f:
            os.chmod(ENC_FILE, 0o600)
            f.write(encrypted)
    except OSError:  # pragma: no cover - filesystem errors
        logger.exception("Failed to write encrypted keys file")
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_key(service: str) -> Optional[str]:
    """Retrieve a stored API key for ``service``.

    Returns ``None`` when the key is unavailable or no backend can provide
    it.
    """

    if IS_WINDOWS and win32cred is not None:
        try:  # pragma: no cover - executed only on Windows
            cred = win32cred.CredRead(service, win32cred.CRED_TYPE_GENERIC, 0)
            blob = cred.get("CredentialBlob", b"")
            if isinstance(blob, bytes):
                return blob.decode("utf-16-le")
            return blob
        except Exception:  # pragma: no cover - win32cred errors
            logger.exception("Failed to read key for %s", service)
            return None

    if keyring is not None:
        try:
            return keyring.get_password(service, _USERNAME)
        except KeyringError:
            logger.exception("Failed to read key for %s from keyring", service)
            return None

    store = _load_file_store()
    return store.get(service)


def save_key(service: str, key: str) -> None:
    """Persist an API key using the most secure backend available."""

    if IS_WINDOWS and win32cred is not None:
        try:  # pragma: no cover - executed only on Windows
            credential = {
                "Type": win32cred.CRED_TYPE_GENERIC,
                "TargetName": service,
                "UserName": _USERNAME,
                "CredentialBlob": key.encode("utf-16-le"),
                "Persist": win32cred.CRED_PERSIST_LOCAL_MACHINE,
            }
            win32cred.CredWrite(credential, 0)
            return
        except Exception:  # pragma: no cover - win32cred errors
            logger.exception("Failed to write key for %s", service)
            raise

    if keyring is not None:
        try:
            keyring.set_password(service, _USERNAME, key)
            return
        except Exception:
            logger.exception("Failed to write key for %s to keyring", service)
            raise

    store = _load_file_store()
    store[service] = key
    _save_file_store(store)


def list_keys() -> Dict[str, str]:
    """Return a mapping of stored API keys.

    Because not all backends support enumeration, callers can provide a
    comma-separated list of services through the ``WINDOWS_AI_SERVICES``
    environment variable.  Keys for those services will be returned when
    available.
    """

    services_env = os.getenv("WINDOWS_AI_SERVICES", "")
    services = [s.strip() for s in services_env.split(",") if s.strip()]
    keys: Dict[str, str] = {}

    if not services:
        if keyring is None and not (IS_WINDOWS and win32cred is not None):
            # File backend can enumerate all stored services
            return _load_file_store()
        return {}

    for svc in services:
        value = load_key(svc)
        if value:
            keys[svc] = value

    return keys


def delete_key(service: str) -> bool:
    """Remove a stored API key for ``service``."""

    if IS_WINDOWS and win32cred is not None:
        try:  # pragma: no cover - executed only on Windows
            win32cred.CredDelete(service, win32cred.CRED_TYPE_GENERIC, 0)
            return True
        except Exception:  # pragma: no cover - win32cred errors
            logger.exception("Failed to delete key for %s", service)
            return False

    if keyring is not None:
        try:
            keyring.delete_password(service, _USERNAME)
            return True
        except KeyringError:
            logger.exception("Failed to delete key for %s from keyring", service)
            return False

    store = _load_file_store()
    existed = service in store
    if existed:
        del store[service]
        _save_file_store(store)
    return existed


def prompt_and_save() -> None:
    """Interactively prompt the user for an API key and save it."""

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

    print(f"Saved {service} key")


__all__ = [
    "load_key",
    "save_key",
    "list_keys",
    "delete_key",
    "prompt_and_save",
    "CONFIG_DIR",
    "ENC_FILE",
    "FERNET_KEY_FILE",
    "keyring",
    "KeyringError",
    "win32cred",
]

