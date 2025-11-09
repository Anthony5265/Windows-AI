"""
Windows System Integration
Registry, WMI, PowerShell, Services, Process monitoring
"""
from typing import Dict, Any
import logging
import platform

logger = logging.getLogger(__name__)

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

class WindowsIntegration:
    """Main Windows integration manager"""

    def __init__(self):
        self.is_windows = IS_WINDOWS

        if not self.is_windows:
            logger.warning("Windows integration modules available but running on non-Windows platform")

    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        return {
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "is_windows": self.is_windows
        }
