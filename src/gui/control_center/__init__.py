"""Control Center package for Windows AI.

Provides a simple chat interface with pluggable backends and a small plugin
registry so that new capabilities (vision, speech, automation, etc.) can be
added without modifying the core GUI.
"""

from __future__ import annotations

from typing import Protocol

__all__ = ["Plugin", "register_plugin", "get_plugins"]


class Plugin(Protocol):
    """Interface that all Control Center plugins must implement.

    Plugins receive an instance of :class:`~control_center.gui.ChatGUI` and can
    modify it by adding widgets, menu entries or command handlers.
    """

    def register(self, gui: "ChatGUI") -> None:  # pragma: no cover - runtime hook
        """Install the plugin into the GUI."""


_PLUGINS: list[Plugin] = []


def register_plugin(plugin: Plugin) -> None:
    """Register a plugin to extend the Control Center GUI."""

    _PLUGINS.append(plugin)


def get_plugins() -> list[Plugin]:
    """Return a copy of all registered plugins."""

    return list(_PLUGINS)
