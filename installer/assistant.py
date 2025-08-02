from __future__ import annotations

"""Simple rule-based assistant used by the installer GUI.

The assistant provides step-by-step guidance, answers basic questions and can
optionally speak responses if ``pyttsx3`` is available.  It also exposes a
helper to detect missing Python package dependencies so the GUI can warn the
user before installation begins.
"""

from typing import Iterable, List
import importlib.util

try:  # pragma: no cover - optional dependency
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover - import may fail in minimal envs
    pyttsx3 = None  # type: ignore

try:  # pragma: no cover - GUI optional
    import tkinter as tk
except Exception:  # pragma: no cover - headless environments
    tk = None  # type: ignore

__all__ = ["Assistant", "ToolTip"]


class Assistant:
    """Minimal helper answering common installer questions."""

    def __init__(self, enable_voice: bool = False) -> None:
        self.enable_voice = bool(enable_voice and pyttsx3 is not None)
        self._tts = pyttsx3.init() if self.enable_voice else None

    # --- core helpers -------------------------------------------------
    def speak(self, text: str) -> None:
        """Speak *text* if text-to-speech is available."""

        if self._tts:  # pragma: no cover - requires pyttsx3
            self._tts.say(text)
            self._tts.runAndWait()

    def step_by_step(self) -> str:
        """Return a short walkthrough of the installer flow."""

        steps = [
            "Run system scan to detect hardware.",
            "Select the components you wish to install.",
            "Choose a model backend and model.",
            "Provide API keys for services that require them.",
            "Click Install Selected to start installation.",
        ]
        return "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))

    def answer(self, question: str) -> str:
        """Return a canned answer for *question* using keyword rules."""

        q = question.lower()
        if "step" in q or "help" in q:
            return self.step_by_step()
        if "api" in q:
            return "Use 'Add API Key' to store credentials for a service."
        if "install" in q:
            return "Select components then press 'Install Selected'."
        if "model" in q:
            return "Pick a model from the list and download it if required."
        if "system" in q or "scan" in q:
            return "Press 'Detect System' to gather hardware information."
        return "I'm not sure how to help with that. Please consult the docs."

    def check_dependencies(self, packages: Iterable[str]) -> List[str]:
        """Return a list of packages from *packages* that are not installed."""

        missing: List[str] = []
        for pkg in packages:
            if importlib.util.find_spec(pkg) is None:
                missing.append(pkg)
        return missing


class ToolTip:
    """Tiny tooltip helper for Tkinter widgets."""

    def __init__(self, widget: "tk.Widget", text: str) -> None:  # pragma: no cover - GUI code
        self.widget = widget
        self.text = text
        self.tipwindow: "tk.Toplevel | None" = None
        if tk:
            widget.bind("<Enter>", self.show)
            widget.bind("<Leave>", self.hide)

    def show(self, event=None) -> None:  # pragma: no cover - GUI code
        if not tk or self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hide(self, event=None) -> None:  # pragma: no cover - GUI code
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
