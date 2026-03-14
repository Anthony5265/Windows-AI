"""
Windows AI - Unified AI Platform
2500+ AI capabilities in one simple package

Quick Start:
    >>> import asyncio
    >>> from windows_ai import quick_start
    >>>
    >>> async def main():
    >>>     ai = await quick_start()
    >>>     response = await ai.chat("Hello!")
    >>>     print(response)
    >>>
    >>> asyncio.run(main())
"""

__version__ = "2.0.0a1"

# Core functionality
from windows_ai.core import WindowsAI, get_windows_ai, quick_start

__all__ = [
    # Core
    "WindowsAI",
    "get_windows_ai",
    "quick_start",

    # Metadata
    "__version__"
]
