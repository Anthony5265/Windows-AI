"""Tkinter-based chat UI integrated with the plugin system.

The widget layout mirrors ``gui.py`` but also exposes installed plugins as a
selectable list of tools.  The module is tolerant of headless environments –
when no display is available the UI elements are not constructed, allowing the
logic to be unit tested.
"""
from __future__ import annotations

from typing import Dict, Optional

try:  # pragma: no cover - executed only when tkinter is available
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover - headless environment
    tk = None
    ttk = None

from backends import Backend, load_backend
from . import get_plugins

__all__ = ["ChatUI", "main"]


class ChatUI:
    """Simple chat window that lists available plugins as tools."""

    def __init__(
        self,
        root: Optional["tk.Tk"] = None,
        backends: Optional[Dict[str, Backend]] = None,
        build: bool = True,
    ) -> None:
        self.backends = backends or {
            "Local": load_backend("local"),
            "Remote": load_backend("remote"),
        }
        self.plugins = get_plugins()
        self.plugin_names = [getattr(p, "name", p.__class__.__name__) for p in self.plugins]

        # GUI related attributes default to ``None`` when running headless
        self.root: Optional["tk.Tk"] = None
        self.backend_var: Optional["tk.StringVar"] = None
        self.node_var: Optional["tk.StringVar"] = None
        self.entry: Optional[ttk.Entry] = None
        self.chat: Optional[tk.Text] = None

        if build and tk is not None:
            try:
                self.root = root or tk.Tk()
                self.root.title("Windows AI Control Center")
                self.backend_var = tk.StringVar(value=next(iter(self.backends)))
                self.node_var = tk.StringVar(
                    value=self.plugin_names[0] if self.plugin_names else ""
                )
                self._build_widgets()
                for plugin in self.plugins:  # pragma: no cover - runtime hook
                    plugin.register(self)
            except tk.TclError:  # pragma: no cover - headless fallback
                self.root = None

    # ------------------------------------------------------------------ UI
    def _build_widgets(self) -> None:  # pragma: no cover - GUI only
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

        ttk.Label(input_frame, text="Tool:").pack(side="left", padx=5)
        node_selector = ttk.Combobox(
            input_frame,
            textvariable=self.node_var,
            values=self.plugin_names,
            state="readonly",
            width=15,
        )
        node_selector.pack(side="left")

        self.entry = ttk.Entry(input_frame)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<Return>", self.send_message)

        ttk.Button(input_frame, text="Send", command=self.send_message).pack(
            side="left", padx=5
        )

    # ----------------------------------------------------------------- Chat
    def send_message(self, event: object | None = None) -> None:
        if self.entry is None or self.chat is None or self.backend_var is None:
            return
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
        if self.root is not None:
            self.root.mainloop()


def main() -> None:  # pragma: no cover - CLI helper
    ui = ChatUI()
    ui.run()


if __name__ == "__main__":  # pragma: no cover
    main()
