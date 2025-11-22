"""
Windows AI Core Module
Master orchestrator and core functionality
"""

from windows_ai.core.plugin_manager import PluginManager
from windows_ai.core.orchestrator import WindowsAI, get_windows_ai, quick_start
from windows_ai.core.auto_setup import AutoSetup, ensure_setup
from windows_ai.core.dependency_installer import DependencyInstaller

__all__ = [
    "PluginManager",
    "WindowsAI",
    "get_windows_ai",
    "quick_start",
    "AutoSetup",
    "ensure_setup",
    "DependencyInstaller"
]
