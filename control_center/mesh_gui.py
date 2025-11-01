"""Simple GUI to configure mesh networking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

try:  # pragma: no cover - import may fail on headless systems
    import tkinter as tk  # type: ignore
    from tkinter import messagebox, ttk  # type: ignore
except Exception:  # pragma: no cover - environment specific
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]

from mesh import MeshHub, MeshNode

__all__ = ["MeshSetupGUI", "main"]


@dataclass
class MeshSetupGUI:
    """Minimal interface to start a hub and connect nodes."""

    root: Optional["tk.Tk"] = None
    hub: MeshHub | None = None
    node: MeshNode | None = None

    def __post_init__(self) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("tkinter is not available")
        self.root = self.root or tk.Tk()
        self.root.title("Mesh Setup")
        self._build_widgets()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self) -> None:
        hub_frame = ttk.LabelFrame(self.root, text="Hub")
        hub_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(hub_frame, text="Start", command=self.start_hub).pack(
            side="left", padx=2, pady=2
        )
        ttk.Button(hub_frame, text="Stop", command=self.stop_hub).pack(
            side="left", padx=2, pady=2
        )
        self.hub_label = ttk.Label(hub_frame, text="stopped")
        self.hub_label.pack(side="left", padx=5)

        task_frame = ttk.Frame(hub_frame)
        task_frame.pack(fill="x", padx=5, pady=5)
        self.task_var = tk.StringVar()
        ttk.Entry(task_frame, textvariable=self.task_var, width=40).pack(
            side="left", padx=2
        )
        ttk.Button(task_frame, text="Send", command=self.send_task).pack(
            side="left", padx=2
        )

        node_frame = ttk.LabelFrame(self.root, text="Node")
        node_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(node_frame, text="Discover & Connect", command=self.connect_node).pack(
            side="left", padx=2, pady=2
        )
        ttk.Button(node_frame, text="Disconnect", command=self.disconnect_node).pack(
            side="left", padx=2, pady=2
        )
        self.node_label = ttk.Label(node_frame, text="disconnected")
        self.node_label.pack(side="left", padx=5)

        self.output = tk.Text(self.root, height=10, state="disabled")
        self.output.pack(fill="both", expand=True, padx=5, pady=5)

    # ------------------------------------------------------------------ Hub
    def start_hub(self) -> None:
        if self.hub is not None:
            return
        self.hub = MeshHub()
        self.hub.start()
        self.hub_label.config(
            text=f"hub {self.hub.host}:{self.hub.port} (disc {self.hub.discovery_port})"
        )

    def stop_hub(self) -> None:
        if self.hub is None:
            return
        self.hub.stop()
        self.hub = None
        self.hub_label.config(text="stopped")

    def send_task(self) -> None:
        if self.hub is None:
            if messagebox is not None:
                messagebox.showwarning("Hub not running", "Start the hub first")
            return
        task = self.task_var.get()
        if not task:
            return
        self.hub.distribute_task(task)
        self.task_var.set("")

    # ------------------------------------------------------------------ Node
    def connect_node(self) -> None:
        if self.node is not None:
            return
        try:
            if self.hub is None:
                raise RuntimeError("Hub must be running for discovery")
            addr = MeshNode.discover(self.hub.discovery_port)
        except Exception as exc:
            if messagebox is not None:
                messagebox.showerror("Discovery failed", str(exc))
            return
        self.node = MeshNode(self._handle_task)
        try:
            self.node.connect(addr)
        except Exception as exc:
            self.node = None
            if messagebox is not None:
                messagebox.showerror("Connection failed", str(exc))
            return
        self.node_label.config(text=f"connected to {addr[0]}:{addr[1]}")

    def disconnect_node(self) -> None:
        if self.node is None:
            return
        self.node.stop()
        self.node = None
        self.node_label.config(text="disconnected")

    def _handle_task(self, task: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", task + "\n")
        self.output.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


# ---------------------------------------------------------------------------

def main() -> None:  # pragma: no cover - manual execution entry point
    gui = MeshSetupGUI()
    gui.run()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
