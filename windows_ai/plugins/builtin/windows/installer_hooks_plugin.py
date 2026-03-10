"""
Windows Installer & Application Hooks Integration - PRODUCTION
Manage installed applications, MSI packages, installation logs, and app repairs.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsInstallerHooksPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_installer_hooks",
            name="Windows Installer & App Hooks",
            description=(
                "Manage Windows Installer (MSI) operations: list installed apps, install/uninstall "
                "MSI packages, view install logs, repair installations, and query app information."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "installer", "msi", "apps", "uninstall", "deployment"],
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        self.connected = False
        return True

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        actions = {
            "list_installed_apps": self._list_installed_apps,
            "install_msi": self._install_msi,
            "uninstall_app": self._uninstall_app,
            "get_install_logs": self._get_install_logs,
            "repair_install": self._repair_install,
            "get_app_info": self._get_app_info,
            "search_apps": self._search_apps,
            "get_msi_info": self._get_msi_info,
            "list_msi_transforms": self._list_msi_transforms,
            "get_install_location": self._get_install_location,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str, timeout: int = 60) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-NonInteractive", "-Command", cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "returncode": process.returncode,
            }
        except FileNotFoundError:
            return {"success": False, "error": "PowerShell not available on this system"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            logger.error(f"PowerShell error: {e}")
            return {"success": False, "error": str(e)}

    async def _list_installed_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all installed applications from the registry."""
        include_system = params.get("include_system", False)
        filter_str = params.get("filter", "")
        limit = params.get("limit", 200)

        cmd = f"""
$apps = @()
$regPaths = @(
    'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
)
foreach ($path in $regPaths) {{
    if (Test-Path $path) {{
        Get-ChildItem -Path $path -ErrorAction SilentlyContinue | ForEach-Object {{
            $props = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
            if ($props.DisplayName) {{
                $isSystem = $props.SystemComponent -eq 1
                if (-not $isSystem -or {str(include_system).lower()}) {{
                    if (-not '{filter_str}' -or $props.DisplayName -like '*{filter_str}*') {{
                        $apps += @{{
                            'name' = $props.DisplayName
                            'version' = $props.DisplayVersion
                            'publisher' = $props.Publisher
                            'install_date' = $props.InstallDate
                            'install_location' = $props.InstallLocation
                            'uninstall_string' = $props.UninstallString
                            'quiet_uninstall' = $props.QuietUninstallString
                            'size_mb' = if ($props.EstimatedSize) {{ [math]::Round($props.EstimatedSize / 1024, 1) }} else {{ $null }}
                            'guid' = $_.PSChildName
                            'system_component' = ($props.SystemComponent -eq 1)
                            'windows_installer' = ($props.WindowsInstaller -eq 1)
                        }}
                    }}
                }}
            }}
        }}
    }}
}}
$limited = $apps | Sort-Object name | Select-Object -First {limit}
@{{ 'apps' = $limited; 'count' = $limited.Count; 'total_found' = $apps.Count }} | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd, timeout=90)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _install_msi(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install an MSI package."""
        msi_path = params.get("msi_path")
        if not msi_path:
            return {"success": False, "error": "Parameter 'msi_path' is required"}
        if not os.path.exists(msi_path):
            return {"success": False, "error": f"MSI file not found: {msi_path}"}

        quiet = params.get("quiet", True)
        log_path = params.get("log_path", "")
        properties = params.get("properties", {})

        safe_msi = msi_path.replace('"', "")
        args = ["/i", f'"{safe_msi}"']
        if quiet:
            args.extend(["/qn", "/norestart"])
        if log_path:
            safe_log = log_path.replace('"', "")
            args.extend(["/l*v", f'"{safe_log}"'])

        for key, val in properties.items():
            safe_key = str(key).replace('"', "").replace("=", "")
            safe_val = str(val).replace('"', "")
            args.append(f'{safe_key}="{safe_val}"')

        try:
            proc = await asyncio.create_subprocess_exec(
                "msiexec.exe", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "msi_path": safe_msi,
                "note": "Exit code 3010 means success with reboot required",
            }
        except FileNotFoundError:
            return {"success": False, "error": "msiexec.exe not available"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "MSI installation timed out (10 minute limit)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _uninstall_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Uninstall an application by name or GUID."""
        app_name = params.get("app_name")
        guid = params.get("guid")
        quiet = params.get("quiet", True)

        if not app_name and not guid:
            return {"success": False, "error": "Either 'app_name' or 'guid' is required"}

        if guid:
            safe_guid = guid.replace('"', "").replace(";", "")
            args = ["/x", f"{{{safe_guid}}}" if not guid.startswith("{") else safe_guid]
            if quiet:
                args.extend(["/qn", "/norestart"])
            try:
                proc = await asyncio.create_subprocess_exec("msiexec.exe", *args,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
                return {
                    "success": proc.returncode == 0,
                    "returncode": proc.returncode,
                    "output": stdout.decode(errors="replace").strip(),
                    "error": stderr.decode(errors="replace").strip(),
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Find uninstall string by app name
        safe_name = app_name.replace("'", "''")
        cmd = f"""
$found = $false
$regPaths = @(
    'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
)
foreach ($path in $regPaths) {{
    if ($found) {{ break }}
    Get-ChildItem -Path $path -ErrorAction SilentlyContinue | ForEach-Object {{
        $props = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
        if ($props.DisplayName -like '*{safe_name}*') {{
            $uninstallStr = if ($props.QuietUninstallString) {{ $props.QuietUninstallString }} else {{ $props.UninstallString }}
            if ($uninstallStr) {{
                Write-Output $uninstallStr
                $found = $true
            }}
        }}
    }}
}}
if (-not $found) {{ Write-Error 'Application not found: {safe_name}' }}
"""
        result = await self._run_ps(cmd)
        if not result["success"] or not result["output"]:
            return {"success": False, "error": f"Application '{app_name}' not found"}

        uninstall_string = result["output"].strip().strip('"')
        # Execute the uninstall string
        cmd2 = f"Start-Process -FilePath 'cmd.exe' -ArgumentList '/c {uninstall_string}' -Wait -PassThru | Select-Object ExitCode | ConvertTo-Json"
        return await self._run_ps(cmd2, timeout=300)

    async def _get_install_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Windows Installer log files."""
        log_dir = params.get("log_dir", os.environ.get("TEMP", r"C:\Windows\Temp"))
        limit = params.get("limit", 20)
        safe_dir = log_dir.replace("'", "''")
        cmd = f"""
$logs = @()
@('{safe_dir}', "$env:TEMP", "$env:SystemRoot\\Temp") | Select-Object -Unique | ForEach-Object {{
    if (Test-Path $_) {{
        Get-ChildItem -Path $_ -Filter 'MSI*.log' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First {limit} |
            ForEach-Object {{
                $logs += @{{
                    'name' = $_.Name
                    'path' = $_.FullName
                    'size_kb' = [math]::Round($_.Length / 1KB, 1)
                    'modified' = $_.LastWriteTime.ToString('o')
                }}
            }}
    }}
}}
@{{ 'logs' = $logs; 'count' = $logs.Count }} | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _repair_install(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Repair an MSI installation."""
        guid = params.get("guid")
        msi_path = params.get("msi_path")
        if not guid and not msi_path:
            return {"success": False, "error": "Either 'guid' or 'msi_path' is required"}

        target = msi_path if msi_path else (f"{{{guid}}}" if not str(guid).startswith("{") else guid)
        safe_target = str(target).replace('"', "")
        try:
            proc = await asyncio.create_subprocess_exec(
                "msiexec.exe", "/fecms", f'"{safe_target}"', "/qn",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "target": safe_target,
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Repair timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_app_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about an installed application."""
        app_name = params.get("app_name")
        guid = params.get("guid")
        if not app_name and not guid:
            return {"success": False, "error": "Either 'app_name' or 'guid' is required"}

        filter_clause = (
            f"$_.PSChildName -eq '{guid.replace(chr(39), chr(39) * 2)}'" if guid
            else f"$props.DisplayName -like '*{app_name.replace(chr(39), chr(39) * 2)}*'"
        )
        cmd = f"""
$result = $null
$regPaths = @(
    'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall',
    'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall'
)
foreach ($path in $regPaths) {{
    if ($result) {{ break }}
    Get-ChildItem -Path $path -ErrorAction SilentlyContinue | ForEach-Object {{
        if ($result) {{ return }}
        $props = Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue
        if ({filter_clause}) {{
            $result = $props | Select-Object * -ExcludeProperty PS*
        }}
    }}
}}
if ($result) {{ $result | ConvertTo-Json -Depth 2 }} else {{ Write-Output '{{}}' }}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _search_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search installed apps by name pattern."""
        query = params.get("query", "")
        if not query:
            return {"success": False, "error": "Parameter 'query' is required"}
        return await self._list_installed_apps({"filter": query, "limit": 50, "include_system": False})

    async def _get_msi_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information from an MSI file without installing it."""
        msi_path = params.get("msi_path")
        if not msi_path:
            return {"success": False, "error": "Parameter 'msi_path' is required"}
        if not os.path.exists(msi_path):
            return {"success": False, "error": f"MSI file not found: {msi_path}"}

        safe_path = msi_path.replace("'", "''")
        cmd = f"""
try {{
    $installer = New-Object -ComObject WindowsInstaller.Installer
    $db = $installer.OpenDatabase('{safe_path}', 0)
    $props = @()
    $view = $db.OpenView("SELECT Property, Value FROM Property")
    $view.Execute()
    $record = $view.Fetch()
    while ($record) {{
        $props += @{{ 'property' = $record.StringData(1); 'value' = $record.StringData(2) }}
        $record = $view.Fetch()
    }}
    $props | ConvertTo-Json -Depth 2
}} catch {{
    @{{ 'error' = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _list_msi_transforms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List transforms applied to an MSI installation."""
        guid = params.get("guid")
        if not guid:
            return {"success": False, "error": "Parameter 'guid' is required"}
        safe_guid = guid.replace("'", "''").replace(";", "")
        cmd = f"""
try {{
    $installer = New-Object -ComObject WindowsInstaller.Installer
    $transforms = $installer.ComponentClients('{safe_guid}') 2>$null
    @{{ 'transforms' = @($transforms); 'guid' = '{safe_guid}' }} | ConvertTo-Json
}} catch {{
    @{{ 'error' = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_install_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the installation directory for an application."""
        app_name = params.get("app_name")
        guid = params.get("guid")
        info_result = await self._get_app_info({"app_name": app_name, "guid": guid})
        if not info_result.get("success"):
            return info_result
        data = info_result.get("data", {})
        location = data.get("InstallLocation") or data.get("InstallDir")
        return {
            "success": bool(location),
            "install_location": location,
            "app_name": data.get("DisplayName"),
            "error": None if location else "Install location not recorded in registry",
        }

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "list_installed_apps": {"description": "List installed applications", "params": {"filter": "str", "limit": "int"}},
                "install_msi": {"description": "Install MSI package", "params": {"msi_path": "str", "quiet": "bool", "log_path": "str"}},
                "uninstall_app": {"description": "Uninstall application", "params": {"app_name": "str", "guid": "str", "quiet": "bool"}},
                "get_install_logs": {"description": "Get MSI install log files", "params": {"log_dir": "str"}},
                "repair_install": {"description": "Repair MSI installation", "params": {"guid": "str", "msi_path": "str"}},
                "get_app_info": {"description": "Get application details", "params": {"app_name": "str", "guid": "str"}},
                "search_apps": {"description": "Search installed apps", "params": {"query": "str"}},
                "get_msi_info": {"description": "Read MSI file properties", "params": {"msi_path": "str"}},
                "get_install_location": {"description": "Get app install directory", "params": {"app_name": "str", "guid": "str"}},
            },
        }


plugin = WindowsInstallerHooksPlugin()
