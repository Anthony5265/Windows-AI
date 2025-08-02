"""GUI-based plugin manager that installs optional tools.

This module reads a plugin catalog and presents the entries in a simple
Tkinter interface.  Users can select which plugins to install and the manager
will invoke the associated installation commands.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

CATALOG_PATH = Path(__file__).resolve().parents[2] / "plugins" / "catalog.json"


@dataclass
class Plugin:
    """Representation of a single plugin entry."""

    name: str
    description: str
    command: str
    paid: bool = False


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
    return [Plugin(**entry) for entry in entries]


class PluginManager:
    """Present and install optional plugins defined in the catalog."""

    def __init__(self, catalog_path: Path = CATALOG_PATH) -> None:
        self.catalog_path = Path(catalog_path)
        self.plugins = load_catalog(self.catalog_path)

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
            label = f"{plugin.name} ({'Paid' if plugin.paid else 'Free'})"
            ttk.Checkbutton(frame, text=label, variable=var).pack(anchor="w")

        def _install() -> None:
            chosen = [p for p in self.plugins if selections[p.name].get()]
            for plugin in chosen:
                self.install(plugin, messagebox)
            messagebox.showinfo("Plugin Manager", "Installation complete")
            root.destroy()

        ttk.Button(root, text="Install Selected", command=_install).pack(pady=5)
        root.mainloop()

    # --- Installation ----------------------------------------------------
    def install(self, plugin: Plugin, messagebox=None) -> None:
        """Run the installation command for a plugin."""

        try:
            subprocess.run(plugin.command, shell=True, check=True)
        except Exception as exc:  # pragma: no cover - subprocess path
            if messagebox is not None:
                messagebox.showerror(
                    "Plugin Install", f"Failed to install {plugin.name}: {exc}"
                )
            else:
                raise


__all__ = ["Plugin", "PluginManager", "load_catalog"]
