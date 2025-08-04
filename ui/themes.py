from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Theme:
    name: str
    background: str
    foreground: str
    # Optional human friendly descriptions for screen readers.
    descriptions: Optional[Dict[str, str]] = None

    def describe(self, element: str) -> Optional[str]:
        """Return a screen reader description for ``element`` if available."""

        if self.descriptions is None:
            return None
        return self.descriptions.get(element)


@dataclass
class Keyset:
    name: str
    mappings: Dict[str, str]


class ThemeManager:
    """Manage UI themes and keysets."""

    def __init__(self):
        self._themes: Dict[str, Theme] = {}
        self._keysets: Dict[str, Keyset] = {}
        self.screen_reader_enabled: bool = False

        # Provide a built-in high contrast theme that can be selected when the
        # operating system requests it.  Users may override it by adding a
        # theme with the same name.
        self.add_theme(Theme(name="high_contrast", background="#000", foreground="#fff"))

    def add_theme(self, theme: Theme) -> None:
        self._themes[theme.name] = theme

    def get_theme(self, name: str) -> Optional[Theme]:
        return self._themes.get(name)

    def add_keyset(self, keyset: Keyset) -> None:
        self._keysets[keyset.name] = keyset

    def get_keyset(self, name: str) -> Optional[Keyset]:
        return self._keysets.get(name)

    # -------------------------------------------------------------- Accessibility
    def apply_accessibility(
        self, screen_reader: bool = False, high_contrast: bool = False
    ) -> Optional[Theme]:
        """Enable accessibility features and return the selected theme.

        ``screen_reader`` toggles exposure of screen reader descriptions while
        ``high_contrast`` chooses the bundled high-contrast theme when
        available.  The method returns the chosen theme so callers can react to
        the change.
        """

        self.screen_reader_enabled = screen_reader
        if high_contrast:
            theme = self._themes.get("high_contrast")
            if theme:
                return theme
        return None
