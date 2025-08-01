"""Virtual environment management for installer plugins and toolsets."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
import venv

# Base directory where all virtual environments are stored
BASE_DIR = Path.home() / ".windows_ai" / "venvs"
BASE_DIR.mkdir(parents=True, exist_ok=True)


def create_env(name: str) -> Path:
    """Create (if needed) and return the path to a virtual environment.

    Parameters
    ----------
    name:
        Name of the plugin or toolset.  The environment will be created under
        ``~/.windows_ai/venvs/<name>``.
    """

    env_path = BASE_DIR / name
    if not env_path.exists():
        venv.EnvBuilder(with_pip=True).create(env_path)
    return env_path


def python_executable(env_path: Path) -> Path:
    """Return the Python interpreter for ``env_path``."""

    return env_path / ("Scripts" if os.name == "nt" else "bin") / "python"


def install_packages(env_path: Path, packages: list[str]) -> None:
    """Install ``packages`` into the virtual environment at ``env_path``."""

    if not packages:
        return
    python = python_executable(env_path)
    subprocess.check_call([python, "-m", "pip", "install", *packages])


__all__ = ["BASE_DIR", "create_env", "python_executable", "install_packages"]
