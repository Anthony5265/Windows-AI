import json
import locale
from importlib import resources


def load_strings(lang: str | None = None) -> dict[str, str]:
    """Load localized strings for the given language code.

    If *lang* is ``None`` the system locale is used.  Only the first two
    characters of the locale are considered.  Falls back to English when the
    requested language is not available.
    """

    if lang is None:
        loc, _ = locale.getdefaultlocale()
        lang = (loc or "en")[:2]
    else:
        lang = lang[:2]

    filename = f"{lang}.json"
    try:
        data = resources.files(__package__).joinpath(filename).read_text("utf-8")
    except FileNotFoundError:
        data = resources.files(__package__).joinpath("en.json").read_text("utf-8")
    return json.loads(data)


_strings = load_strings()


def _(key: str) -> str:
    """Return the localized string for *key*."""

    return _strings.get(key, key)


def set_language(lang: str | None) -> None:
    """Reload localized strings for the given language code."""

    global _strings
    _strings = load_strings(lang)

