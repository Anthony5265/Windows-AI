"""Re-export backends from windows_ai.search.backends for backwards compatibility."""

from windows_ai.search.backends import LocalBackend, CloudBackend, SearchBackend

__all__ = ["LocalBackend", "CloudBackend", "SearchBackend"]
