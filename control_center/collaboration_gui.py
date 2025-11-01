"""Team dashboard interface for the Windows AI Control Center.

Provides a minimal Tkinter-based UI that allows administrators to create and
share dashboards with team members. It reuses the :class:`DashboardManager`
from :mod:`control_center.gui` for storing dashboard metadata.
"""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - import may fail on headless systems
    import tkinter as tk  # type: ignore
    from tkinter import ttk, simpledialog  # type: ignore
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    simpledialog = None  # type: ignore[assignment]

from .gui import DashboardManager

__all__ = ["CollaborationGUI"]


class CollaborationGUI:
    """Lightweight interface for managing shared dashboards."""

    def __init__(
        self,
        root: Optional["tk.Tk"] = None,
        manager: Optional[DashboardManager] = None,
    ) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("tkinter is not available")
        try:
            self.root = root or tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError(
                "tkinter is not available or no display is found"
            ) from exc
        self.manager = manager or DashboardManager()
        self.root.title("Team Dashboards")
        self._build_widgets()
        self.refresh()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(frame, height=10)
        self.listbox.pack(side="left", fill="both", expand=True)

        btns = ttk.Frame(frame)
        btns.pack(side="right", fill="y")
        ttk.Button(btns, text="New", command=self.new_dashboard).pack(fill="x")
        ttk.Button(
            btns,
            text="Share",
            command=self.share_dashboard,
        ).pack(fill="x")
        ttk.Button(btns, text="Refresh", command=self.refresh).pack(fill="x")

    # ------------------------------------------------------------- Operations
    def refresh(self) -> None:
        """Refresh the dashboard list."""

        self.listbox.delete(0, tk.END)
        for name in sorted(self.manager.dashboards):
            self.listbox.insert(tk.END, name)

    def new_dashboard(self) -> None:
        """Prompt for dashboard info and create it."""

        if simpledialog is None:
            return
        name = simpledialog.askstring("Dashboard", "Name")
        owner = simpledialog.askstring("Dashboard", "Owner")
        if name and owner:
            self.manager.create(name, owner)
            self.refresh()

    def share_dashboard(self) -> None:
        """Prompt for user and role and share the dashboard."""

        if simpledialog is None:
            return
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        user = simpledialog.askstring("Share", "User")
        role = simpledialog.askstring("Share", "Role (view/edit)")
        if user and role:
            self.manager.share(name, user, role)
