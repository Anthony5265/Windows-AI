"""
Search Module Compatibility Shim
Re-exports SearchEngine and backends from windows_ai.search for test compatibility.
"""

from windows_ai.search import SearchEngine, load_engine
from windows_ai.search.backends import LocalBackend, CloudBackend

__all__ = [
    "SearchEngine",
    "load_engine",
    "LocalBackend",
    "CloudBackend",
]
