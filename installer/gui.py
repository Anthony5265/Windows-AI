from __future__ import annotations

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

if __package__ is None or __package__ == "":  # pragma: no cover - script entry
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from installer import api_keys, env, model_selector, models, plugins, system_info
from installer.assistant import Assistant, ToolTip


class InstallerGUI:
    """Web-based installer interface using PyWebView.

    The interface renders a React component that mimics ChatGPT's chat layout.
    Themes are managed through :class:`ui.themes.ThemeManager` and exposed to
    the JavaScript side via the PyWebView API.
    """

    def __init__(self) -> None:
        try:
            import webview  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("pywebview is required to launch the installer") from exc

        self._webview = webview
        self.themes = ThemeManager()
        # Provide basic light and dark themes
        self.themes.add_theme(Theme(name="light", background="#ffffff", foreground="#000000"))
        self.themes.add_theme(Theme(name="dark", background="#000000", foreground="#ffffff"))
        self._theme = self.themes.get_theme("light")  # default theme

        html = self._html_path("chat_ui.html")
        self.window = self._webview.create_window(
            "Windows AI Installer", html, width=900, height=700, js_api=self
        )

    # ------------------------------------------------------------------ HTML
    def _html_path(self, name: str) -> str:
        """Return absolute path to ``installer/web/<name>``."""

        return str(Path(__file__).with_name("web") / name)

    # ------------------------------------------------------------------ Theme API
    def get_theme(self) -> dict:
        """Return the currently selected theme as a JSON-serialisable dict."""

        assert self._theme is not None
        return {
            "name": self._theme.name,
            "background": self._theme.background,
            "foreground": self._theme.foreground,
        }

        # Progress indicator
        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)
        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(padx=10)

        theme = self.themes.get_theme(name)
        if theme is None:
            raise ValueError(f"Unknown theme: {name}")
        self._theme = theme
        return self.get_theme()

    # ------------------------------------------------------------------ Runner
    def run(self) -> None:
        """Start the PyWebView event loop."""

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

        # Warn about missing dependencies before starting
        deps_to_check: list[str] = []
        for plugin_name in selected_plugins:
            deps_to_check.extend(self.registry.dependencies.get(plugin_name, []))
        missing = self.assistant.check_dependencies(deps_to_check)
        if missing:
            msg = "Missing dependencies: " + ", ".join(missing)
            self.assistant.speak(msg)
            messagebox.showinfo("Dependencies", msg)

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

    # --- Model downloads -------------------------------------------------
    def download_selected_model(self) -> None:
        """Download the model chosen in the combo box."""

        model_name = getattr(self, "model_var", None)
        if not model_name:
            return
        model_name = self.model_var.get()
        dest = filedialog.askdirectory(title="Select download directory") or "."
        self.download_btn.config(state=tk.DISABLED)
        self.progress.config(mode="determinate", maximum=100, value=0)

        start_time = time.monotonic()

        def progress(downloaded: int, total: int) -> None:
            percent = int(downloaded / total * 100) if total else 0
            elapsed = time.monotonic() - start_time
            speed = downloaded / 1048576 / elapsed if elapsed else 0
            downloaded_mb = downloaded / 1048576
            total_mb = total / 1048576 if total else 0

            def update() -> None:
                self.progress.config(value=percent)
                self.progress_label.config(
                    text=f"{downloaded_mb:.1f} / {total_mb:.1f} MB ({speed:.1f} MB/s)"
                )

            self.root.after(0, update)

        def worker() -> None:
            try:
                models.download_model(model_name, dest, progress)
                self.root.after(0, lambda: messagebox.showinfo("Download", "Model downloaded"))
            except Exception as exc:  # pragma: no cover - network path
                self.root.after(0, lambda: messagebox.showerror("Download", str(exc)))
            finally:
                self.root.after(0, self._download_complete)

        threading.Thread(target=worker, daemon=True).start()

    def _download_complete(self) -> None:
        self.download_btn.config(state=tk.NORMAL)
        self.progress.config(value=0)

    # --- Assistant -------------------------------------------------------
    def ask_assistant(self) -> None:
        """Prompt the user for a question and show the assistant's reply."""

        question = simpledialog.askstring("Assistant", "How can I help?", parent=self.root)
        if not question:
            return
        reply = self.assistant.answer(question)
        self.assistant.speak(reply)
        messagebox.showinfo("Assistant", reply)


def main() -> None:  # pragma: no cover - thin wrapper
    InstallerGUI().run()


if __name__ == "__main__":  # pragma: no cover
    main()
