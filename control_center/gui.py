"""Tkinter-based chat interface for the Windows AI Control Center.

The GUI presents a minimal chat window and a backend selector allowing users
to switch between local models and remote APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Callable

try:  # pragma: no cover - import may fail on headless systems
    import tkinter as tk  # type: ignore
    from tkinter import ttk, messagebox  # type: ignore
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]

from .backends import Backend, LocalBackend, RemoteBackend
from . import get_plugins
from mesh import MeshNode
from iot import ADAPTERS, discover_devices, pair_device
from secrets import token_urlsafe
from windows_ai.core.plugin_manager import PluginManager
from security import AuditLogger, PermissionManager
from optimization import tuning
from eco.scheduler import EcoScheduler
from eco.monitor import EcoMonitor
from eco.tracker import PowerInfo
from updater import Updater
from installer import snapshot

try:  # pragma: no cover - optional dependency
    import qrcode  # type: ignore
except Exception:  # pragma: no cover
    qrcode = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import speech_recognition as sr  # type: ignore
except Exception:  # pragma: no cover
    sr = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover
    pyttsx3 = None  # type: ignore[assignment]

__all__ = ["ChatGUI", "DashboardManager", "main"]


# ---------------------------------------------------------------- Dashboards
@dataclass
class Dashboard:
    name: str
    owner: str
    roles: Dict[str, str] = field(default_factory=dict)


class DashboardManager:
    """Manage shared dashboards with simple role-based access control."""

    def __init__(self) -> None:
        self.dashboards: Dict[str, Dashboard] = {}

    def create(self, name: str, owner: str) -> None:
        dash = Dashboard(name, owner, {owner: "owner"})
        self.dashboards[name] = dash

    def share(self, name: str, user: str, role: str) -> None:
        if name not in self.dashboards:
            raise KeyError(f"Unknown dashboard {name}")
        self.dashboards[name].roles[user] = role

    def can_access(self, name: str, user: str, role: str) -> bool:
        dash = self.dashboards.get(name)
        if not dash:
            return False
        current = dash.roles.get(user)
        if current == "owner":
            return True
        if current == "edit":
            return role in {"edit", "view"}
        if current == "view":
            return role == "view"
        return False


class ChatGUI:
    """Simple chat window that can switch between multiple backends."""

    def __init__(
        self,
        root: Optional["tk.Tk"] = None,
        backends: Optional[Dict[str, Backend]] = None,
        scheduler: Optional[EcoScheduler] = None,
        monitor: Optional[EcoMonitor] = None,
    ) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("tkinter is not available")
        try:
            self.root = root or tk.Tk()
        except tk.TclError as exc:  # pragma: no cover - environment specific
            raise RuntimeError("tkinter is not available or no display is found") from exc

        self.root.title("Windows AI Control Center")
        self.backends = backends or {
            "Local": LocalBackend(),
            "Remote": RemoteBackend(),
        }
        self.backend_var = tk.StringVar(value=next(iter(self.backends)))
        self.mesh_node: MeshNode | None = None
        # Sync settings
        self.sync_frequency = 60  # minutes
        self.conflict_resolution = "ask"
        # Security
        self.audit_logger = AuditLogger()
        self.permission_manager = PermissionManager(audit_logger=self.audit_logger)
        prompt_cb = permission_prompt or (lambda _p, _perm: True)
        self.permission_manager.prompt("control_center", "network", prompt_cb)
        self.dashboard_manager = DashboardManager()
        self.scheduler = scheduler or EcoScheduler()
        self.eco_monitor = monitor or EcoMonitor(scheduler=self.scheduler)
        self.updater = Updater()

        # Accessibility
        acc = self._detect_accessibility()
        self.screen_reader_enabled = acc.get("screen_reader", False)
        self.high_contrast_enabled = acc.get("high_contrast", False)
        self.speech_enabled = False
        self._tts = pyttsx3.init() if pyttsx3 else None
        self._recognizer = sr.Recognizer() if sr else None
        self._mic = sr.Microphone() if sr else None
        self._sr_thread: threading.Thread | None = None

        self._build_widgets()

        if self.high_contrast_enabled:
            self._apply_high_contrast()

        # Allow external plugins to modify the GUI
        for plugin in get_plugins():  # pragma: no cover - runtime hook
            plugin.register(self)

    # ------------------------------------------------------------------ UI
    def _build_widgets(self) -> None:
        """Create the base widgets."""

        chat_frame = ttk.Frame(self.root)
        chat_frame.pack(fill="both", expand=True)

        self.chat = tk.Text(chat_frame, wrap="word", state="normal", height=20)
        self.chat.pack(fill="both", expand=True, padx=5, pady=5)

        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="Backend:").pack(side="left", padx=5)
        selector = ttk.Combobox(
            input_frame,
            textvariable=self.backend_var,
            values=list(self.backends.keys()),
            state="readonly",
            width=10,
        )
        selector.pack(side="left")

        ttk.Label(input_frame, text="Profile:").pack(side="left", padx=5)
        self.profile_var = tk.StringVar(value="balanced")
        profile_selector = ttk.Combobox(
            input_frame,
            textvariable=self.profile_var,
            values=list(tuning.PROFILES),
            state="readonly",
            width=12,
        )
        profile_selector.pack(side="left")
        ttk.Button(input_frame, text="Apply", command=self.apply_profile).pack(
            side="left", padx=5
        )
        ttk.Button(input_frame, text="Revert", command=self.revert_profile).pack(
            side="left", padx=5
        )

        self.entry = ttk.Entry(input_frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<Return>", self.send_message)

        ttk.Button(input_frame, text="Send", command=self.send_message).pack(
            side="left", padx=5
        )
        ttk.Button(input_frame, text="Mesh", command=self._open_mesh_config).pack(
            side="left", padx=5
        )
        # IoT management
        ttk.Button(input_frame, text="IoT", command=self._open_iot_dialog).pack(
            side="left", padx=5
        )
        ttk.Button(
            input_frame, text="Pair Mobile", command=self._open_mobile_pair_window
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Sync Settings", command=self._open_sync_settings
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Plugins", command=self._open_plugin_marketplace
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Permissions", command=self._open_plugin_permissions
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Logs", command=self._open_audit_log
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Automation", command=self._open_automation_builder
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Defer", command=self.schedule_message
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Eco", command=self._open_eco_settings
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Scheduler", command=self._open_scheduler_settings
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Updates", command=self._open_update_settings
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Snapshot", command=self._create_snapshot
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Restore", command=self._restore_snapshot
        ).pack(side="left", padx=5)
        ttk.Button(
            input_frame, text="Accessibility", command=self._open_accessibility_settings
        ).pack(side="left", padx=5)

    def _create_snapshot(self) -> None:
        """Create a system snapshot for later restoration."""
        snapshot.create_snapshot()
        self.chat.insert("end", "[Snapshot] Created\n")
        self.chat.see("end")

    def _restore_snapshot(self) -> None:
        """Restore the previously recorded snapshot."""
        snapshot.restore()
        self.chat.insert("end", "[Snapshot] Restored\n")
        self.chat.see("end")

    def apply_profile(self) -> None:
        """Apply the selected optimization profile."""
        profile = self.profile_var.get()
        tuning.apply(profile)
        self.chat.insert("end", f"[Optimization] Applied {profile} profile\n")
        self.chat.see("end")

    def revert_profile(self) -> None:
        """Revert to the previous optimization profile."""
        tuning.revert()
        self.chat.insert("end", "[Optimization] Reverted profile\n")
        self.chat.see("end")

    # -------------------------------------------------------- Accessibility
    def _detect_accessibility(self) -> Dict[str, bool]:
        """Inspect basic Windows accessibility settings."""
        info = {"screen_reader": False, "high_contrast": False}
        if platform.system() == "Windows":  # pragma: no cover - OS dependent
            try:
                import ctypes

                SPI_GETSCREENREADER = 70
                SPI_GETHIGHCONTRAST = 67

                flag = ctypes.c_int()
                if ctypes.windll.user32.SystemParametersInfoW(
                    SPI_GETSCREENREADER, 0, ctypes.byref(flag), 0
                ):
                    info["screen_reader"] = bool(flag.value)

                class HIGHCONTRAST(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", ctypes.c_uint),
                        ("dwFlags", ctypes.c_uint),
                        ("lpszDefaultScheme", ctypes.c_wchar_p),
                    ]

                hc = HIGHCONTRAST()
                hc.cbSize = ctypes.sizeof(HIGHCONTRAST)
                if ctypes.windll.user32.SystemParametersInfoW(
                    SPI_GETHIGHCONTRAST, hc.cbSize, ctypes.byref(hc), 0
                ):
                    info["high_contrast"] = bool(hc.dwFlags & 1)
            except Exception:
                pass
        return info

    def _apply_high_contrast(self) -> None:
        """Apply a minimal high contrast theme to the chat widgets."""
        self.root.configure(bg="black")
        self.chat.configure(bg="black", fg="white")
        self.entry.configure(bg="black", fg="white", insertbackground="white")

    def _speak(self, text: str) -> None:
        """Speak text when screen reader mode is enabled."""
        if self.screen_reader_enabled and self._tts:
            threading.Thread(
                target=lambda: (self._tts.say(text), self._tts.runAndWait()),
                daemon=True,
            ).start()

    def _listen_loop(self) -> None:
        """Background speech recognition loop."""
        if not (self._recognizer and self._mic):
            return
        while self.speech_enabled:
            with self._mic as source:
                audio = self._recognizer.listen(source)
            try:
                text = self._recognizer.recognize_google(audio)
            except Exception:
                text = ""
            if text:
                self.entry.insert("end", text + " ")

    def _toggle_speech_recognition(self) -> None:
        """Start or stop the speech recognition loop."""
        if not self._recognizer or not self._mic:
            return
        self.speech_enabled = not self.speech_enabled
        if self.speech_enabled:
            self._sr_thread = threading.Thread(
                target=self._listen_loop, daemon=True
            )
            self._sr_thread.start()

    def _open_accessibility_settings(self) -> None:
        """Allow enabling speech recognition and screen reader hooks."""
        win = tk.Toplevel(self.root)
        win.title("Accessibility")

        sr_var = tk.BooleanVar(value=self.screen_reader_enabled)
        sp_var = tk.BooleanVar(value=self.speech_enabled)
        hc_var = tk.BooleanVar(value=self.high_contrast_enabled)

        ttk.Checkbutton(win, text="Screen reader", variable=sr_var).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Checkbutton(win, text="Speech input", variable=sp_var).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Checkbutton(win, text="High contrast", variable=hc_var).grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )

        def save() -> None:
            self.screen_reader_enabled = sr_var.get()
            if self.speech_enabled != sp_var.get():
                self._toggle_speech_recognition()
            self.high_contrast_enabled = hc_var.get()
            if self.high_contrast_enabled:
                self._apply_high_contrast()
            else:
                # simple reset by recreating widgets' colors
                self.root.configure(bg="SystemButtonFace")
                self.chat.configure(bg="white", fg="black")
                self.entry.configure(bg="white", fg="black", insertbackground="black")
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=3, column=0, padx=5, pady=5, sticky="e"
        )

    # ------------------------------------------------------------- Scheduling
    def schedule_message(self) -> None:
        """Schedule the current entry text for the next off-peak window."""

        prompt = self.entry.get().strip()
        if not prompt:
            return
        backend = self.backends[self.backend_var.get()]

        def run() -> None:
            response = backend.generate(prompt)
            self.chat.insert("end", f"[Off-peak] Bot: {response}\n")
            self.chat.see("end")
            self._speak(f"Bot: {response}")

        self.scheduler.schedule(run)
        self.chat.insert("end", f"[Scheduled] {prompt}\n")
        self.chat.see("end")
        self._speak(f"Scheduled {prompt}")
        self.entry.delete(0, "end")

    def _open_scheduler_settings(self) -> None:
        """Configure off-peak hours for deferred tasks."""

        win = tk.Toplevel(self.root)
        win.title("Scheduler")
        start_var = tk.IntVar(value=self.scheduler.start_hour)
        end_var = tk.IntVar(value=self.scheduler.end_hour)

        ttk.Label(win, text="Start hour:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(win, textvariable=start_var, width=5).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(win, text="End hour:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(win, textvariable=end_var, width=5).grid(row=1, column=1, padx=5, pady=5)

        def save() -> None:
            self.scheduler.start_hour = start_var.get()
            self.scheduler.end_hour = end_var.get()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=2, column=0, columnspan=2, pady=5
        )

    def _open_eco_settings(self) -> None:
        """Show current energy usage and scheduler options."""

        win = tk.Toplevel(self.root)
        win.title("Eco Settings")

        def fmt(info: PowerInfo) -> str:
            percent = f"{info.percent:.0f}%" if info.percent is not None else "n/a"
            if info.secs_left is None or info.secs_left < 0:
                left = "n/a"
            else:
                left = f"{info.secs_left // 60}m"
            plugged = (
                "yes"
                if info.power_plugged
                else "no" if info.power_plugged is not None else "n/a"
            )
            return f"Battery: {percent}\nTime left: {left}\nPlugged in: {plugged}"

        label = ttk.Label(win, text=fmt(self.eco_monitor.sample()), justify="left")
        label.pack(padx=5, pady=5)

        def refresh() -> None:
            label.config(text=fmt(self.eco_monitor.sample()))

        ttk.Button(win, text="Refresh", command=refresh).pack(pady=5)
        ttk.Button(win, text="Scheduler", command=self._open_scheduler_settings).pack(
            pady=5
        )

    def _open_update_settings(self) -> None:
        """Simple update window showing release notes."""

        win = tk.Toplevel(self.root)
        win.title("Updates")
        ttk.Button(win, text="Check", command=self._check_updates).pack(
            padx=5, pady=5
        )
        self._release_notes = tk.Text(win, height=10, width=60, state="disabled")
        self._release_notes.pack(fill="both", expand=True, padx=5, pady=5)

    def _check_updates(self) -> None:
        version = self.updater.latest_version()
        notes = self.updater.get_release_notes(version)
        self._release_notes.config(state="normal")
        self._release_notes.delete("1.0", "end")
        self._release_notes.insert(
            "1.0", f"Latest version: {version}\n\n{notes}".strip()
        )
        self._release_notes.config(state="disabled")

    # ---------------------------------------------------------- Dashboards API
    def create_dashboard(self, name: str, owner: str) -> None:
        self.dashboard_manager.create(name, owner)

    def share_dashboard(self, name: str, user: str, role: str) -> None:
        self.dashboard_manager.share(name, user, role)

    def can_access_dashboard(self, name: str, user: str, role: str) -> bool:
        return self.dashboard_manager.can_access(name, user, role)

    # ----------------------------------------------------------------- Chat
    def _open_mesh_config(self) -> None:
        """Open a simple window to configure mesh networking."""

        win = tk.Toplevel(self.root)
        win.title("Mesh Configuration")
        host_var = tk.StringVar(value="127.0.0.1")
        port_var = tk.StringVar(value="0")

        ttk.Label(win, text="Hub host:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(win, textvariable=host_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(win, text="Hub port:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(win, textvariable=port_var).grid(row=1, column=1, padx=5, pady=5)

        def connect() -> None:
            if self.mesh_node:
                self.mesh_node.stop()
            def handler(task: str) -> None:
                self.chat.insert("end", f"[Mesh] {task}\n")
                self.chat.see("end")
            self.mesh_node = MeshNode(handler)
            self.mesh_node.connect((host_var.get(), int(port_var.get())))

        ttk.Button(win, text="Connect", command=connect).grid(
            row=2, column=0, columnspan=2, pady=5
        )

    # ----------------------------------------------------------------- Chat
    def _open_iot_dialog(self) -> None:
        """Open a dialog for device discovery and pairing."""

        win = tk.Toplevel(self.root)
        win.title("Device Discovery")

        proto_var = tk.StringVar(value=next(iter(ADAPTERS)))
        ttk.Label(win, text="Protocol:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(
            win,
            textvariable=proto_var,
            values=list(ADAPTERS.keys()),
            state="readonly",
        ).grid(row=0, column=1, padx=5, pady=5)

        listbox = tk.Listbox(win, height=6)
        listbox.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        win.rowconfigure(1, weight=1)
        win.columnconfigure(1, weight=1)

        def do_discover() -> None:
            devices = discover_devices(proto_var.get())
            listbox.delete(0, "end")
            for dev in devices:
                listbox.insert("end", f"{dev.id}: {dev.name}")

        def do_pair() -> None:
            if not listbox.curselection():
                return
            item = listbox.get(listbox.curselection()[0])
            device_id = item.split(":", 1)[0]
            protocol = proto_var.get()
            for dev in discover_devices(protocol):
                if dev.id == device_id:
                    if pair_device(protocol, dev):
                        self.chat.insert("end", f"[IoT] Paired {dev.name}\n")
                        self.chat.see("end")
                    break

        ttk.Button(win, text="Discover", command=do_discover).grid(
            row=2, column=0, padx=5, pady=5, sticky="ew"
        )
        ttk.Button(win, text="Pair", command=do_pair).grid(
            row=2, column=1, padx=5, pady=5, sticky="ew"
        )

    # ----------------------------------------------------------- Mobile Pairing
    def _open_mobile_pair_window(self) -> None:
        """Display a pairing token and optional QR code."""

        win = tk.Toplevel(self.root)
        win.title("Mobile Pairing")
        token = token_urlsafe(8)
        if qrcode:
            qr = qrcode.QRCode(border=1)
            qr.add_data(token)
            qr.make(fit=True)
            ascii_qr = "\n".join(
                "".join("██" if cell else "  " for cell in row) for row in qr.get_matrix()
            )
            tk.Label(win, font=("Courier", 1), text=ascii_qr).pack(padx=5, pady=5)
        elif messagebox:
            messagebox.showwarning(
                "Mobile Pairing",
                "Install 'qrcode' to enable QR-code display.",
            )
        ttk.Label(win, text=f"Token: {token}").pack(padx=5, pady=5)

    # -------------------------------------------------------------- Marketplace
    def _open_plugin_marketplace(self) -> None:
        """Simple plugin marketplace for browsing and installing plugins."""

        pm = PluginManager()
        win = tk.Toplevel(self.root)
        win.title("Plugin Marketplace")

        tree = ttk.Treeview(win, columns=("description", "rating"), show="headings")
        tree.heading("description", text="Description")
        tree.heading("rating", text="Rating")
        for plugin in pm.plugins:
            tree.insert(
                "",
                "end",
                iid=plugin.name,
                values=(plugin.description, plugin.rating or "-"),
            )
        tree.pack(fill="both", expand=True, padx=5, pady=5)

        def install() -> None:
            for sel in tree.selection():
                plugin = pm.get_plugin(sel)
                if plugin:
                    pm.install(plugin)

        def update() -> None:
            # For now update simply reinstalls the plugin
            install()

        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Install", command=install).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Update", command=update).pack(side="left", padx=5)

    # ----------------------------------------------------------- Permissions
    def _open_plugin_permissions(self) -> None:
        """Configure permissions for individual plugins."""

        pm = PluginManager()
        win = tk.Toplevel(self.root)
        win.title("Plugin Permissions")

        listbox = tk.Listbox(win, height=6)
        listbox.pack(side="left", fill="y", padx=5, pady=5)
        for plugin in pm.plugins:
            listbox.insert("end", plugin.name)

        check_frame = ttk.Frame(win)
        check_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        network_var = tk.BooleanVar()
        fs_var = tk.BooleanVar()
        ttk.Checkbutton(check_frame, text="Network", variable=network_var).pack(anchor="w")
        ttk.Checkbutton(check_frame, text="Filesystem", variable=fs_var).pack(anchor="w")

        def update_checks(event: object | None = None) -> None:
            if not listbox.curselection():
                return
            name = listbox.get(listbox.curselection()[0])
            perms = self.permission_manager.permissions.get(name, set())
            network_var.set("network" in perms)
            fs_var.set("filesystem" in perms)

        def save() -> None:
            if not listbox.curselection():
                return
            name = listbox.get(listbox.curselection()[0])
            if network_var.get():
                self.permission_manager.grant(name, "network")
            else:
                self.permission_manager.revoke(name, "network")
            if fs_var.get():
                self.permission_manager.grant(name, "filesystem")
            else:
                self.permission_manager.revoke(name, "filesystem")

        listbox.bind("<<ListboxSelect>>", update_checks)
        ttk.Button(check_frame, text="Save", command=save).pack(pady=5)

    # --------------------------------------------------------------- Log view
    def _open_audit_log(self) -> None:
        """Display the contents of the audit log."""

        win = tk.Toplevel(self.root)
        win.title("Audit Log")
        text = tk.Text(win, wrap="word", height=20, width=80)
        text.pack(fill="both", expand=True, padx=5, pady=5)
        text.insert("end", self.audit_logger.read())
        text.config(state="disabled")

    def _open_automation_builder(self) -> None:
        """Launch the workflow builder."""

        from automation.builder import WorkflowBuilder

        backend = self.backends[self.backend_var.get()]
        WorkflowBuilder(backend=backend)

    # ----------------------------------------------------------------- Chat
    def send_message(self, event: object | None = None) -> None:
        """Handle user input and display backend response."""

        prompt = self.entry.get().strip()
        if not prompt:
            return
        self.chat.insert("end", f"You: {prompt}\n")
        self._speak(f"You: {prompt}")
        self.entry.delete(0, "end")
        backend = self.backends[self.backend_var.get()]
        response = backend.generate(prompt)
        self.chat.insert("end", f"Bot: {response}\n")
        self._speak(f"Bot: {response}")
        self.chat.see("end")

    # ---------------------------------------------------------- Sync settings
    def _open_sync_settings(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Sync Settings")
        freq_var = tk.IntVar(value=self.sync_frequency)
        strat_var = tk.StringVar(value=self.conflict_resolution)

        ttk.Label(win, text="Frequency (min):").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Entry(win, textvariable=freq_var, width=10).grid(
            row=0, column=1, padx=5, pady=5, sticky="ew"
        )
        ttk.Label(win, text="On conflict:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        ttk.Combobox(
            win,
            textvariable=strat_var,
            values=["ask", "local", "remote"],
            state="readonly",
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        def save() -> None:
            self.sync_frequency = freq_var.get()
            self.conflict_resolution = strat_var.get()
            win.destroy()

        ttk.Button(win, text="Save", command=save).grid(
            row=2, column=0, columnspan=2, pady=5
        )

    def run(self) -> None:  # pragma: no cover - GUI loop
        """Start the Tk event loop."""

        self.root.mainloop()


def main() -> None:  # pragma: no cover - CLI helper
    def _prompt(plugin: str, perm: str) -> bool:
        if messagebox is None:
            return True
        return messagebox.askyesno("Permission", f"{plugin} requests {perm} access?")

    gui = ChatGUI(permission_prompt=_prompt)
    gui.run()


if __name__ == "__main__":  # pragma: no cover
    main()
