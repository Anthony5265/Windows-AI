from __future__ import annotations

from pathlib import Path
from ui.themes import ThemeManager, Theme


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

    def set_theme(self, name: str) -> dict:
        """Switch to another theme and return it to the frontend."""

        theme = self.themes.get_theme(name)
        if theme is None:
            raise ValueError(f"Unknown theme: {name}")
        self._theme = theme
        return self.get_theme()

    # ------------------------------------------------------------------ Runner
    def run(self) -> None:
        """Start the PyWebView event loop."""

        self._webview.start()


def main() -> None:  # pragma: no cover - thin wrapper
    InstallerGUI().run()


if __name__ == "__main__":  # pragma: no cover
    main()
