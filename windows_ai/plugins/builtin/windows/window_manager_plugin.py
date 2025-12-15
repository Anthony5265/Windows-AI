"""
Windows Window Manager Plugin - PRODUCTION
Comprehensive window management and manipulation capabilities
"""
import os
import asyncio
import subprocess
import ctypes
from ctypes import wintypes
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)

# Windows API constants
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_SHOWMAXIMIZED = 3
SW_RESTORE = 9
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

try:
    # Windows API functions
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
except Exception:
    user32 = None
    kernel32 = None

class WindowsWindowManagerPlugin(IntegrationPlugin):
    """
    Comprehensive Windows window management plugin
    
    Features:
    - List all windows
    - Move, resize, minimize, maximize windows
    - Set window always-on-top
    - Focus windows
    - Close windows
    - Get window information
    - Multi-monitor support
    - Virtual desktop management
    """
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_window_manager",
            name="Windows Window Manager",
            description="Comprehensive window management and manipulation",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "os", "window", "management", "desktop"]
        )
        super().__init__(metadata)
        self.connected = False
        self._hwnd_cache = {}

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            if user32 is None:
                logger.warning("Windows API not available - running in compatibility mode")
            self._initialized = True
            logger.info("Window Manager plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Window Manager plugin: {e}")
            return False

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to window management system"""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from window management system"""
        self.connected = False
        self._hwnd_cache.clear()
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute window management action
        
        Args:
            action: Action to perform (list, focus, minimize, maximize, close, etc.)
            parameters: Action parameters
            
        Returns:
            Result dictionary
        """
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        try:
            if action == "list_windows":
                return await self.list_windows(parameters)
            elif action == "focus_window":
                return await self.focus_window(parameters)
            elif action == "minimize_window":
                return await self.minimize_window(parameters)
            elif action == "maximize_window":
                return await self.maximize_window(parameters)
            elif action == "restore_window":
                return await self.restore_window(parameters)
            elif action == "close_window":
                return await self.close_window(parameters)
            elif action == "move_window":
                return await self.move_window(parameters)
            elif action == "resize_window":
                return await self.resize_window(parameters)
            elif action == "set_always_on_top":
                return await self.set_always_on_top(parameters)
            elif action == "get_window_info":
                return await self.get_window_info(parameters)
            elif action == "get_foreground_window":
                return await self.get_foreground_window()
            elif action == "tile_windows":
                return await self.tile_windows(parameters)
            elif action == "cascade_windows":
                return await self.cascade_windows(parameters)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f"Error executing window manager action '{action}': {e}")
            return {"success": False, "error": str(e)}

    async def list_windows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all visible windows"""
        try:
            if user32 is None:
                # Fallback to PowerShell
                return await self._list_windows_powershell()
            
            windows = []
            
            def enum_callback(hwnd, _):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buffer = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buffer, length + 1)
                        title = buffer.value
                        
                        # Get process ID
                        pid = wintypes.DWORD()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "pid": pid.value
                        })
                return True
            
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
            
            # Filter by criteria if provided
            filter_title = params.get("filter_title")
            if filter_title:
                windows = [w for w in windows if filter_title.lower() in w["title"].lower()]
            
            return {
                "success": True,
                "windows": windows,
                "count": len(windows)
            }
            
        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            return {"success": False, "error": str(e)}

    async def _list_windows_powershell(self) -> Dict[str, Any]:
        """Fallback method using PowerShell"""
        try:
            script = """
            Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object Id, MainWindowTitle, ProcessName | ConvertTo-Json
            """
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                windows_data = json.loads(stdout.decode())
                if not isinstance(windows_data, list):
                    windows_data = [windows_data]
                
                windows = [
                    {
                        "hwnd": w.get("Id"),
                        "title": w.get("MainWindowTitle", ""),
                        "pid": w.get("Id"),
                        "process": w.get("ProcessName", "")
                    }
                    for w in windows_data
                ]
                return {"success": True, "windows": windows, "count": len(windows)}
            else:
                return {"success": False, "error": stderr.decode()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def focus_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bring window to foreground"""
        try:
            hwnd = params.get("hwnd")
            title = params.get("title")
            
            if not hwnd and not title:
                return {"success": False, "error": "Either hwnd or title must be provided"}
            
            if title and not hwnd:
                # Find window by title
                windows = await self.list_windows({"filter_title": title})
                if windows.get("success") and windows.get("windows"):
                    hwnd = windows["windows"][0]["hwnd"]
                else:
                    return {"success": False, "error": f"Window with title '{title}' not found"}
            
            if user32:
                user32.SetForegroundWindow(int(hwnd))
                user32.ShowWindow(int(hwnd), SW_RESTORE)
                return {"success": True, "hwnd": hwnd}
            else:
                # PowerShell fallback
                script = f"(Get-Process | Where-Object {{$_.MainWindowTitle -like '*{title}*'}}).MainWindowHandle | ForEach-Object {{[System.Windows.Forms.NativeMethods]::SetForegroundWindow($_)}}"
                return await self._execute_powershell(script)
                
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return {"success": False, "error": str(e)}

    async def minimize_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Minimize window"""
        try:
            hwnd = params.get("hwnd")
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                user32.ShowWindow(int(hwnd), SW_SHOWMINIMIZED)
                return {"success": True, "hwnd": hwnd}
            else:
                script = f"(Get-Process -Id {hwnd}).MainWindowHandle | ForEach-Object {{[WindowsAPI]::ShowWindow($_, 2)}}"
                return await self._execute_powershell(script)
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def maximize_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Maximize window"""
        try:
            hwnd = params.get("hwnd")
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                user32.ShowWindow(int(hwnd), SW_SHOWMAXIMIZED)
                return {"success": True, "hwnd": hwnd}
            else:
                script = f"(Get-Process -Id {hwnd}).MainWindowHandle | ForEach-Object {{[WindowsAPI]::ShowWindow($_, 3)}}"
                return await self._execute_powershell(script)
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def restore_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore window to normal size"""
        try:
            hwnd = params.get("hwnd")
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                user32.ShowWindow(int(hwnd), SW_RESTORE)
                return {"success": True, "hwnd": hwnd}
            else:
                script = f"(Get-Process -Id {hwnd}).MainWindowHandle | ForEach-Object {{[WindowsAPI]::ShowWindow($_, 9)}}"
                return await self._execute_powershell(script)
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close window"""
        try:
            hwnd = params.get("hwnd")
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                WM_CLOSE = 0x0010
                user32.SendMessageW(int(hwnd), WM_CLOSE, 0, 0)
                return {"success": True, "hwnd": hwnd}
            else:
                script = f"Stop-Process -Id {hwnd} -Force"
                return await self._execute_powershell(script)
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def move_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move window to specified position"""
        try:
            hwnd = params.get("hwnd")
            x = params.get("x", 0)
            y = params.get("y", 0)
            
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                rect = wintypes.RECT()
                user32.GetWindowRect(int(hwnd), ctypes.byref(rect))
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                
                user32.SetWindowPos(
                    int(hwnd), HWND_TOP, int(x), int(y), width, height,
                    SWP_NOZORDER
                )
                return {"success": True, "hwnd": hwnd, "x": x, "y": y}
            else:
                return {"success": False, "error": "Windows API not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def resize_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resize window"""
        try:
            hwnd = params.get("hwnd")
            width = params.get("width")
            height = params.get("height")
            
            if not hwnd or width is None or height is None:
                return {"success": False, "error": "hwnd, width, and height parameters required"}
            
            if user32:
                rect = wintypes.RECT()
                user32.GetWindowRect(int(hwnd), ctypes.byref(rect))
                
                user32.SetWindowPos(
                    int(hwnd), HWND_TOP, rect.left, rect.top, int(width), int(height),
                    SWP_NOZORDER
                )
                return {"success": True, "hwnd": hwnd, "width": width, "height": height}
            else:
                return {"success": False, "error": "Windows API not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_always_on_top(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set window always on top"""
        try:
            hwnd = params.get("hwnd")
            enabled = params.get("enabled", True)
            
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                rect = wintypes.RECT()
                user32.GetWindowRect(int(hwnd), ctypes.byref(rect))
                
                hwnd_flag = HWND_TOPMOST if enabled else HWND_NOTOPMOST
                user32.SetWindowPos(
                    int(hwnd), hwnd_flag,
                    rect.left, rect.top,
                    rect.right - rect.left, rect.bottom - rect.top,
                    SWP_NOMOVE | SWP_NOSIZE
                )
                return {"success": True, "hwnd": hwnd, "always_on_top": enabled}
            else:
                return {"success": False, "error": "Windows API not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_window_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed window information"""
        try:
            hwnd = params.get("hwnd")
            if not hwnd:
                return {"success": False, "error": "hwnd parameter required"}
            
            if user32:
                # Get window title
                length = user32.GetWindowTextLengthW(int(hwnd))
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(int(hwnd), buffer, length + 1)
                title = buffer.value
                
                # Get window rect
                rect = wintypes.RECT()
                user32.GetWindowRect(int(hwnd), ctypes.byref(rect))
                
                # Get process ID
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(int(hwnd), ctypes.byref(pid))
                
                # Check if visible
                is_visible = user32.IsWindowVisible(int(hwnd))
                
                return {
                    "success": True,
                    "hwnd": hwnd,
                    "title": title,
                    "pid": pid.value,
                    "visible": bool(is_visible),
                    "rect": {
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.right - rect.left,
                        "height": rect.bottom - rect.top
                    }
                }
            else:
                return {"success": False, "error": "Windows API not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_foreground_window(self) -> Dict[str, Any]:
        """Get currently focused window"""
        try:
            if user32:
                hwnd = user32.GetForegroundWindow()
                if hwnd:
                    return await self.get_window_info({"hwnd": hwnd})
                else:
                    return {"success": False, "error": "No foreground window"}
            else:
                return {"success": False, "error": "Windows API not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def tile_windows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tile windows on screen"""
        try:
            hwnds = params.get("hwnds", [])
            if not hwnds:
                # Get all visible windows
                windows = await self.list_windows({})
                if windows.get("success"):
                    hwnds = [w["hwnd"] for w in windows.get("windows", [])][:4]  # Max 4 windows
            
            if not hwnds:
                return {"success": False, "error": "No windows to tile"}
            
            # Get screen dimensions
            if user32:
                screen_width = user32.GetSystemMetrics(0)
                screen_height = user32.GetSystemMetrics(1)
                
                count = len(hwnds)
                cols = 2 if count > 1 else 1
                rows = (count + 1) // 2
                
                width = screen_width // cols
                height = screen_height // rows
                
                for i, hwnd in enumerate(hwnds):
                    col = i % cols
                    row = i // cols
                    x = col * width
                    y = row * height
                    
                    await self.move_window({"hwnd": hwnd, "x": x, "y": y})
                    await self.resize_window({"hwnd": hwnd, "width": width, "height": height})
                
                return {"success": True, "tiled_count": count}
            else:
                return {"success": False, "error": "Windows API not available"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cascade_windows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cascade windows"""
        try:
            hwnds = params.get("hwnds", [])
            if not hwnds:
                windows = await self.list_windows({})
                if windows.get("success"):
                    hwnds = [w["hwnd"] for w in windows.get("windows", [])][:10]
            
            if not hwnds:
                return {"success": False, "error": "No windows to cascade"}
            
            offset = 30
            for i, hwnd in enumerate(hwnds):
                x = i * offset
                y = i * offset
                await self.move_window({"hwnd": hwnd, "x": x, "y": y})
                await self.restore_window({"hwnd": hwnd})
            
            return {"success": True, "cascaded_count": len(hwnds)}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_powershell(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell script"""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else ""
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shutdown(self):
        """Shutdown plugin"""
        await self.disconnect()
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Get plugin schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list_windows", "focus_window", "minimize_window",
                        "maximize_window", "restore_window", "close_window",
                        "move_window", "resize_window", "set_always_on_top",
                        "get_window_info", "get_foreground_window",
                        "tile_windows", "cascade_windows"
                    ]
                },
                "parameters": {"type": "object"}
            },
            "required": ["action"]
        }

plugin = WindowsWindowManagerPlugin()
