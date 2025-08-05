"""Manage optional plugins with basic security features.

This module loads plugin definitions from :mod:`plugins.catalog.json` and
provides a :class:`PluginManager` capable of installing them.  Plugins can
declare dependencies and include a simple integrity signature.  Installation
commands run inside a restricted sandbox directory to avoid unexpected
side‑effects during tests.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath

# Catalog lives alongside this file
CATALOG_PATH = Path(__file__).resolve().parent / "catalog.json"
# Temporary directory used for sandboxed execution
SANDBOX_DIR = Path(tempfile.gettempdir())


@dataclass
class Plugin:
    """Representation of a plugin entry in the catalog."""

    name: str
    description: str
    command: str
    paid: bool = False
    metadata: dict[str, str] | None = None
    rating: float | None = None
    dependencies: list[str] = field(default_factory=list)
    signature: str | None = None


def load_catalog(path: Path = CATALOG_PATH) -> list[Plugin]:
    """Load plugin definitions from a JSON catalog."""

    path = Path(path)
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    entries = data.get("plugins", []) if isinstance(data, dict) else []

    plugins: list[Plugin] = []
    for entry in entries:
        plugins.append(
            Plugin(
                name=entry.get("name", ""),
                description=entry.get("description", ""),
                command=entry.get("command", ""),
                paid=entry.get("paid", False),
                metadata=entry.get("metadata"),
                rating=entry.get("rating"),
                dependencies=entry.get("dependencies", []),
                signature=entry.get("signature"),
            )
        )
    return plugins


class PluginManager:
    """Present and install plugins from the catalog."""

    ALLOWED_COMMANDS = {"pip", "npm", "brew"}

    def __init__(self, catalog_path: Path = CATALOG_PATH) -> None:
        self.catalog_path = Path(catalog_path)
        self.plugins = load_catalog(self.catalog_path)
        self._installed: set[str] = set()

    # ------------------------------------------------------------------ helpers
    def get_plugin(self, name: str) -> Plugin | None:
        """Return a plugin by name."""

        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None

    def verify_signature(self, plugin: Plugin) -> None:
        """Ensure a plugin's signature matches its expected value.

        For simplicity we expect the signature to be the SHA256 hash of the
        plugin name.  Real implementations would use asymmetric cryptography.
        """

        if plugin.signature is None:
            return
        expected = hashlib.sha256(plugin.name.encode("utf-8")).hexdigest()
        if plugin.signature != expected:
            raise ValueError("Invalid signature")

    def sandbox_run(self, args: list[str]) -> None:
        """Execute a command inside a restricted environment."""

        subprocess.run(
            args,
            shell=False,
            check=True,
            cwd=str(SANDBOX_DIR),
            env={"PATH": os.environ.get("PATH", "")},
        )

    # --------------------------------------------------------------- installation
    def install(
        self,
        plugin: Plugin,
        messagebox=None,
        _stack: set[str] | None = None,
    ) -> None:
        """Install a plugin and its dependencies."""

        if plugin.name in self._installed:
            return

        if _stack is None:
            _stack = set()
        if plugin.name in _stack:
            raise ValueError("Cyclic dependency detected")
        _stack.add(plugin.name)

        # Install dependencies first
        for dep_name in plugin.dependencies:
            dep = self.get_plugin(dep_name)
            if dep is None:
                raise ValueError(f"Missing dependency: {dep_name}")
            self.install(dep, messagebox, _stack)

        _stack.remove(plugin.name)

        try:
            self.verify_signature(plugin)
            raw_args = shlex.split(plugin.command, posix=os.name != "nt")
            if not raw_args:
                raise ValueError("Empty command")
                
            if os.name == "nt":
                # ``shlex`` on Windows cannot handle unquoted executable paths
                # containing spaces.  Join tokens until we hit something that
                # looks like a real executable (has a file extension).
                exe = raw_args[0]
                i = 1
                while i < len(raw_args) and Path(exe).suffix == "":
                    exe += f" {raw_args[i]}"
                    i += 1
                args = [exe, *raw_args[i:]]
            else:
                args = raw_args

            exe_str = args[0]
            executable = Path(exe_str)
            # pathlib on POSIX does not recognise Windows paths as absolute.
            # Allow execution when the path is absolute for either platform or
            # when the command is explicitly whitelisted.
            is_abs = executable.is_absolute() or PureWindowsPath(exe_str).is_absolute()

            if not is_abs and executable.name not in self.ALLOWED_COMMANDS:
                raise ValueError("Command not allowed")
            self.sandbox_run(args)
            self._installed.add(plugin.name)
        except Exception as exc:  # pragma: no cover - subprocess path
            if messagebox is not None:
                messagebox.showerror("Plugin Install", f"Failed to install {plugin.name}: {exc}")
            else:
                raise

    # ------------------------------------------------------------- uninstallation
    def uninstall(
        self,
        plugin: Plugin,
        messagebox=None,
        _stack: set[str] | None = None,
    ) -> None:
        """Uninstall a plugin and any unneeded dependencies."""

        if plugin.name not in self._installed:
            return

        if _stack is None:
            _stack = set()
        if plugin.name in _stack:
            raise ValueError("Cyclic dependency detected")
        _stack.add(plugin.name)

        # Remove dependencies first when no other installed plugin requires them
        for dep_name in plugin.dependencies:
            dep = self.get_plugin(dep_name)
            if dep is None:
                raise ValueError(f"Missing dependency: {dep_name}")

            # Determine if another plugin still depends on this dependency
            shared = any(
                dep_name in (self.get_plugin(other).dependencies if self.get_plugin(other) else [])
                for other in self._installed
                if other != plugin.name
            )
            if not shared:
                self.uninstall(dep, messagebox, _stack)

        _stack.remove(plugin.name)

        try:
            raw_args = shlex.split(plugin.command, posix=os.name != "nt")
            if not raw_args:
                raise ValueError("Empty command")

            if os.name == "nt":
                exe = raw_args[0]
                i = 1
                while i < len(raw_args) and Path(exe).suffix == "":
                    exe += f" {raw_args[i]}"
                    i += 1
                args = [exe, *raw_args[i:]]
            else:
                args = raw_args

            if args[0] in self.ALLOWED_COMMANDS and len(args) > 1:
                args[1] = "uninstall"
                if args[0] == "pip" and "-y" not in args and "--yes" not in args:
                    args.append("-y")
            self.sandbox_run(args)
            self._installed.discard(plugin.name)
        except Exception as exc:  # pragma: no cover - subprocess path
            if messagebox is not None:
                messagebox.showerror("Plugin Uninstall", f"Failed to uninstall {plugin.name}: {exc}")
            else:
                raise


__all__ = ["Plugin", "PluginManager", "load_catalog", "SANDBOX_DIR"]

