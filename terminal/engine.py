"""
Terminal Engine Compatibility Shim
Re-exports TerminalEngine from windows_ai.terminal.engine for test compatibility.
"""

from windows_ai.terminal.engine import TerminalEngine

__all__ = ["TerminalEngine"]
