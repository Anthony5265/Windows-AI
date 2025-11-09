"""GUI-based plugin manager that installs optional tools.

This module reads a plugin catalog and presents the entries in a simple
Tkinter interface.  Users can select which plugins to install and the manager
will invoke the associated installation commands.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STATE_PATH = Path(__file__).resolve().with_name("plugin_state.json")

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[2] / "plugins" / "catalog.json"
CATALOG_PATH = Path(os.environ.get("WINDOWS_AI_PLUGIN_CATALOG", DEFAULT_CATALOG_PATH))


@dataclass
class Plugin:
    """Representation of a single plugin entry."""

    name: str
    description: str
    command: str
    paid: bool = False
    metadata: dict | None = None
    rating: float | None = None
    dependencies: list | None = None


def load_catalog(path: Path = CATALOG_PATH) -> list[Plugin]:
    """Load plugin definitions from a JSON or YAML file."""

    path = Path(path)
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("PyYAML is required to load YAML catalogs") from exc
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text or "{}")

    entries = data.get("plugins", []) if isinstance(data, dict) else []
    # Create Plugin objects, handling optional fields
    plugins = []
    for entry in entries:
        # Extract only the fields that Plugin accepts
        plugin_data = {
            "name": entry.get("name", ""),
            "description": entry.get("description", ""),
            "command": entry.get("command", ""),
            "paid": entry.get("paid", False),
            "metadata": entry.get("metadata"),
            "rating": entry.get("rating"),
            "dependencies": entry.get("dependencies"),
        }
        plugins.append(Plugin(**plugin_data))
    return plugins


class PluginManager:
    """Present and install optional plugins defined in the catalog."""

    def __init__(
        self, catalog_path: Path = CATALOG_PATH, state_path: Path | None = None
    ) -> None:
        self.catalog_path = Path(catalog_path)
        self.state_path = Path(state_path) if state_path else STATE_PATH
        self.plugins = load_catalog(self.catalog_path)
        self.installed: list[str] = []
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text()) or {}
                self.installed = list(data.get("installed", []))
            except Exception:  # pragma: no cover - corrupted state file
                self.installed = []

    # --- State ------------------------------------------------------------
    def _save_state(self) -> None:
        self.state_path.write_text(
            json.dumps({"installed": self.installed}, indent=2),
            encoding="utf-8",
        )

    # --- Plugin Access ----------------------------------------------------
    def get_plugin(self, name: str) -> Plugin | None:
        """
        Get a plugin by name (case-insensitive).

        Args:
            name: Plugin name to search for

        Returns:
            Plugin object if found, None otherwise
        """
        name_lower = name.lower()
        for plugin in self.plugins:
            if plugin.name.lower() == name_lower:
                return plugin
        return None

    # --- GUI -------------------------------------------------------------
    def run(self) -> None:
        """Launch the Tkinter GUI for plugin selection."""

        try:
            import tkinter as tk
            from tkinter import messagebox, ttk
        except Exception as exc:  # pragma: no cover - environment specific
            raise RuntimeError("tkinter is required for the plugin manager") from exc

        root = tk.Tk()
        root.title("Plugin Manager")

        selections: dict[str, tk.BooleanVar] = {}
        frame = tk.LabelFrame(root, text="Available Plugins")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        for plugin in self.plugins:
            var = tk.BooleanVar(value=False)
            selections[plugin.name] = var
            label = (
                f"{plugin.name} ({'Paid' if plugin.paid else 'Free'})\n{plugin.description}"
            )
            ttk.Checkbutton(
                frame, text=label, variable=var, justify="left"
            ).pack(anchor="w", fill="x", padx=5, pady=2)

        def _install() -> None:
            chosen = [p for p in self.plugins if selections[p.name].get()]
            progress_win = tk.Toplevel(root)
            progress_win.title("Installing Plugins")
            ttk.Label(progress_win, text="Installing...").pack(padx=10, pady=10)
            progress_var = tk.IntVar(value=0)
            progress = ttk.Progressbar(
                progress_win, maximum=len(chosen), variable=progress_var
            )
            progress.pack(fill="x", padx=10, pady=10)

            installed_session: list[Plugin] = []

            def _step() -> None:
                progress_var.set(progress_var.get() + 1)
                progress_win.update_idletasks()

            try:
                for plugin in chosen:
                    self.install(plugin, messagebox, progress=_step)
                    installed_session.append(plugin)
            except Exception:
                self.rollback(installed_session)
                messagebox.showerror(
                    "Plugin Manager", "Installation failed; changes rolled back"
                )
            else:
                messagebox.showinfo("Plugin Manager", "Installation complete")
            finally:
                progress_win.destroy()
                root.destroy()

        ttk.Button(root, text="Install Selected", command=_install).pack(pady=5)
        root.mainloop()

    ALLOWED_COMMANDS = {"pip", "npm", "brew"}

    # --- Installation ----------------------------------------------------
    def install(self, plugin: Plugin, messagebox=None, progress=None) -> None:
        """Run the installation command for a plugin."""

        try:
            args = shlex.split(plugin.command)
            if not args:
                raise ValueError("Empty command")
            executable = Path(args[0])
            if not executable.is_absolute() and executable.name not in self.ALLOWED_COMMANDS:
                raise ValueError("Command not allowed")
            subprocess.run(args, shell=False, check=True, cwd=None, env=None)
            self.installed.append(plugin.name)
            self._save_state()
            if progress is not None:
                progress()
        except Exception as exc:  # pragma: no cover - subprocess path
            if messagebox is not None:
                messagebox.showerror(
                    "Plugin Install", f"Failed to install {plugin.name}: {exc}"
                )
            raise

    # --- Rollback --------------------------------------------------------
    def _uninstall_command(self, plugin: Plugin) -> list[str]:
        args = shlex.split(plugin.command)
        if not args:
            return []
        if args[0] == "pip" and "install" in args:
            return ["pip", "uninstall", "-y", args[-1]]
        if args[0] == "npm" and "install" in args:
            cmd = ["npm", "uninstall"]
            if "-g" in args:
                cmd.append("-g")
            cmd.append(args[-1])
            return cmd
        if args[0] == "brew" and "install" in args:
            return ["brew", "uninstall", args[-1]]
        return []

    def rollback(self, plugins: Iterable[Plugin]) -> None:
        """Attempt to uninstall previously installed plugins."""

        for plugin in reversed(list(plugins)):
            cmd = self._uninstall_command(plugin)
            if not cmd:
                continue
            try:
                subprocess.run(cmd, shell=False, check=True)
            except Exception:  # pragma: no cover - best effort
                pass
            if plugin.name in self.installed:
                self.installed.remove(plugin.name)
        self._save_state()


__all__ = ["Plugin", "PluginManager", "load_catalog"]
