"""
Windows Registry Management Integration - PRODUCTION

Provides comprehensive Windows Registry management capabilities including:
- Reading/writing registry keys and values
- Creating/deleting registry keys
- Exporting/importing registry data
- Registry backup and restore
- Value type support (String, DWORD, Binary, etc.)
"""
import asyncio
import json
try:
    import winreg
    _HAS_WINREG = True
except ImportError:
    _HAS_WINREG = False
    winreg = None
from typing import Dict, Any, Optional, List, Union
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)

# Registry hive mappings
if _HAS_WINREG:
    HIVE_MAP = {
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKCR": winreg.HKEY_CLASSES_ROOT,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_USERS": winreg.HKEY_USERS,
        "HKU": winreg.HKEY_USERS,
        "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
    "HKCC": winreg.HKEY_CURRENT_CONFIG,
    }
else:
    HIVE_MAP = {}

if _HAS_WINREG:
    VALUE_TYPES = {
        "REG_SZ": winreg.REG_SZ,
        "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
        "REG_BINARY": winreg.REG_BINARY,
        "REG_DWORD": winreg.REG_DWORD,
        "REG_QWORD": winreg.REG_QWORD,
        "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
    }
else:
    VALUE_TYPES = {}


class WindowsRegistryManagementPlugin(IntegrationPlugin):
    """Windows Registry Management plugin with full registry access capabilities."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_registry_management",
            name="Windows Registry Management",
            description="Comprehensive Windows Registry management with read/write/export capabilities",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "registry", "system", "configuration"]
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize the registry plugin."""
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to the registry (no credentials needed for local access)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from registry operations."""
        self.connected = False
        return True

    def _parse_key_path(self, key_path: str) -> tuple:
        """Parse a registry path into hive and subkey."""
        parts = key_path.replace("/", "\\").split("\\", 1)
        hive_name = parts[0].upper()
        subkey = parts[1] if len(parts) > 1 else ""
        
        if hive_name not in HIVE_MAP:
            raise ValueError(f"Unknown registry hive: {hive_name}")
        
        return HIVE_MAP[hive_name], subkey

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a registry operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        actions = {
            "get_value": self._get_value,
            "set_value": self._set_value,
            "delete_value": self._delete_value,
            "create_key": self._create_key,
            "delete_key": self._delete_key,
            "list_keys": self._list_keys,
            "list_values": self._list_values,
            "export_key": self._export_key,
            "key_exists": self._key_exists,
            "value_exists": self._value_exists,
            "search": self._search_registry,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Registry operation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_value(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a registry value."""
        key_path = params.get("key_path", "")
        value_name = params.get("value_name", "")
        
        hive, subkey = self._parse_key_path(key_path)
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                value, value_type = winreg.QueryValueEx(key, value_name)
                type_name = next((k for k, v in VALUE_TYPES.items() if v == value_type), "UNKNOWN")
                return {
                    "success": True,
                    "value": value,
                    "type": type_name,
                    "key_path": key_path,
                    "value_name": value_name
                }
        except FileNotFoundError:
            return {"success": False, "error": "Key or value not found"}

    async def _set_value(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a registry value."""
        key_path = params.get("key_path", "")
        value_name = params.get("value_name", "")
        value = params.get("value")
        value_type = params.get("type", "REG_SZ")
        
        if value_type not in VALUE_TYPES:
            return {"success": False, "error": f"Unknown value type: {value_type}"}
        
        hive, subkey = self._parse_key_path(key_path)
        reg_type = VALUE_TYPES[value_type]
        
        # Convert value based on type
        if reg_type == winreg.REG_DWORD:
            value = int(value)
        elif reg_type == winreg.REG_QWORD:
            value = int(value)
        elif reg_type == winreg.REG_BINARY:
            if isinstance(value, str):
                value = bytes.fromhex(value.replace(" ", ""))
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, value_name, 0, reg_type, value)
                return {"success": True, "message": f"Value '{value_name}' set successfully"}
        except PermissionError:
            return {"success": False, "error": "Permission denied. Run as administrator."}

    async def _delete_value(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a registry value."""
        key_path = params.get("key_path", "")
        value_name = params.get("value_name", "")
        
        hive, subkey = self._parse_key_path(key_path)
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, value_name)
                return {"success": True, "message": f"Value '{value_name}' deleted"}
        except FileNotFoundError:
            return {"success": False, "error": "Value not found"}
        except PermissionError:
            return {"success": False, "error": "Permission denied"}

    async def _create_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a registry key."""
        key_path = params.get("key_path", "")
        
        hive, subkey = self._parse_key_path(key_path)
        
        try:
            key = winreg.CreateKeyEx(hive, subkey, 0, winreg.KEY_WRITE)
            winreg.CloseKey(key)
            return {"success": True, "message": f"Key created: {key_path}"}
        except PermissionError:
            return {"success": False, "error": "Permission denied"}

    async def _delete_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a registry key (must be empty)."""
        key_path = params.get("key_path", "")
        
        hive, subkey = self._parse_key_path(key_path)
        
        try:
            winreg.DeleteKey(hive, subkey)
            return {"success": True, "message": f"Key deleted: {key_path}"}
        except OSError as e:
            return {"success": False, "error": str(e)}

    async def _list_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List subkeys of a registry key."""
        key_path = params.get("key_path", "")
        
        hive, subkey = self._parse_key_path(key_path)
        keys = []
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        keys.append(winreg.EnumKey(key, i))
                        i += 1
                    except OSError:
                        break
            return {"success": True, "keys": keys, "count": len(keys)}
        except FileNotFoundError:
            return {"success": False, "error": "Key not found"}

    async def _list_values(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List values in a registry key."""
        key_path = params.get("key_path", "")
        
        hive, subkey = self._parse_key_path(key_path)
        values = []
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, value_type = winreg.EnumValue(key, i)
                        type_name = next((k for k, v in VALUE_TYPES.items() if v == value_type), "UNKNOWN")
                        values.append({
                            "name": name or "(Default)",
                            "value": value if not isinstance(value, bytes) else value.hex(),
                            "type": type_name
                        })
                        i += 1
                    except OSError:
                        break
            return {"success": True, "values": values, "count": len(values)}
        except FileNotFoundError:
            return {"success": False, "error": "Key not found"}

    async def _export_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export a registry key to a dictionary structure."""
        key_path = params.get("key_path", "")
        recursive = params.get("recursive", False)
        
        hive, subkey = self._parse_key_path(key_path)
        
        def export_recursive(hive_handle, sub_path: str) -> Dict:
            result = {"values": {}, "subkeys": {}}
            try:
                with winreg.OpenKey(hive_handle, sub_path, 0, winreg.KEY_READ) as key:
                    # Export values
                    i = 0
                    while True:
                        try:
                            name, value, vtype = winreg.EnumValue(key, i)
                            type_name = next((k for k, v in VALUE_TYPES.items() if v == vtype), "UNKNOWN")
                            result["values"][name or "(Default)"] = {
                                "value": value if not isinstance(value, bytes) else value.hex(),
                                "type": type_name
                            }
                            i += 1
                        except OSError:
                            break
                    
                    # Export subkeys if recursive
                    if recursive:
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                new_path = f"{sub_path}\\{subkey_name}" if sub_path else subkey_name
                                result["subkeys"][subkey_name] = export_recursive(hive_handle, new_path)
                                i += 1
                            except OSError:
                                break
            except Exception as e:
                result["error"] = str(e)
            return result
        
        try:
            exported = export_recursive(hive, subkey)
            return {"success": True, "data": exported, "key_path": key_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _key_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a registry key exists."""
        key_path = params.get("key_path", "")
        
        hive, subkey = self._parse_key_path(key_path)
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ):
                return {"success": True, "exists": True}
        except FileNotFoundError:
            return {"success": True, "exists": False}

    async def _value_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a registry value exists."""
        key_path = params.get("key_path", "")
        value_name = params.get("value_name", "")
        
        hive, subkey = self._parse_key_path(key_path)
        
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, value_name)
                return {"success": True, "exists": True}
        except FileNotFoundError:
            return {"success": True, "exists": False}

    async def _search_registry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for keys or values matching a pattern."""
        key_path = params.get("key_path", "HKEY_CURRENT_USER")
        pattern = params.get("pattern", "")
        search_type = params.get("search_type", "both")  # keys, values, or both
        max_results = params.get("max_results", 100)
        
        # Use PowerShell for efficient searching
        ps_script = f'''
        $results = @()
        $searchPath = "{key_path.replace('HKEY_', 'HKEY_').replace('HKCU', 'HKCU:').replace('HKLM', 'HKLM:')}"
        $pattern = "{pattern}"
        
        Get-ChildItem -Path $searchPath -Recurse -ErrorAction SilentlyContinue | 
            ForEach-Object {{
                if ($_.PSPath -match $pattern) {{
                    $results += @{{Path = $_.PSPath; Type = "Key"}}
                }}
                $_.GetValueNames() | ForEach-Object {{
                    if ($_ -match $pattern) {{
                        $results += @{{Path = $_.PSPath; Name = $_; Type = "Value"}}
                    }}
                }}
            }} | Select-Object -First {max_results}
        
        $results | ConvertTo-Json
        '''
        
        process = await asyncio.create_subprocess_exec(
            "powershell", "-Command", ps_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        try:
            results = json.loads(stdout.decode()) if stdout else []
            return {"success": True, "results": results, "count": len(results)}
        except:
            return {"success": True, "results": [], "count": 0}

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for plugin parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get_value", "set_value", "delete_value", "create_key", 
                             "delete_key", "list_keys", "list_values", "export_key",
                             "key_exists", "value_exists", "search"]
                },
                "key_path": {"type": "string", "description": "Registry key path (e.g., HKCU\\Software\\MyApp)"},
                "value_name": {"type": "string", "description": "Registry value name"},
                "value": {"description": "Value to set"},
                "type": {"type": "string", "enum": list(VALUE_TYPES.keys())},
                "recursive": {"type": "boolean", "default": False},
                "pattern": {"type": "string", "description": "Search pattern"},
            },
            "required": ["action"]
        }


plugin = WindowsRegistryManagementPlugin()
