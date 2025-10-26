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
        if webview is None:  # pragma: no cover - runtime safeguard
            raise RuntimeError("pywebview is not installed")

        self.themes = themes.ThemeManager()
        # Basic light and dark themes
        self.themes.add_theme(
            themes.Theme(name="light", background="#ffffff", foreground="#000000")
        )
        self.themes.add_theme(
            themes.Theme(name="dark", background="#000000", foreground="#ffffff")
        )
        self._theme = self.themes.get_theme("light")  # type: ignore[assignment]

        html = self._html_path("chat_ui.html")
        self.window = webview.create_window(
            "Windows AI Installer", html, js_api=self, width=900, height=700
        )

    # ------------------------------------------------------------------ JS API
    def get_theme(self) -> Dict[str, str]:
        """Return the current theme as a plain dictionary."""

        return {
            "name": self._theme.name,
            "background": self._theme.background,
            "foreground": self._theme.foreground,
        }

    def set_theme(self, name: str) -> Dict[str, str]:
        """Switch to ``name`` and return the new theme."""

        theme = self.themes.get_theme(name)
        if theme is not None:
            self._theme = theme
        return self.get_theme()

    # ---------------------------------------------------------------- Helpers
    def _html_path(self, filename: str) -> str:
        return str(Path(__file__).resolve().parent / "web" / filename)

    def run(self) -> None:  # pragma: no cover - thin wrapper
        """Start the PyWebView event loop."""

        webview.start()


def main() -> None:  # pragma: no cover - thin wrapper
    InstallerGUI().run()


if __name__ == "__main__":  # pragma: no cover
    main()
