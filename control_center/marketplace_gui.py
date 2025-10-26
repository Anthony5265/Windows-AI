"""Tkinter panels for interacting with the plugin marketplace service.

The GUI allows browsing available plugins and publishing new ones to the
:mod:`marketplace` FastAPI service.  It is intentionally small and avoids
external dependencies beyond ``requests`` which is available in the test
environment.
"""

from __future__ import annotations

from typing import Dict, Any

try:  # pragma: no cover - import may fail on headless systems
    import tkinter as tk  # type: ignore
    from tkinter import ttk  # type: ignore
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]

import requests

__all__ = ["MarketplaceGUI"]


class MarketplaceGUI:
    """Simple interface for the plugin marketplace service."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        if tk is None or ttk is None:
            raise RuntimeError("tkinter is not available")
        self.base_url = base_url.rstrip("/")
        self.root = tk.Toplevel() if tk._default_root else tk.Tk()
        self.root.title("Plugin Marketplace")
        self._build_widgets()
        self.refresh()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self) -> None:
        self.tree = ttk.Treeview(self.root, columns=("description", "rating"), show="headings")
        self.tree.heading("description", text="Description")
        self.tree.heading("rating", text="Rating")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        form = ttk.Frame(self.root)
        form.pack(fill="x", padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.cmd_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=10).grid(row=0, column=0, padx=2)
        ttk.Entry(form, textvariable=self.desc_var, width=20).grid(row=0, column=1, padx=2)
        ttk.Entry(form, textvariable=self.cmd_var, width=20).grid(row=0, column=2, padx=2)
        ttk.Button(form, text="Publish", command=self.publish).grid(row=0, column=3, padx=2)
        ttk.Button(form, text="Refresh", command=self.refresh).grid(row=0, column=4, padx=2)

    # ----------------------------------------------------------------- Actions
    def refresh(self) -> None:
        """Fetch catalog from the marketplace service."""

        try:
            resp = requests.get(f"{self.base_url}/plugins", timeout=5)
            data: Dict[str, Any] = resp.json()
        except Exception:
            data = {"plugins": []}
        self.tree.delete(*self.tree.get_children())
        for plugin in data.get("plugins", []):
            self.tree.insert("", "end", values=(plugin.get("description"), plugin.get("rating")))

    def publish(self) -> None:
        payload = {
            "name": self.name_var.get() or "Unnamed",
            "description": self.desc_var.get() or "",
            "command": self.cmd_var.get() or "",
            "paid": False,
            "metadata": {},
            "dependencies": [],
        }
        try:
            requests.post(f"{self.base_url}/plugins", json=payload, timeout=5)
        finally:
            self.refresh()

    def run(self) -> None:  # pragma: no cover - manual execution helper
        self.root.mainloop()
