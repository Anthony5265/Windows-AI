"""Tkinter-based chat interface for the Windows AI Control Center.

The GUI presents a minimal chat window and a backend selector allowing users
to switch between local models and remote APIs.
"""

from __future__ import annotations

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

__all__ = ["ChatGUI", "main"]


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

        self.entry = ttk.Entry(input_frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<Return>", self.send_message)

        ttk.Button(input_frame, text="Send", command=self.send_message).pack(
            side="left", padx=5
        )
        ttk.Button(input_frame, text="Mesh", command=self._open_mesh_config).pack(
            side="left", padx=5
        )

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

    def run(self) -> None:  # pragma: no cover - GUI loop
        """Start the Tk event loop."""

        self.root.mainloop()


def main() -> None:  # pragma: no cover - CLI helper
    gui = ChatGUI()
    gui.run()


if __name__ == "__main__":  # pragma: no cover
    main()
