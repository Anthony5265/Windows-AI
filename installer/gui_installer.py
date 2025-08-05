"""Minimal Tkinter-based installer front end.

The GUI exposes system detection and API-key storage through a couple of
buttons and a progress bar. It intentionally keeps dependencies light so
it can run in constrained environments.
"""

from __future__ import annotations

import os
import ctypes
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from installer.locales import _

if __package__ is None or __package__ == "":  # pragma: no cover - script entry
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from installer import api_keys, model_selector, system_info

__all__ = ["GUIInstaller", "main"]


class GUIInstaller:
    """Minimal Tkinter-based installer front end."""

    def __init__(self, root: tk.Tk | None = None) -> None:
        try:
            self.root = root or tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError(
                _("tkinter is not available or no display is found")
            ) from exc

        self.root.title(_("Windows AI Installer"))

        # configuration defaults
        self.auto_select: bool = True
        self.backend: str | None = None
        self.model_specs = {
            "requires_gpu": True,
            "min_vram_gb": 4.0,
            "min_ram_gb": 8.0,
        }

        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=10)

        ttk.Button(
            button_frame, text=_("Detect System"), command=self.detect_system
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=_("Add API Key"), command=self.add_api_key).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text=_("Check API Key"), command=self.check_api_key).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            button_frame, text=_("Install Dependencies"), command=self.install_all
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text=_("Configure"), command=self.open_config).pack(
            side=tk.LEFT, padx=5
        )

        self.info = tk.Text(self.root, width=60, height=10, state="disabled")
        self.info.pack(padx=10, pady=5)

        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)
        self.root.protocol("WM_DELETE_WINDOW", self._finalize)

    @staticmethod
    def _parse_float(value: str, label: str) -> float | None:
        """Convert a string to ``float`` while reporting errors."""

        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except Exception:
            messagebox.showerror("Configuration", f"{label} must be a number")
            raise ValueError from None

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
            if self.auto_select:
                backend = model_selector.select_backend("default", self.model_specs)
                self.backend = backend
                self.info.insert(
                    tk.END,
                    _("Recommended backend: {backend}").format(backend=backend) + "\n",
                )
            else:
                self.info.insert(
                    tk.END,
                    _("Manual backend: {backend}").format(backend=self.backend) + "\n",
                )
            self.info.config(state="disabled")

        self.root.after(0, update)

    # --- API key handling -------------------------------------------------
    def add_api_key(self) -> None:
        """Prompt the user for an API key and store it on disk."""
        service = simpledialog.askstring(_("API Key"), _("Service name:"), parent=self.root)
        if not service:
            return
        key = simpledialog.askstring(
            _("API Key"),
            _("Enter API key for {service}:").format(service=service),
            show="*",
            parent=self.root,
        )
        if not key:
            return
        self.progress.config(mode="indeterminate")
        self.progress.start()
        try:
            api_keys.save_key(service, key)
            messagebox.showinfo(
                _("API Key"), _("Saved key for {service}").format(service=service)
            )
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror(_("API Key"), str(exc))
        finally:
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)

    def check_api_key(self) -> None:
        """Verify whether a stored key exists for a service."""

        service = simpledialog.askstring(_("API Key"), _("Service name:"), parent=self.root)
        if not service:
            return
        self.progress.config(mode="indeterminate")
        self.progress.start()
        try:
            key = api_keys.load_key(service)
            if key:
                messagebox.showinfo(
                    _("API Key"), _("Key stored for {service}").format(service=service)
                )
            else:
                messagebox.showinfo(
                    _("API Key"), _("No key stored for {service}").format(service=service)
                )
        finally:
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)

    # --- Dependency installation -----------------------------------------
    def install_all(self) -> None:
        """Install plugin/tool dependencies with one click."""

        self.progress.config(mode="indeterminate")
        self.progress.start()
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self) -> None:
        from installer import env_setup

        env_setup.setup_all()

        def update() -> None:
            self.progress.stop()
            self.progress.config(mode="determinate", value=0)
            messagebox.showinfo(
                _("Installer"), _("Plugin and tool dependencies installed")
            )

        self.root.after(0, update)

    # --- Configuration ----------------------------------------------------
    def open_config(self) -> None:
        """Open the advanced configuration panel."""

        top = tk.Toplevel(self.root)
        top.title(_("Configuration"))

        auto_var = tk.BooleanVar(value=self.auto_select)
        ttk.Checkbutton(
            top, text=_("Automatic model selection"), variable=auto_var
        ).pack(anchor="w", padx=10, pady=5)

        manual_var = tk.StringVar(value=self.backend or "remote")
        manual_frame = ttk.LabelFrame(top, text=_("Manual backend"))
        manual_frame.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(
            manual_frame, text=_("Local"), variable=manual_var, value="local"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            manual_frame, text=_("Remote"), variable=manual_var, value="remote"
        ).pack(side=tk.LEFT, padx=5)

        specs_frame = ttk.LabelFrame(top, text=_("Advanced requirements"))
        specs_frame.pack(fill="x", padx=10, pady=5)
        req_gpu_var = tk.BooleanVar(value=self.model_specs.get("requires_gpu", True))
        ttk.Checkbutton(specs_frame, text=_("Requires GPU"), variable=req_gpu_var).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )

        ttk.Label(specs_frame, text=_("Min VRAM (GB)")).grid(row=1, column=0, sticky="w")
        vram_var = tk.StringVar(
            value=(
                "" if self.model_specs.get("min_vram_gb") is None else str(self.model_specs.get("min_vram_gb"))
            )
        )
        ttk.Entry(specs_frame, textvariable=vram_var, width=7).grid(
            row=1, column=1, sticky="w"
        )

        ttk.Label(specs_frame, text=_("Min RAM (GB)")).grid(row=2, column=0, sticky="w")
        ram_var = tk.StringVar(
            value=(
                "" if self.model_specs.get("min_ram_gb") is None else str(self.model_specs.get("min_ram_gb"))
            )
        )
        ttk.Entry(specs_frame, textvariable=ram_var, width=7).grid(
            row=2, column=1, sticky="w"
        )

        def apply_config() -> None:
            self.auto_select = auto_var.get()
            self.backend = manual_var.get()

            try:
                vram = self._parse_float(vram_var.get(), "Min VRAM")
                ram = self._parse_float(ram_var.get(), "Min RAM")
            except ValueError:
                return

            self.model_specs = {
                "requires_gpu": req_gpu_var.get(),
                "min_vram_gb": vram,
                "min_ram_gb": ram,
            }
            top.destroy()

        ttk.Button(top, text=_("Apply"), command=apply_config).pack(pady=5)

    # --- Guide handling ---------------------------------------------------
    def open_guide(self) -> None:
        """Open the quick-start guide in the selected language."""

        path = self._guide_paths.get(self._lang_var.get())
        if path and path.exists():
            webbrowser.open(path.as_uri())
        else:
            messagebox.showerror("Guide", "Guide not found")

    # --- Finalization -----------------------------------------------------
    def _is_admin(self) -> bool:
        """Return True if running with administrator rights."""

        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:  # pragma: no cover - platform dependent
            # If the API is unavailable (e.g. non-Windows), assume admin.
            return True

    def _run_install_script(self) -> None:
        base = (
            Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent.parent
        )
        script = base / "install" / "install.ps1"
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                "Start-Process PowerShell -Verb RunAs -ArgumentList "
                f"'-ExecutionPolicy Bypass -File \"{script}\"' -Wait"
            ),
        ]
        subprocess.run(cmd, check=True)

    def _finalize(self) -> None:
        self.progress.config(mode="indeterminate")
        self.progress.start()
        self.root.update()
        try:
            if not self._is_admin():
                self.progress.stop()
                self.progress.config(mode="determinate", value=0)
                if messagebox.askyesno(
                    "Installer",
                    "Administrator rights required. Relaunch with elevation?",
                ):
                    params = " ".join(f'"{arg}"' for arg in sys.argv)
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable, params, None, 1
                    )
                return
            self._run_install_script()
            messagebox.showinfo(_("Installer"), _("Setup complete"))
        except Exception as exc:  # pragma: no cover - environment specific
            messagebox.showerror(
                _("Installer"), _("Post-install step failed: {exc}").format(exc=exc)
            )
        finally:
            self.progress.stop()
            self.root.destroy()


def main() -> None:
    gui = GUIInstaller()
    gui.root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
