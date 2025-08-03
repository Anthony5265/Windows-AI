from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Theme:
    name: str
    background: str
    foreground: str


@dataclass
class Keyset:
    name: str
    mappings: Dict[str, str]


class ThemeManager:
    """Manage UI themes and keysets."""

    def __init__(self):
        self._themes: Dict[str, Theme] = {}
        self._keysets: Dict[str, Keyset] = {}

    def add_theme(self, theme: Theme) -> None:
        self._themes[theme.name] = theme

    def get_theme(self, name: str) -> Optional[Theme]:
        return self._themes.get(name)

    def add_keyset(self, keyset: Keyset) -> None:
        self._keysets[keyset.name] = keyset

    def get_keyset(self, name: str) -> Optional[Keyset]:
        return self._keysets.get(name)
