"""Tkinter-based chat interface for the Windows AI Control Center.

The GUI presents a minimal chat window and a backend selector allowing users
to switch between local models and remote APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

try:  # pragma: no cover - import may fail on headless systems
    import tkinter as tk  # type: ignore
    from tkinter import ttk  # type: ignore
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]

from .backends import Backend, LocalBackend, RemoteBackend
from . import get_plugins
from mesh import MeshNode
from iot import ADAPTERS, discover_devices, pair_device
from secrets import token_urlsafe
from plugins.manager import PluginManager
from security import AuditLogger, PermissionManager
from optimization import tuning

try:  # pragma: no cover - optional dependency
    import qrcode  # type: ignore
except Exception:  # pragma: no cover
    qrcode = None  # type: ignore[assignment]

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
        self.dashboard_manager = DashboardManager()

        self._build_widgets()

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
        ttk.Button(input_frame, text="IoT", command=self._open_iot_window).pack(
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
    def _open_iot_window(self) -> None:
        """Open device discovery and pairing window."""

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
        self.entry.delete(0, "end")
        backend = self.backends[self.backend_var.get()]
        response = backend.generate(prompt)
        self.chat.insert("end", f"Bot: {response}\n")
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
    gui = ChatGUI()
    gui.run()


if __name__ == "__main__":  # pragma: no cover
    main()
