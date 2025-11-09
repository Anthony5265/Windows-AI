"""
Windows Registry Access Module
Read, write, and manage Windows Registry keys and values
"""
from typing import Dict, Any, List, Optional, Union
import logging
import platform

logger = logging.getLogger(__name__)

# Try to import Windows-specific modules
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        import winreg
        WINREG_AVAILABLE = True
    except ImportError:
        WINREG_AVAILABLE = False
else:
    WINREG_AVAILABLE = False


class RegistryManager:
    """Production Windows Registry access"""

    def __init__(self):
        self.is_available = WINREG_AVAILABLE

        # Registry hive constants
        if WINREG_AVAILABLE:
            self.hives = {
                "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
                "HKCR": winreg.HKEY_CLASSES_ROOT,
                "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
                "HKCU": winreg.HKEY_CURRENT_USER,
                "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
                "HKLM": winreg.HKEY_LOCAL_MACHINE,
                "HKEY_USERS": winreg.HKEY_USERS,
                "HKU": winreg.HKEY_USERS,
                "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
                "HKCC": winreg.HKEY_CURRENT_CONFIG
            }

            # Value type constants
            self.value_types = {
                "REG_BINARY": winreg.REG_BINARY,
                "REG_DWORD": winreg.REG_DWORD,
                "REG_DWORD_LITTLE_ENDIAN": winreg.REG_DWORD_LITTLE_ENDIAN,
                "REG_DWORD_BIG_ENDIAN": winreg.REG_DWORD_BIG_ENDIAN,
                "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
                "REG_LINK": winreg.REG_LINK,
                "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
                "REG_NONE": winreg.REG_NONE,
                "REG_QWORD": winreg.REG_QWORD,
                "REG_QWORD_LITTLE_ENDIAN": winreg.REG_QWORD_LITTLE_ENDIAN,
                "REG_SZ": winreg.REG_SZ
            }
        else:
            self.hives = {}
            self.value_types = {}

    def read_value(self, hive: str, key_path: str, value_name: str) -> Dict[str, Any]:
        """
        Read a registry value

        Args:
            hive: Registry hive (e.g., "HKLM", "HKCU")
            key_path: Path to registry key
            value_name: Name of value to read

        Returns:
            Dict with value data and type
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available (not Windows or winreg not imported)"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            with winreg.OpenKey(hive_key, key_path) as key:
                value_data, value_type = winreg.QueryValueEx(key, value_name)

                # Get type name
                type_name = None
                for name, type_const in self.value_types.items():
                    if type_const == value_type:
                        type_name = name
                        break

                return {
                    "status": "success",
                    "value": value_data,
                    "type": type_name or f"Unknown ({value_type})",
                    "type_code": value_type
                }

        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Key not found: {hive}\\{key_path}"
            }
        except Exception as e:
            logger.error(f"Registry read error: {e}")
            return {"status": "error", "message": str(e)}

    def write_value(self, hive: str, key_path: str, value_name: str,
                   value_data: Any, value_type: str = "REG_SZ") -> Dict[str, Any]:
        """
        Write a registry value

        Args:
            hive: Registry hive
            key_path: Path to registry key
            value_name: Name of value to write
            value_data: Data to write
            value_type: Type of value (e.g., "REG_SZ", "REG_DWORD")

        Returns:
            Dict with success status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            type_const = self.value_types.get(value_type)
            if type_const is None:
                return {"status": "error", "message": f"Unknown value type: {value_type}"}

            with winreg.CreateKeyEx(hive_key, key_path) as key:
                winreg.SetValueEx(key, value_name, 0, type_const, value_data)

            return {
                "status": "success",
                "message": f"Value written: {hive}\\{key_path}\\{value_name}"
            }

        except PermissionError:
            return {
                "status": "error",
                "message": "Permission denied. Administrator rights required."
            }
        except Exception as e:
            logger.error(f"Registry write error: {e}")
            return {"status": "error", "message": str(e)}

    def delete_value(self, hive: str, key_path: str, value_name: str) -> Dict[str, Any]:
        """
        Delete a registry value

        Args:
            hive: Registry hive
            key_path: Path to registry key
            value_name: Name of value to delete

        Returns:
            Dict with success status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            with winreg.OpenKey(hive_key, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, value_name)

            return {
                "status": "success",
                "message": f"Value deleted: {hive}\\{key_path}\\{value_name}"
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Value not found: {hive}\\{key_path}\\{value_name}"
            }
        except PermissionError:
            return {
                "status": "error",
                "message": "Permission denied. Administrator rights required."
            }
        except Exception as e:
            logger.error(f"Registry delete error: {e}")
            return {"status": "error", "message": str(e)}

    def create_key(self, hive: str, key_path: str) -> Dict[str, Any]:
        """
        Create a registry key

        Args:
            hive: Registry hive
            key_path: Path to registry key to create

        Returns:
            Dict with success status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            winreg.CreateKey(hive_key, key_path)

            return {
                "status": "success",
                "message": f"Key created: {hive}\\{key_path}"
            }

        except PermissionError:
            return {
                "status": "error",
                "message": "Permission denied. Administrator rights required."
            }
        except Exception as e:
            logger.error(f"Registry create key error: {e}")
            return {"status": "error", "message": str(e)}

    def delete_key(self, hive: str, key_path: str) -> Dict[str, Any]:
        """
        Delete a registry key (must be empty)

        Args:
            hive: Registry hive
            key_path: Path to registry key to delete

        Returns:
            Dict with success status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            winreg.DeleteKey(hive_key, key_path)

            return {
                "status": "success",
                "message": f"Key deleted: {hive}\\{key_path}"
            }

        except OSError as e:
            if "subkeys" in str(e).lower():
                return {
                    "status": "error",
                    "message": "Key has subkeys. Delete subkeys first or use delete_key_tree."
                }
            return {"status": "error", "message": str(e)}
        except PermissionError:
            return {
                "status": "error",
                "message": "Permission denied. Administrator rights required."
            }
        except Exception as e:
            logger.error(f"Registry delete key error: {e}")
            return {"status": "error", "message": str(e)}

    def list_subkeys(self, hive: str, key_path: str) -> Dict[str, Any]:
        """
        List all subkeys of a registry key

        Args:
            hive: Registry hive
            key_path: Path to registry key

        Returns:
            Dict with list of subkey names
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            subkeys = []
            with winreg.OpenKey(hive_key, key_path) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkeys.append(subkey_name)
                        i += 1
                    except OSError:
                        break

            return {
                "status": "success",
                "subkeys": subkeys,
                "count": len(subkeys)
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Key not found: {hive}\\{key_path}"
            }
        except Exception as e:
            logger.error(f"Registry list subkeys error: {e}")
            return {"status": "error", "message": str(e)}

    def list_values(self, hive: str, key_path: str) -> Dict[str, Any]:
        """
        List all values in a registry key

        Args:
            hive: Registry hive
            key_path: Path to registry key

        Returns:
            Dict with list of values
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "Registry access not available"
            }

        try:
            hive_key = self.hives.get(hive)
            if hive_key is None:
                return {"status": "error", "message": f"Unknown hive: {hive}"}

            values = []
            with winreg.OpenKey(hive_key, key_path) as key:
                i = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, i)

                        # Get type name
                        type_name = None
                        for name, type_const in self.value_types.items():
                            if type_const == value_type:
                                type_name = name
                                break

                        values.append({
                            "name": value_name,
                            "data": value_data,
                            "type": type_name or f"Unknown ({value_type})"
                        })
                        i += 1
                    except OSError:
                        break

            return {
                "status": "success",
                "values": values,
                "count": len(values)
            }

        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Key not found: {hive}\\{key_path}"
            }
        except Exception as e:
            logger.error(f"Registry list values error: {e}")
            return {"status": "error", "message": str(e)}
