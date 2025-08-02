from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from . import api_keys, env, model_selector, plugins, system_info


class InstallerGUI:
    """Tkinter-based interface for the Windows AI installer.

    The GUI mirrors the flow described in ``docs/Smart-Installer.md``:
    1. System scan
    2. Component selection
    3. API-key prompts
    4. Progress indicators
    """

    def __init__(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError("tkinter is not available or no display is found") from exc

        self.root.title("Windows AI Installer")

        # System scan
        info = system_info.detect_system()
        info_lines = [f"{k}: {v}" for k, v in info.items()]
        tk.Label(self.root, text="\n".join(info_lines), justify="left").pack(
            padx=10, pady=10
        )

        # Component selection
        self.registry = plugins.discover_plugins()
        self.component_vars: dict[str, tk.BooleanVar] = {}
        component_frame = tk.LabelFrame(self.root, text="Components")
        component_frame.pack(fill="x", padx=10, pady=5)
        for plugin_name in sorted(self.registry.dependencies.keys()):
            var = tk.BooleanVar(value=True)
            self.component_vars[plugin_name] = var
            ttk.Checkbutton(component_frame, text=plugin_name, variable=var).pack(
                anchor="w"
            )
        if not self.registry.dependencies:
            tk.Label(component_frame, text="No plugin dependencies found.").pack(
                padx=5, pady=5
            )

        # Backend selection
        backend_frame = tk.LabelFrame(self.root, text="Model Backend")
        backend_frame.pack(fill="x", padx=10, pady=5)
        recommended = model_selector.select_backend("default", {})
        self.backend_var = tk.StringVar(value=recommended)
        ttk.Radiobutton(
            backend_frame,
            text="Use Local Models",
            value="local",
            variable=self.backend_var,
        ).pack(anchor="w")
        ttk.Radiobutton(
            backend_frame,
            text="Use Remote APIs",
            value="remote",
            variable=self.backend_var,
        ).pack(anchor="w")
        tk.Label(
            backend_frame, text=f"Recommended: {recommended}", justify="left"
        ).pack(anchor="w", padx=5)

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Add API Key", command=self.add_api_key).pack(
            side=tk.LEFT, padx=5
        )
        self.install_btn = ttk.Button(
            button_frame, text="Install Selected", command=self.install_selected
        )
        self.install_btn.pack(side=tk.LEFT, padx=5)

        # Progress indicator
        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)

    # --- API key handling -------------------------------------------------
    def add_api_key(self) -> None:
        """Prompt the user to store an API key."""

        service = simpledialog.askstring("API Key", "Service name:", parent=self.root)
        if not service:
            return
        key = simpledialog.askstring(
            "API Key", f"Enter API key for {service}:", show="*", parent=self.root
        )
        if not key:
            return
        try:
            api_keys.save_key(service, key)
            messagebox.showinfo("API Key", f"Saved key for {service}")
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror("API Key", str(exc))

    # --- Installation -----------------------------------------------------
    def install_selected(self) -> None:
        """Install the components chosen by the user."""

        selected_plugins = [p for p, var in self.component_vars.items() if var.get()]
        if not selected_plugins:
            messagebox.showinfo("Install", "No components selected")
            return

        # Allow user override of the model backend
        backend = self.backend_var.get()
        print(f"Backend chosen: {backend}")

        # Prompt for API key before installation
        service = simpledialog.askstring(
            "API Key", "Service requiring key (leave blank to skip):", parent=self.root
        )
        if service:
            key = simpledialog.askstring(
                "API Key", f"Enter API key for {service}:", show="*", parent=self.root
            )
            if key:
                try:
                    api_keys.save_key(service, key)
                    messagebox.showinfo("API Key", f"Saved key for {service}")
                except Exception as exc:  # pragma: no cover - GUI path
                    messagebox.showerror("API Key", str(exc))

        self.install_btn.config(state=tk.DISABLED)
        self.progress.config(maximum=len(selected_plugins))
        threading.Thread(
            target=self._run_install, args=(selected_plugins,), daemon=True
        ).start()

    def _run_install(self, selected_plugins: list[str]) -> None:
        """Background worker that performs the actual installation."""

        try:
            for plugin_name in selected_plugins:
                env_path = env.create_env(plugin_name)
                deps = self.registry.dependencies.get(plugin_name, [])
                env.install_packages(env_path, deps)
                self.root.after(0, self.progress.step, 1)
            # Signal successful completion
            self.root.after(0, self._install_complete, None)
        except Exception as exc:  # pragma: no cover - subprocess path
            # Pass the exception to the main thread for display
            self.root.after(0, self._install_complete, exc)

    def _install_complete(self, error: Exception | None) -> None:
        """Handle completion of the install worker."""

        self.install_btn.config(state=tk.NORMAL)
        if error:
            messagebox.showerror("Install", f"Install failed: {error}")
            return

        # Offer to launch the Control Center after a successful install
        if messagebox.askyesno(
            "Install", "Installation complete. Launch Control Center now?"
        ):
            try:
                from control_center.gui import main as launch_gui

                self.root.destroy()
                launch_gui()
            except Exception as exc:  # pragma: no cover - runtime path
                messagebox.showerror("Control Center", f"Failed to launch: {exc}")


def main() -> None:
    gui = InstallerGUI()
    gui.root.mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()
