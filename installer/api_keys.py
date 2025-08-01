"""Simple API key storage helper."""
from __future__ import annotations

import json
import os
from getpass import getpass
from typing import Dict

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".windows_ai")
KEYS_FILE = os.path.join(CONFIG_DIR, "keys.json")


def load_keys() -> Dict[str, str]:
    """Load stored API keys."""
    try:
        with open(KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_key(service: str, key: str) -> None:
    """Persist a new API key."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    keys = load_keys()
    keys[service] = key
    with open(KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2)


def prompt_and_save() -> None:
    """Interactively ask the user for an API key and save it."""
    service = input("Service name: ")
    key = getpass("API key: ")
    save_key(service, key)
    print(f"Saved {service} key to {KEYS_FILE}")
