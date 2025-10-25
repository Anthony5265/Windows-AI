from __future__ import annotations

import os
import sys
import time
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from installer.locales import _
from installer import api_keys, env, model_selector, models, plugins, system_info
from installer.assistant import Assistant, ToolTip


class InstallerGUI:
    """Simple Tkinter-based installer interface."""

    def __init__(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError(
                _("tkinter is not available or no display is found")
            ) from exc
        self.root.title(_("Windows AI Installer"))

        html = self._html_path("chat_ui.html")
        self.window = self._webview.create_window(
            _("Windows AI Installer"), html, width=900, height=700, js_api=self
        )

        # Component selection
        self.registry = plugins.discover_plugins()
        self.component_vars: dict[str, tk.BooleanVar] = {}
        component_frame = tk.LabelFrame(self.root, text=_("Components"))
        component_frame.pack(fill="x", padx=10, pady=5)
        for plugin_name in sorted(self.registry.dependencies.keys()):
            var = tk.BooleanVar(value=True)
            self.component_vars[plugin_name] = var
            ttk.Checkbutton(component_frame, text=plugin_name, variable=var).pack(
                anchor="w"
            )
        if not self.registry.dependencies:
            tk.Label(component_frame, text=_("No plugin dependencies found.")).pack(
                padx=5, pady=5
            )

        # Backend selection
        backend_frame = tk.LabelFrame(self.root, text=_("Model Backend"))
        backend_frame.pack(fill="x", padx=10, pady=5)
        recommended = model_selector.select_backend("default", {})
        self.backend_var = tk.StringVar(value=recommended)
        ttk.Radiobutton(
            backend_frame,
            text=_("Use Local Models"),
            value="local",
            variable=self.backend_var,
        ).pack(anchor="w")
        ttk.Radiobutton(
            backend_frame,
            text=_("Use Remote APIs"),
            value="remote",
            variable=self.backend_var,
        ).pack(anchor="w")
        tk.Label(
            backend_frame,
            text=_("Recommended: {recommended}").format(recommended=recommended),
            justify="left",
        ).pack(anchor="w", padx=5)

        # Model selection
        info = system_info.detect_system()
        model_frame = tk.LabelFrame(self.root, text=_("Models"))
        model_frame.pack(fill="x", padx=10, pady=5)
        self.available_models = models.compatible_models(info)
        if self.available_models:
            names = [m.name for m in self.available_models]
            self.model_var = tk.StringVar(value=names[0])
            ttk.Combobox(
                model_frame,
                textvariable=self.model_var,
                values=names,
                state="readonly",
            ).pack(anchor="w", padx=5, pady=5)
            self.download_btn = ttk.Button(
                model_frame,
                text=_("Download Selected Model"),
                command=self.download_selected_model,
            )
            self.download_btn.pack(anchor="w", padx=5, pady=5)
            ToolTip(self.download_btn, _("Download the chosen model"))
        else:
            tk.Label(
                model_frame, text=_("No compatible models available.")
            ).pack(anchor="w", padx=5, pady=5)

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        self.api_btn = ttk.Button(button_frame, text="Add API Key", command=self.add_api_key)
        self.api_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.api_btn, "Store a service API key")
        api_btn = ttk.Button(
            button_frame, text=_("Add API Key"), command=self.add_api_key
        )
        api_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(api_btn, _("Store a service API key"))
        self.install_btn = ttk.Button(
            button_frame, text=_("Install Selected"), command=self.install_selected
        )
        self.install_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.install_btn, "Install chosen components")
        self.ask_btn = ttk.Button(button_frame, text="Ask Assistant", command=self.ask_assistant)
        self.ask_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.ask_btn, "Chat with the installer assistant")
        self.cancel_btn = ttk.Button(
            button_frame, text="Cancel", command=self.cancel_install, state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.cancel_btn, "Cancel the current installation")
        ToolTip(self.install_btn, _("Install chosen components"))
        ask_btn = ttk.Button(
            button_frame, text=_("Ask Assistant"), command=self.ask_assistant
        )
        ask_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(ask_btn, _("Ask questions or get step-by-step help"))

        # Progress indicator
        self.progress = ttk.Progressbar(self.root, length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)
        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(padx=10)

        self.assistant = Assistant()
        self.cancel_event = threading.Event()

    def run(self) -> None:  # pragma: no cover - thin wrapper
        self.root.mainloop()

    # --- Helpers ---------------------------------------------------------
    def _disable_interaction(self) -> None:
        """Disable all interactive widgets."""

        def disable(widget: tk.Widget) -> None:
            try:
                widget.configure(state=tk.DISABLED)
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                disable(child)

        disable(self.root)

    # --- API keys --------------------------------------------------------
    def add_api_key(self) -> None:
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
        try:
            api_keys.save_key(service, key)
            messagebox.showinfo(
                _("API Key"), _("Saved key for {service}").format(service=service)
            )
        except Exception as exc:  # pragma: no cover - GUI path
            messagebox.showerror(_("API Key"), str(exc))

    # --- Installation -----------------------------------------------------
    def install_selected(self) -> None:
        """Install the components chosen by the user."""

        selected_plugins = [p for p, var in self.component_vars.items() if var.get()]
        if not selected_plugins:
            messagebox.showinfo(_("Install"), _("No components selected"))
            return

        deps_to_check: list[str] = []
        for plugin_name in selected_plugins:
            deps_to_check.extend(self.registry.dependencies.get(plugin_name, []))
        missing = self.assistant.check_dependencies(deps_to_check)
        if missing:
            msg = _("Missing dependencies: {deps}").format(
                deps=", ".join(missing)
            )
            self.assistant.speak(msg)
            messagebox.showinfo(_("Dependencies"), msg)

        # Prompt for API key before installation
        service = simpledialog.askstring(
            _("API Key"),
            _("Service requiring key (leave blank to skip):"),
            parent=self.root,
        )
        if service:
            key = simpledialog.askstring(
                _("API Key"),
                _("Enter API key for {service}:").format(service=service),
                show="*",
                parent=self.root,
            )
            if key:
                try:
                    api_keys.save_key(service, key)
                    messagebox.showinfo(
                        _("API Key"),
                        _("Saved key for {service}").format(service=service),
                    )
                except Exception as exc:  # pragma: no cover - GUI path
                    messagebox.showerror(_("API Key"), str(exc))

        self.install_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress.config(maximum=len(selected_plugins), value=0)
        self.cancel_event.clear()
        threading.Thread(
            target=self._run_install, args=(selected_plugins,), daemon=True
        ).start()

    def cancel_install(self) -> None:
        self.cancel_event.set()
        self.cancel_btn.config(state=tk.DISABLED)
        self._disable_interaction()

    def _run_install(self, selected_plugins: list[str]) -> None:
        """Background worker that performs the actual installation."""

        completed: list[str] = []
        try:
            for plugin_name in selected_plugins:
                if self.cancel_event.is_set():
                    break
                env_path = env.create_env(plugin_name)
                deps = self.registry.dependencies.get(plugin_name, [])
                env.install_packages(env_path, deps)
                completed.append(plugin_name)
                self.root.after(0, self.progress.step, 1)
            if self.cancel_event.is_set():
                remaining = [p for p in selected_plugins if p not in completed]
                self.root.after(0, self._install_cancelled, completed, remaining)
            else:
                self.root.after(0, self._install_complete, None)
        except Exception as exc:  # pragma: no cover - subprocess path
            self.root.after(0, self._install_complete, exc)

    def _install_complete(self, error: Exception | None) -> None:
        """Handle completion of the install worker."""

        self.install_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        if error:
            messagebox.showerror(
                _("Install"), _("Install failed: {error}").format(error=error)
            )
            return

        # Offer to launch the Control Center after a successful install
        if messagebox.askyesno(
            _("Install"),
            _("Installation complete. Launch Control Center now?"),
        ):
            try:
                from control_center.gui import main as launch_gui

                self.root.destroy()
                launch_gui()
            except Exception as exc:  # pragma: no cover - runtime path
                messagebox.showerror(
                    _("Control Center"),
                    _("Failed to launch: {exc}").format(exc=exc),
                )

    def _install_cancelled(self, completed: list[str], remaining: list[str]) -> None:
        """Show summary when installation is cancelled."""

        summary = (
            _("Installation cancelled.\nInstalled: {done}\nSkipped: {skipped}").format(
                done=", ".join(completed) or _("none"),
                skipped=", ".join(remaining) or _("none"),
            )
        )
        messagebox.showinfo(_("Install"), summary)

    # --- Model downloads -------------------------------------------------
    def download_selected_model(self) -> None:
        """Download the model chosen in the combo box."""

        model_name = getattr(self, "model_var", None)
        if not model_name:
            return
        model_name = self.model_var.get()
        dest = filedialog.askdirectory(title=_("Select download directory")) or "."
        self.download_btn.config(state=tk.DISABLED)
        self.progress.config(mode="determinate", maximum=100, value=0)
        start = time.monotonic()

        start = time.monotonic()

        def progress(downloaded: int, total: int) -> None:
            percent = int(downloaded / total * 100) if total else 0
            elapsed = time.monotonic() - start
            mb_downloaded = downloaded / 1_048_576
            mb_total = total / 1_048_576 if total else 0
            speed = mb_downloaded / elapsed if elapsed else 0

            def update() -> None:
                self.progress.config(value=percent)
                self.progress_label.config(
                    text=f"{mb_downloaded:.1f} / {mb_total:.1f} MB ({speed:.1f} MB/s)"
                )
            speed = (downloaded / 1024 / 1024) / elapsed if elapsed > 0 else 0
            downloaded_mb = downloaded / 1024 / 1024
            total_mb = total / 1024 / 1024 if total else 0
            label = f"{downloaded_mb:.1f} / {total_mb:.1f} MB ({speed:.1f} MB/s)"

            def update() -> None:
                self.progress.config(value=percent)
                self.progress_label.config(text=label)

            self.root.after(0, update)

        def worker() -> None:
            try:
                models.download_model(model_name, dest, progress)
                self.root.after(
                    0, lambda: messagebox.showinfo("Download", "Model downloaded")
                    0,
                    lambda: messagebox.showinfo(
                        _("Download"), _("Model downloaded")
                    ),
                )
            except Exception as exc:  # pragma: no cover - network path
                self.root.after(
                    0, lambda: messagebox.showerror(_("Download"), str(exc))
                )
            finally:
                self.root.after(0, self._download_complete)

        threading.Thread(target=worker, daemon=True).start()

    def _download_complete(self) -> None:
        self.download_btn.config(state=tk.NORMAL)
        self.progress.config(value=0)

    # --- Assistant -------------------------------------------------------
    def ask_assistant(self) -> None:  # pragma: no cover - GUI path
        pass
    def ask_assistant(self) -> None:
        """Open a simple chat window with the assistant."""

        if getattr(self, "chat_win", None) and self.chat_win.winfo_exists():
            self.chat_win.lift()
            return

        self.chat_win = tk.Toplevel(self.root)
        self.chat_win.title(_("Assistant"))

        self.chat_log = tk.Text(self.chat_win, state="disabled", width=60, height=15, wrap="word")
        self.chat_log.pack(padx=5, pady=5, fill="both", expand=True)

        entry_frame = tk.Frame(self.chat_win)
        entry_frame.pack(fill="x", padx=5, pady=5)
        self.chat_entry = tk.Entry(entry_frame)
        self.chat_entry.pack(side=tk.LEFT, fill="x", expand=True)
        send_btn = ttk.Button(entry_frame, text=_("Send"), command=self.send_chat)
        send_btn.pack(side=tk.LEFT, padx=5)

    def send_chat(self) -> None:  # pragma: no cover - GUI path
        pass

    def _append_chat(self, text: str) -> None:  # pragma: no cover - GUI path
        pass
        question = self.chat_entry.get().strip()
        if not question:
            return
        self.chat_entry.delete(0, tk.END)
        self._append_chat(
            f"{_('User')}: {question}\n{_('Assistant')}: "
        )

        def worker() -> None:
            parts: list[str] = []
            try:
                for token in self.assistant.answer_stream(question):
                    parts.append(token)
                    self.root.after(0, self._append_chat, token)
            except Exception as exc:
                msg = f"[error: {exc}]"
                parts.append(msg)
                self.root.after(0, self._append_chat, msg)
            finally:
                reply = "".join(parts)
                self.assistant.speak(reply)
                self.root.after(0, self._append_chat, "\n")

        threading.Thread(target=worker, daemon=True).start()

    def _append_chat(self, text: str) -> None:
        if not hasattr(self, "chat_log"):
            return
        self.chat_log.config(state="normal")
        self.chat_log.insert("end", text)
        self.chat_log.see("end")
        self.chat_log.config(state="disabled")


def main() -> None:  # pragma: no cover - thin wrapper
    InstallerGUI().run()


if __name__ == "__main__":  # pragma: no cover
    main()
