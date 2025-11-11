"""
Global Hotkeys System
Enables quick access to Windows AI via keyboard shortcuts
"""
import logging
import platform
from typing import Callable, Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path
import json
import threading

logger = logging.getLogger(__name__)


@dataclass
class HotkeyConfig:
    """Configuration for a hotkey"""
    name: str
    key_combination: str  # e.g., "Ctrl+Alt+W"
    description: str
    action: str  # Action identifier
    enabled: bool = True


class GlobalHotkeyManager:
    """
    Manages global hotkeys for Windows AI

    Features:
    - Register global hotkeys
    - Cross-platform support (Windows primary, Linux/Mac fallback)
    - Customizable key combinations
    - Action callbacks
    - Persistent configuration
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = data_dir / "hotkeys.json"

        # Hotkey configurations
        self.hotkeys: Dict[str, HotkeyConfig] = {}

        # Action callbacks
        self.action_callbacks: Dict[str, Callable] = {}

        # Platform-specific handler
        self.platform = platform.system()
        self.handler = None

        # Threading
        self._listening = False
        self._listener_thread: Optional[threading.Thread] = None

        # Load configuration
        self._load_config()

        # Initialize default hotkeys
        self._initialize_default_hotkeys()

    def _initialize_default_hotkeys(self):
        """Initialize default hotkey bindings"""
        defaults = [
            HotkeyConfig(
                name="show_windows_ai",
                key_combination="Ctrl+Alt+W",
                description="Show/Hide Windows AI window",
                action="toggle_window"
            ),
            HotkeyConfig(
                name="quick_command",
                key_combination="Ctrl+Alt+Space",
                description="Open quick command palette",
                action="show_command_palette"
            ),
            HotkeyConfig(
                name="voice_input",
                key_combination="Ctrl+Alt+V",
                description="Activate voice input",
                action="start_voice_input"
            ),
            HotkeyConfig(
                name="screenshot_analyze",
                key_combination="Ctrl+Alt+S",
                description="Take screenshot and analyze",
                action="screenshot_analyze"
            ),
            HotkeyConfig(
                name="clipboard_assist",
                key_combination="Ctrl+Alt+C",
                description="AI assist with clipboard content",
                action="clipboard_assist"
            ),
        ]

        for hotkey in defaults:
            if hotkey.name not in self.hotkeys:
                self.hotkeys[hotkey.name] = hotkey

    def register_action(self, action_name: str, callback: Callable):
        """
        Register a callback for an action

        Args:
            action_name: Name of the action
            callback: Function to call when hotkey is pressed
        """
        self.action_callbacks[action_name] = callback
        logger.info(f"Registered action callback: {action_name}")

    def start_listening(self):
        """Start listening for hotkeys"""
        if self._listening:
            logger.warning("Hotkey listener already running")
            return

        self._listening = True

        if self.platform == "Windows":
            self._start_windows_listener()
        else:
            self._start_cross_platform_listener()

        logger.info(f"Started global hotkey listener ({self.platform})")

    def stop_listening(self):
        """Stop listening for hotkeys"""
        self._listening = False

        if self._listener_thread:
            self._listener_thread.join(timeout=2)

        logger.info("Stopped global hotkey listener")

    def _start_windows_listener(self):
        """Start Windows-specific hotkey listener"""
        try:
            import win32con
            import win32api

            def listen_loop():
                """Windows message loop for hotkeys"""
                # Register each hotkey
                hotkey_ids = {}
                hotkey_id = 1

                for name, config in self.hotkeys.items():
                    if not config.enabled:
                        continue

                    try:
                        # Parse key combination
                        modifiers, vk_code = self._parse_windows_hotkey(config.key_combination)

                        # Register hotkey
                        success = win32api.RegisterHotKey(
                            None,  # Current thread
                            hotkey_id,
                            modifiers,
                            vk_code
                        )

                        if success:
                            hotkey_ids[hotkey_id] = name
                            logger.info(f"Registered Windows hotkey: {name} - {config.key_combination}")
                            hotkey_id += 1
                        else:
                            logger.warning(f"Failed to register hotkey: {name}")

                    except Exception as e:
                        logger.error(f"Error registering hotkey {name}: {e}")

                # Message loop
                import win32gui
                while self._listening:
                    try:
                        msg = win32gui.GetMessage(None, 0, 0)
                        if msg:
                            if msg[1][1] == win32con.WM_HOTKEY:
                                hotkey_id = msg[1][2]
                                if hotkey_id in hotkey_ids:
                                    hotkey_name = hotkey_ids[hotkey_id]
                                    self._trigger_action(hotkey_name)
                    except Exception as e:
                        logger.error(f"Error in hotkey message loop: {e}")
                        break

                # Unregister hotkeys
                for hk_id in hotkey_ids.keys():
                    try:
                        win32api.UnregisterHotKey(None, hk_id)
                    except:
                        pass

            self._listener_thread = threading.Thread(target=listen_loop, daemon=True)
            self._listener_thread.start()

        except ImportError:
            logger.warning("win32 modules not available, falling back to cross-platform listener")
            self._start_cross_platform_listener()

    def _start_cross_platform_listener(self):
        """Start cross-platform hotkey listener using keyboard library"""
        try:
            import keyboard

            def on_hotkey(name: str):
                """Callback when hotkey is pressed"""
                self._trigger_action(name)

            # Register hotkeys
            for name, config in self.hotkeys.items():
                if not config.enabled:
                    continue

                try:
                    # Convert to keyboard library format
                    hotkey_str = config.key_combination.lower().replace("ctrl", "control")

                    keyboard.add_hotkey(
                        hotkey_str,
                        lambda n=name: on_hotkey(n),
                        suppress=False
                    )

                    logger.info(f"Registered hotkey: {name} - {config.key_combination}")

                except Exception as e:
                    logger.error(f"Error registering hotkey {name}: {e}")

            # Keep thread alive
            def keep_alive():
                import time
                while self._listening:
                    time.sleep(0.1)

            self._listener_thread = threading.Thread(target=keep_alive, daemon=True)
            self._listener_thread.start()

        except ImportError:
            logger.error("keyboard library not available. Global hotkeys disabled.")
            logger.info("Install with: pip install keyboard")

    def _parse_windows_hotkey(self, key_combination: str) -> tuple[int, int]:
        """Parse key combination into Windows modifiers and virtual key code"""
        import win32con

        parts = key_combination.split("+")
        modifiers = 0
        vk_code = 0

        for part in parts:
            part = part.strip().lower()

            if part == "ctrl" or part == "control":
                modifiers |= win32con.MOD_CONTROL
            elif part == "alt":
                modifiers |= win32con.MOD_ALT
            elif part == "shift":
                modifiers |= win32con.MOD_SHIFT
            elif part == "win" or part == "windows":
                modifiers |= win32con.MOD_WIN
            else:
                # Get virtual key code
                vk_code = ord(part.upper())

        return modifiers, vk_code

    def _trigger_action(self, hotkey_name: str):
        """Trigger the action associated with a hotkey"""
        config = self.hotkeys.get(hotkey_name)
        if not config:
            return

        logger.info(f"Hotkey triggered: {hotkey_name} ({config.key_combination})")

        # Find and execute callback
        action = config.action
        callback = self.action_callbacks.get(action)

        if callback:
            try:
                # Execute in separate thread to avoid blocking
                threading.Thread(target=callback, daemon=True).start()
            except Exception as e:
                logger.error(f"Error executing hotkey action {action}: {e}")
        else:
            logger.warning(f"No callback registered for action: {action}")

    def add_hotkey(self, config: HotkeyConfig):
        """Add or update a hotkey"""
        self.hotkeys[config.name] = config
        self._save_config()
        logger.info(f"Added hotkey: {config.name}")

        # If already listening, restart to register new hotkey
        if self._listening:
            logger.info("Restarting hotkey listener to apply changes")
            self.stop_listening()
            self.start_listening()

    def remove_hotkey(self, name: str):
        """Remove a hotkey"""
        if name in self.hotkeys:
            del self.hotkeys[name]
            self._save_config()
            logger.info(f"Removed hotkey: {name}")

    def enable_hotkey(self, name: str, enabled: bool = True):
        """Enable or disable a hotkey"""
        if name in self.hotkeys:
            self.hotkeys[name].enabled = enabled
            self._save_config()
            logger.info(f"{'Enabled' if enabled else 'Disabled'} hotkey: {name}")

    def get_all_hotkeys(self) -> List[Dict]:
        """Get all hotkey configurations"""
        return [
            {
                "name": config.name,
                "key_combination": config.key_combination,
                "description": config.description,
                "action": config.action,
                "enabled": config.enabled
            }
            for config in self.hotkeys.values()
        ]

    def _save_config(self):
        """Save hotkey configuration"""
        try:
            config_dict = {
                name: {
                    "name": config.name,
                    "key_combination": config.key_combination,
                    "description": config.description,
                    "action": config.action,
                    "enabled": config.enabled
                }
                for name, config in self.hotkeys.items()
            }

            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving hotkey config: {e}")

    def _load_config(self):
        """Load hotkey configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_dict = json.load(f)

                for name, data in config_dict.items():
                    self.hotkeys[name] = HotkeyConfig(**data)

                logger.info(f"Loaded {len(self.hotkeys)} hotkey configurations")

        except Exception as e:
            logger.error(f"Error loading hotkey config: {e}")


# Global instance
_hotkey_manager: Optional[GlobalHotkeyManager] = None


def get_hotkey_manager(data_dir: Path = None) -> GlobalHotkeyManager:
    """Get or create global hotkey manager"""
    global _hotkey_manager

    if _hotkey_manager is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "hotkeys"
        _hotkey_manager = GlobalHotkeyManager(data_dir)

    return _hotkey_manager


def initialize_hotkey_system(data_dir: Path = None, start_listening: bool = True):
    """Initialize the global hotkey system"""
    manager = get_hotkey_manager(data_dir)

    if start_listening:
        manager.start_listening()

    logger.info("Global hotkey system initialized")
    return manager
