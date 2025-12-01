"""
Windows Automation Manager
Complete Windows OS integration with AI capabilities
"""

import asyncio
import logging
import os
import sys
import subprocess
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class WindowsAutomationManager:
    """Complete Windows automation with AI integration"""

    def __init__(self):
        self._initialized = False
        self._is_windows = sys.platform == "win32"

    async def initialize(self, config: Optional[Dict] = None):
        """Initialize Windows automation"""
        if self._initialized:
            return

        if self._is_windows:
            try:
                import win32com.client
                import win32gui
                import win32api
                import win32con
                import pywinauto
                self._win32_available = True
            except ImportError:
                self._win32_available = False
                logger.warning("win32 libraries not available")
        else:
            self._win32_available = False

        self._initialized = True
        logger.info("Windows Automation Manager initialized")

    # ==================== SYSTEM INFORMATION ====================

    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        import psutil
        import platform

        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total if not self._is_windows else psutil.disk_usage('C:\\').total,
                "free": psutil.disk_usage('/').free if not self._is_windows else psutil.disk_usage('C:\\').free,
                "percent": psutil.disk_usage('/').percent if not self._is_windows else psutil.disk_usage('C:\\').percent
            }
        }

        if self._is_windows and self._win32_available:
            import wmi
            c = wmi.WMI()
            info["bios"] = c.Win32_BIOS()[0].SerialNumber if c.Win32_BIOS() else None
            info["gpu"] = [gpu.Name for gpu in c.Win32_VideoController()]

        return info

    # ==================== PROCESS MANAGEMENT ====================

    async def list_processes(self, filter_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List running processes"""
        import psutil

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                info = proc.info
                if filter_name and filter_name.lower() not in info['name'].lower():
                    continue
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)

    async def kill_process(self, pid: int = None, name: str = None) -> bool:
        """Kill a process by PID or name"""
        import psutil

        if pid:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                return True
            except psutil.NoSuchProcess:
                return False

        if name:
            killed = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == name.lower():
                    proc.terminate()
                    killed = True
            return killed

        return False

    async def start_process(self, command: str, args: List[str] = None, cwd: str = None) -> int:
        """Start a new process"""
        args = args or []
        process = await asyncio.create_subprocess_exec(
            command, *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        return process.pid

    # ==================== WINDOW MANAGEMENT ====================

    async def list_windows(self) -> List[Dict[str, Any]]:
        """List all visible windows"""
        if not self._is_windows or not self._win32_available:
            return []

        import win32gui
        import win32process

        windows = []

        def enum_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    results.append({
                        "hwnd": hwnd,
                        "title": title,
                        "pid": pid
                    })

        win32gui.EnumWindows(enum_callback, windows)
        return windows

    async def focus_window(self, hwnd: int = None, title: str = None) -> bool:
        """Focus a window by handle or title"""
        if not self._is_windows or not self._win32_available:
            return False

        import win32gui
        import win32con

        if title and not hwnd:
            hwnd = win32gui.FindWindow(None, title)

        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True

        return False

    async def minimize_window(self, hwnd: int) -> bool:
        """Minimize a window"""
        if not self._is_windows or not self._win32_available:
            return False

        import win32gui
        import win32con

        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return True

    async def maximize_window(self, hwnd: int) -> bool:
        """Maximize a window"""
        if not self._is_windows or not self._win32_available:
            return False

        import win32gui
        import win32con

        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return True

    # ==================== FILE OPERATIONS ====================

    async def list_directory(self, path: str, pattern: str = "*") -> List[Dict[str, Any]]:
        """List directory contents"""
        import glob
        from datetime import datetime

        results = []
        for item in glob.glob(os.path.join(path, pattern)):
            stat = os.stat(item)
            results.append({
                "name": os.path.basename(item),
                "path": item,
                "is_dir": os.path.isdir(item),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return results

    async def search_files(self, directory: str, pattern: str, recursive: bool = True) -> List[str]:
        """Search for files matching pattern"""
        results = []
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if pattern.lower() in file.lower():
                        results.append(os.path.join(root, file))
        else:
            import glob
            results = glob.glob(os.path.join(directory, f"*{pattern}*"))

        return results

    async def read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents"""
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    async def write_file(self, path: str, content: str, encoding: str = "utf-8"):
        """Write content to file"""
        with open(path, "w", encoding=encoding) as f:
            f.write(content)

    # ==================== CLIPBOARD ====================

    async def get_clipboard(self) -> str:
        """Get clipboard contents"""
        if self._is_windows and self._win32_available:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData()
                return data
            except TypeError:
                return ""
            finally:
                win32clipboard.CloseClipboard()
        else:
            import pyperclip
            return pyperclip.paste()

    async def set_clipboard(self, text: str):
        """Set clipboard contents"""
        if self._is_windows and self._win32_available:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text)
            finally:
                win32clipboard.CloseClipboard()
        else:
            import pyperclip
            pyperclip.copy(text)

    # ==================== KEYBOARD & MOUSE ====================

    async def type_text(self, text: str, interval: float = 0.05):
        """Type text using keyboard"""
        import keyboard
        keyboard.write(text, delay=interval)

    async def press_key(self, key: str):
        """Press a key"""
        import keyboard
        keyboard.press_and_release(key)

    async def hotkey(self, *keys):
        """Press a hotkey combination"""
        import keyboard
        keyboard.press_and_release("+".join(keys))

    async def mouse_click(self, x: int, y: int, button: str = "left"):
        """Click mouse at position"""
        import pyautogui
        pyautogui.click(x, y, button=button)

    async def mouse_move(self, x: int, y: int):
        """Move mouse to position"""
        import pyautogui
        pyautogui.moveTo(x, y)

    async def screenshot(self, region: tuple = None, path: str = None) -> str:
        """Take a screenshot"""
        import pyautogui
        from datetime import datetime

        img = pyautogui.screenshot(region=region)

        if not path:
            path = str(Path.home() / ".windowsai" / "screenshots" / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        return path

    # ==================== REGISTRY (Windows only) ====================

    async def read_registry(self, key_path: str, value_name: str) -> Any:
        """Read a registry value"""
        if not self._is_windows:
            return None

        import winreg

        # Parse key path
        root_keys = {
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        }

        parts = key_path.split("\\", 1)
        root = root_keys.get(parts[0])
        subkey = parts[1] if len(parts) > 1 else ""

        try:
            key = winreg.OpenKey(root, subkey)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value
        except WindowsError:
            return None

    # ==================== SERVICES (Windows only) ====================

    async def list_services(self) -> List[Dict[str, Any]]:
        """List Windows services"""
        if not self._is_windows:
            return []

        import psutil

        services = []
        for service in psutil.win_service_iter():
            try:
                info = service.as_dict()
                services.append({
                    "name": info["name"],
                    "display_name": info["display_name"],
                    "status": info["status"],
                    "start_type": info["start_type"]
                })
            except Exception:
                pass

        return services

    async def control_service(self, name: str, action: str) -> bool:
        """Start, stop, or restart a service"""
        if not self._is_windows:
            return False

        valid_actions = ["start", "stop", "restart"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action. Use: {valid_actions}")

        result = subprocess.run(
            ["sc", action, name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0

    # ==================== POWERSHELL ====================

    async def run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute a PowerShell script"""
        if not self._is_windows:
            return {"error": "PowerShell only available on Windows"}

        process = await asyncio.create_subprocess_exec(
            "powershell", "-NoProfile", "-Command", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "return_code": process.returncode
        }

    # ==================== NOTIFICATIONS ====================

    async def send_notification(self, title: str, message: str, icon: str = None):
        """Send a Windows notification"""
        if self._is_windows:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, icon_path=icon, duration=5, threaded=True)
        else:
            # Linux/Mac fallback
            subprocess.run(["notify-send", title, message])

    # ==================== SCHEDULED TASKS ====================

    async def create_scheduled_task(
        self,
        name: str,
        command: str,
        trigger: str,  # "daily", "weekly", "once"
        time: str = "09:00"
    ) -> bool:
        """Create a scheduled task"""
        if not self._is_windows:
            return False

        triggers = {
            "daily": "/sc daily",
            "weekly": "/sc weekly",
            "once": "/sc once"
        }

        cmd = f'schtasks /create /tn "{name}" /tr "{command}" {triggers.get(trigger, "/sc once")} /st {time} /f'
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.returncode == 0

    async def delete_scheduled_task(self, name: str) -> bool:
        """Delete a scheduled task"""
        if not self._is_windows:
            return False

        result = subprocess.run(
            f'schtasks /delete /tn "{name}" /f',
            shell=True,
            capture_output=True
        )
        return result.returncode == 0
