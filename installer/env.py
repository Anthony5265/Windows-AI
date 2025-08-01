"""Virtual environment management for installer plugins and toolsets.

This module abstracts creation of isolated Python environments using either the
built-in ``venv`` module or ``conda`` when available.  Paths to created
environments are recorded so the AI Control Center can later activate them.
"""

from __future__ import annotations

import json
import os
import subprocess
import venv
from pathlib import Path
from typing import Iterable
import shutil

# Base configuration and environment directories
CONFIG_DIR = Path.home() / ".windows_ai"
BASE_DIR = CONFIG_DIR / "venvs"
ENV_RECORD_FILE = CONFIG_DIR / "envs.json"
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _use_conda() -> bool:
    """Return ``True`` if conda environments should be used."""

    env_var = os.getenv("WINDOWS_AI_USE_CONDA")
    if env_var is not None:
        return env_var.lower() not in {"0", "false", "no"}
    return shutil.which("conda") is not None


def _record_env_path(name: str, path: Path) -> None:
    """Persist the mapping between ``name`` and ``path``."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data: dict[str, str] = {}
    if ENV_RECORD_FILE.exists():
        try:
            data = json.loads(ENV_RECORD_FILE.read_text())
        except Exception:
            data = {}
    data[name] = str(path)
    ENV_RECORD_FILE.write_text(json.dumps(data, indent=2))


def create_env(name: str, backend: str | None = None) -> Path:
    """Create (if needed) and return the path to an isolated environment.

    Parameters
    ----------
    name:
        Name of the plugin or toolset.  The environment will be created under
        ``~/.windows_ai/venvs/<name>``.
    backend:
        Optional backend selector.  Accepts ``"venv"`` or ``"conda"``.  When
        omitted the function automatically chooses ``conda`` if
        ``WINDOWS_AI_USE_CONDA`` is set or the ``conda`` command is available.
    """

    env_path = BASE_DIR / name
    backend = backend or ("conda" if _use_conda() else "venv")
    if not env_path.exists():
        if backend == "conda":
            subprocess.check_call(["conda", "create", "-y", "-p", str(env_path), "python"])
        else:
            venv.EnvBuilder(with_pip=True).create(env_path)
    _record_env_path(name, env_path)
    return env_path


def python_executable(env_path: Path) -> Path:
    """Return the Python interpreter for ``env_path``."""

    return env_path / ("Scripts" if os.name == "nt" else "bin") / "python"


def install_packages(env_path: Path, packages: Iterable[str]) -> None:
    """Install ``packages`` into the environment at ``env_path``."""

    packages = list(packages)
    if not packages:
        return
    python = python_executable(env_path)
    subprocess.check_call([python, "-m", "pip", "install", *packages])


def load_recorded_envs() -> dict[str, str]:
    """Return the mapping of recorded environments."""

    if not ENV_RECORD_FILE.exists():
        return {}
    try:
        return json.loads(ENV_RECORD_FILE.read_text())
    except Exception:
        return {}


__all__ = [
    "CONFIG_DIR",
    "BASE_DIR",
    "ENV_RECORD_FILE",
    "create_env",
    "python_executable",
    "install_packages",
    "load_recorded_envs",
]
