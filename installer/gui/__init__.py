from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from .. import api_keys, system_info, cli


def main() -> None:
    """Launch a minimal Tkinter interface for the installer."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # pragma: no cover - environment specific
        raise RuntimeError("tkinter is not available or no display is found") from exc

    root.title("Windows AI Installer")

    info = system_info.detect_system()
    info_lines = [f"{k}: {v}" for k, v in info.items()]
    info_label = tk.Label(root, text="\n".join(info_lines), justify="left")
    info_label.pack(padx=10, pady=10)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    def add_api_key() -> None:
        service = simpledialog.askstring("API Key", "Service name:", parent=root)
        if not service:
            return
        key = simpledialog.askstring(
            "API Key", f"Enter API key for {service}:", show="*", parent=root
        )
        if not key:
            return
        try:
            api_keys.save_key(service, key)
            messagebox.showinfo("API Key", f"Saved key for {service}")
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("API Key", str(exc))

    def run_install_all() -> None:
        try:
            cli.install_all()
            messagebox.showinfo("Install", "Install all completed")
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("Install", f"Install failed: {exc}")

    tk.Button(button_frame, text="Add API Key", command=add_api_key).pack(
        side=tk.LEFT, padx=5
    )
    tk.Button(button_frame, text="Install All", command=run_install_all).pack(
        side=tk.LEFT, padx=5
    )

    root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
