"""
Windows Registry Plugin
Supports reading and writing Windows Registry keys
"""

from typing import Dict, Any, Optional
import winreg


class RegistryPlugin:
    """Plugin for Windows Registry operations"""
    
    name = "registry"
    version = "1.0.0"
    description = "Windows Registry read/write operations"
    author = "Windows AI Team"
    
    def __init__(self):
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Registry plugin"""
        try:
            # No special initialization needed for registry access
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Registry plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a registry action"""
        if not self._initialized:
            return {"error": "Plugin not initialized."}
        
        try:
            if action == "read_key":
                return self._read_key(params)
            elif action == "write_key":
                return self._write_key(params)
            elif action == "delete_key":
                return self._delete_key(params)
            elif action == "list_keys":
                return self._list_keys(params)
            elif action == "list_values":
                return self._list_values(params)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_hive(self, hive_name: str):
        """Get registry hive constant from name"""
        hives = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }
        return hives.get(hive_name.upper())
    
    def _read_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a registry key value"""
        hive_name = params.get("hive", "HKEY_CURRENT_USER")
        key_path = params.get("key_path", "")
        value_name = params.get("value_name", "")
        
        hive = self._get_hive(hive_name)
        if not hive:
            return {"error": f"Invalid hive: {hive_name}"}
        
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                value, value_type = winreg.QueryValueEx(key, value_name)
                return {
                    "value": value,
                    "value_type": value_type,
                    "hive": hive_name,
                    "key_path": key_path,
                    "value_name": value_name
                }
        except FileNotFoundError:
            return {"error": "Key or value not found"}
        except Exception as e:
            return {"error": str(e)}
    
    def _write_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write a registry key value"""
        hive_name = params.get("hive", "HKEY_CURRENT_USER")
        key_path = params.get("key_path", "")
        value_name = params.get("value_name", "")
        value = params.get("value")
        value_type = params.get("value_type", winreg.REG_SZ)
        
        hive = self._get_hive(hive_name)
        if not hive:
            return {"error": f"Invalid hive: {hive_name}"}
        
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, value_name, 0, value_type, value)
                return {
                    "success": True,
                    "hive": hive_name,
                    "key_path": key_path,
                    "value_name": value_name,
                    "value": value,
                    "value_type": value_type
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _delete_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a registry key or value"""
        hive_name = params.get("hive", "HKEY_CURRENT_USER")
        key_path = params.get("key_path", "")
        value_name = params.get("value_name")  # If None, delete the key
        
        hive = self._get_hive(hive_name)
        if not hive:
            return {"error": f"Invalid hive: {hive_name}"}
        
        try:
            if value_name is not None:
                # Delete value
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, value_name)
                return {
                    "success": True,
                    "deleted": "value",
                    "hive": hive_name,
                    "key_path": key_path,
                    "value_name": value_name
                }
            else:
                # Delete key
                winreg.DeleteKey(hive, key_path)
                return {
                    "success": True,
                    "deleted": "key",
                    "hive": hive_name,
                    "key_path": key_path
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _list_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List subkeys of a registry key"""
        hive_name = params.get("hive", "HKEY_CURRENT_USER")
        key_path = params.get("key_path", "")
        
        hive = self._get_hive(hive_name)
        if not hive:
            return {"error": f"Invalid hive: {hive_name}"}
        
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                keys = []
                i = 0
                while True:
                    try:
                        subkey = winreg.EnumKey(key, i)
                        keys.append(subkey)
                        i += 1
                    except OSError:
                        break
                return {
                    "keys": keys,
                    "count": len(keys),
                    "hive": hive_name,
                    "key_path": key_path
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _list_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List values of a registry key"""
        hive_name = params.get("hive", "HKEY_CURRENT_USER")
        key_path = params.get("key_path", "")
        
        hive = self._get_hive(hive_name)
        if not hive:
            return {"error": f"Invalid hive: {hive_name}"}
        
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                values = []
                i = 0
                while True:
                    try:
                        value_name, value, value_type = winreg.EnumValue(key, i)
                        values.append({
                            "name": value_name,
                            "value": value,
                            "type": value_type
                        })
                        i += 1
                    except OSError:
                        break
                return {
                    "values": values,
                    "count": len(values),
                    "hive": hive_name,
                    "key_path": key_path
                }
        except Exception as e:
            return {"error": str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = RegistryPlugin
PLUGIN_NAME = "registry"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Windows Registry operations"
PLUGIN_ACTIONS = ["read_key", "write_key", "delete_key", "list_keys", "list_values"]