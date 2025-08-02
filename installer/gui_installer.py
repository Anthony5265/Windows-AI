"""Minimal Tkinter-based installer front end.

The GUI exposes system detection and API-key storage through a couple of
buttons and a progress bar. It intentionally keeps dependencies light so
it can run in constrained environments.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from . import api_keys, system_info

__all__ = ["GUIInstaller", "main"]


class GUIInstaller:
    """Minimal Tkinter-based installer front end."""

    def __init__(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError("tkinter is not available or no display is found") from exc

        self.root.title("Windows AI Installer")

        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=10)

        ttk.Button(
            button_frame, text="Detect System", command=self.detect_system
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add API Key", command=self.add_api_key).pack(
            side=tk.LEFT, padx=5
        )

        self.info = tk.Text(self.root, width=60, height=10, state="disabled")
        self.info.pack(padx=10, pady=5)

        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)

    # --- System detection -------------------------------------------------
    def detect_system(self) -> None:
        """Run system detection in the background and show the results."""

        self.progress.config(mode="indeterminate")
        self.progress.start()
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self) -> None:
        """Worker thread to gather system info and update the text widget."""

        info = system_info.detect_system()

        def update() -> None:
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)
            self.info.config(state="normal")
            self.info.delete("1.0", tk.END)
            for k, v in info.items():
                self.info.insert(tk.END, f"{k}: {v}\n")
            self.info.config(state="disabled")

        self.root.after(0, update)

    # --- API key handling -------------------------------------------------
    def add_api_key(self) -> None:
        """Prompt the user for an API key and store it on disk."""
        service = simpledialog.askstring("API Key", "Service name:", parent=self.root)
        if not service:
            return
        key = simpledialog.askstring(
            "API Key", f"Enter API key for {service}:", show="*", parent=self.root
        )
        if not key:
            return
        self.progress.config(mode="indeterminate")
        self.progress.start()
        try:
            api_keys.save_key(service, key)
            messagebox.showinfo("API Key", f"Saved key for {service}")
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("API Key", str(exc))
        finally:
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)


def main() -> None:
    gui = GUIInstaller()
    gui.root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
