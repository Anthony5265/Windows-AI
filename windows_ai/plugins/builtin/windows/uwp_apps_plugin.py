"""
Windows Universal Windows Platform (UWP) Apps Integration - PRODUCTION
Manage UWP/MSIX applications: list, install, uninstall, reset, repair, query packages.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsUWPAppsPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_uwp_apps",
            name="Windows UWP Apps Manager",
            description=(
                "Manage Universal Windows Platform (UWP/MSIX) apps: list installed packages, "
                "install/uninstall/reset/repair apps, query package info and capabilities."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "uwp", "msix", "appx", "store", "packages"],
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
            "list_uwp_apps": self._list_uwp_apps,
            "install_uwp_app": self._install_uwp_app,
            "uninstall_uwp_app": self._uninstall_uwp_app,
            "get_uwp_info": self._get_uwp_info,
            "reset_uwp_app": self._reset_uwp_app,
            "repair_uwp_app": self._repair_uwp_app,
            "list_packages": self._list_packages,
            "get_package_capabilities": self._get_package_capabilities,
            "enable_sideloading": self._enable_sideloading,
            "register_package": self._register_package,
            "get_package_dependencies": self._get_package_dependencies,
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

    async def _list_uwp_apps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List installed UWP/MSIX apps for current user."""
        filter_str = params.get("filter", "")
        all_users = params.get("all_users", False)
        limit = params.get("limit", 100)
        scope_flag = "-AllUsers" if all_users else ""
        cmd = f"""
$packages = Get-AppxPackage {scope_flag} -ErrorAction SilentlyContinue |
    Where-Object {{ -not '{filter_str}' -or $_.Name -like '*{filter_str}*' -or $_.Publisher -like '*{filter_str}*' }} |
    Select-Object -First {limit} |
    ForEach-Object {{
        @{{
            'name' = $_.Name
            'package_full_name' = $_.PackageFullName
            'publisher' = $_.Publisher
            'version' = $_.Version.ToString()
            'architecture' = $_.Architecture.ToString()
            'install_location' = $_.InstallLocation
            'is_framework' = $_.IsFramework
            'is_bundle' = $_.IsBundle
            'is_resource_package' = $_.IsResourcePackage
            'status' = $_.Status.ToString()
            'package_family_name' = $_.PackageFamilyName
        }}
    }}
@{{ 'apps' = @($packages); 'count' = @($packages).Count }} | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _install_uwp_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install a UWP/MSIX app from a file path or URL."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Parameter 'path' (MSIX/APPX file path or URL) is required"}
        safe_path = path.replace("'", "''")
        cmd = f"""
try {{
    Add-AppxPackage -Path '{safe_path}' -ErrorAction Stop
    Write-Output 'Package installed successfully'
}} catch {{
    Write-Error $_.Exception.Message
}}
"""
        return await self._run_ps(cmd, timeout=300)

    async def _uninstall_uwp_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Uninstall a UWP app by name or package full name."""
        app_name = params.get("app_name")
        package_full_name = params.get("package_full_name")
        all_users = params.get("all_users", False)
        if not app_name and not package_full_name:
            return {"success": False, "error": "Either 'app_name' or 'package_full_name' is required"}

        if package_full_name:
            safe_pkg = package_full_name.replace("'", "''")
            all_flag = "-AllUsers" if all_users else ""
            cmd = f"Remove-AppxPackage -Package '{safe_pkg}' {all_flag} -ErrorAction Stop; Write-Output 'Uninstalled'"
        else:
            safe_name = app_name.replace("'", "''")
            all_flag = "-AllUsers" if all_users else ""
            cmd = f"""
$pkg = Get-AppxPackage -Name '*{safe_name}*' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {{
    Remove-AppxPackage -Package $pkg.PackageFullName {all_flag} -ErrorAction Stop
    Write-Output "Uninstalled: $($pkg.Name)"
}} else {{
    Write-Error 'Package not found: {safe_name}'
}}
"""
        return await self._run_ps(cmd, timeout=120)

    async def _get_uwp_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed info about a UWP app."""
        app_name = params.get("app_name")
        package_full_name = params.get("package_full_name")
        if not app_name and not package_full_name:
            return {"success": False, "error": "Either 'app_name' or 'package_full_name' is required"}

        filter_clause = (
            f"-Name '{package_full_name.replace(chr(39), chr(39)*2)}'" if package_full_name
            else f"-Name '*{app_name.replace(chr(39), chr(39)*2)}*'"
        )
        cmd = f"""
$pkg = Get-AppxPackage {filter_clause} -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {{
    $manifest = $null
    try {{
        $manifestPath = Join-Path $pkg.InstallLocation 'AppxManifest.xml'
        if (Test-Path $manifestPath) {{
            [xml]$manifest = Get-Content $manifestPath -ErrorAction SilentlyContinue
            $displayName = $manifest.Package.Properties.DisplayName
        }}
    }} catch {{}}
    @{{
        'name' = $pkg.Name
        'package_full_name' = $pkg.PackageFullName
        'package_family_name' = $pkg.PackageFamilyName
        'publisher' = $pkg.Publisher
        'publisher_id' = $pkg.PublisherId
        'version' = $pkg.Version.ToString()
        'architecture' = $pkg.Architecture.ToString()
        'install_location' = $pkg.InstallLocation
        'is_framework' = $pkg.IsFramework
        'is_bundle' = $pkg.IsBundle
        'status' = $pkg.Status.ToString()
        'sign_certificate' = $pkg.SignatureCertificationAlgorithm
        'dependencies' = @($pkg.Dependencies | ForEach-Object {{ $_.FullName }})
    }} | ConvertTo-Json -Depth 3
}} else {{
    @{{'error' = 'Package not found'}} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _reset_uwp_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset a UWP app (clear its data)."""
        app_name = params.get("app_name")
        if not app_name:
            return {"success": False, "error": "Parameter 'app_name' is required"}
        safe_name = app_name.replace("'", "''")
        cmd = f"""
$pkg = Get-AppxPackage -Name '*{safe_name}*' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {{
    $localAppData = [Environment]::GetFolderPath('LocalApplicationData')
    $appDataPath = Join-Path $localAppData "Packages\\$($pkg.PackageFamilyName)"
    if (Test-Path $appDataPath) {{
        @('LocalState', 'TempState', 'LocalCache') | ForEach-Object {{
            $subPath = Join-Path $appDataPath $_
            if (Test-Path $subPath) {{
                Get-ChildItem $subPath | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            }}
        }}
        Write-Output "Reset app data for: $($pkg.Name)"
    }} else {{
        Write-Output "No app data found for: $($pkg.Name)"
    }}
}} else {{
    Write-Error 'Package not found: {safe_name}'
}}
"""
        return await self._run_ps(cmd)

    async def _repair_uwp_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Repair/re-register a UWP app."""
        app_name = params.get("app_name")
        if not app_name:
            return {"success": False, "error": "Parameter 'app_name' is required"}
        safe_name = app_name.replace("'", "''")
        cmd = f"""
$pkg = Get-AppxPackage -Name '*{safe_name}*' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {{
    $manifest = Join-Path $pkg.InstallLocation 'AppxManifest.xml'
    if (Test-Path $manifest) {{
        Add-AppxPackage -Register -Path $manifest -DisableDevelopmentMode -ErrorAction Stop
        Write-Output "Re-registered: $($pkg.Name)"
    }} else {{
        Write-Error 'Manifest not found at install location'
    }}
}} else {{
    Write-Error 'Package not found: {safe_name}'
}}
"""
        return await self._run_ps(cmd, timeout=120)

    async def _list_packages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all AppX packages including provisioned packages."""
        include_provisioned = params.get("include_provisioned", False)
        limit = params.get("limit", 100)
        cmd = f"""
$pkgs = Get-AppxPackage -ErrorAction SilentlyContinue | Select-Object -First {limit} |
    Select-Object Name, Version, Architecture, PackageFullName, InstallLocation, Status
$result = @{{ 'packages' = @($pkgs | ConvertTo-Json -Depth 1 | ConvertFrom-Json); 'count' = @($pkgs).Count }}
"""
        if include_provisioned:
            cmd += r"""
$prov = Get-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue |
    Select-Object DisplayName, PackageName, Version
$result['provisioned'] = @($prov)
$result['provisioned_count'] = @($prov).Count
"""
        cmd += "$result | ConvertTo-Json -Depth 3"
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_package_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get capabilities declared in a UWP package manifest."""
        app_name = params.get("app_name")
        if not app_name:
            return {"success": False, "error": "Parameter 'app_name' is required"}
        safe_name = app_name.replace("'", "''")
        cmd = f"""
$pkg = Get-AppxPackage -Name '*{safe_name}*' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {{
    $manifestPath = Join-Path $pkg.InstallLocation 'AppxManifest.xml'
    if (Test-Path $manifestPath) {{
        [xml]$manifest = Get-Content $manifestPath
        $ns = @{{m='http://schemas.microsoft.com/appx/manifest/foundation/windows10'}}
        $caps = $manifest.Package.Capabilities
        $result = @{{
            'app_name' = $pkg.Name
            'capabilities' = @($caps.ChildNodes | ForEach-Object {{ $_.Name + ': ' + $_.InnerText }})
        }}
    }} else {{
        $result = @{{'error' = 'Manifest not found'}}
    }}
}} else {{
    $result = @{{'error' = 'Package not found: {safe_name}'}}
}}
$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _enable_sideloading(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable app sideloading (developer mode or sideloading policy)."""
        cmd = r"""
# Enable sideloading via registry
$devModePath = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock'
if (-not (Test-Path $devModePath)) { New-Item -Path $devModePath -Force | Out-Null }
Set-ItemProperty -Path $devModePath -Name 'AllowAllTrustedApps' -Value 1 -Type DWord -Force
Set-ItemProperty -Path $devModePath -Name 'AllowDevelopmentWithoutDevLicense' -Value 0 -Type DWord -Force
Write-Output 'Sideloading (trusted apps) enabled. Restart may be required.'
"""
        return await self._run_ps(cmd)

    async def _register_package(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register an AppX package from a manifest file (developer mode)."""
        manifest_path = params.get("manifest_path")
        if not manifest_path:
            return {"success": False, "error": "Parameter 'manifest_path' is required"}
        safe_path = manifest_path.replace("'", "''")
        cmd = f"Add-AppxPackage -Register -Path '{safe_path}' -DisableDevelopmentMode; Write-Output 'Registered'"
        return await self._run_ps(cmd, timeout=120)

    async def _get_package_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get dependencies for a UWP package."""
        app_name = params.get("app_name")
        if not app_name:
            return {"success": False, "error": "Parameter 'app_name' is required"}
        safe_name = app_name.replace("'", "''")
        cmd = f"""
$pkg = Get-AppxPackage -Name '*{safe_name}*' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pkg) {{
    @{{
        'app_name' = $pkg.Name
        'dependencies' = @($pkg.Dependencies | ForEach-Object {{ @{{'full_name'=$_.FullName; 'publisher'=$_.Publisher; 'version'=$_.Version.ToString()}} }})
        'dependency_count' = $pkg.Dependencies.Count
    }} | ConvertTo-Json -Depth 3
}} else {{
    @{{'error' = 'Package not found: {safe_name}'}} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "list_uwp_apps": {"description": "List UWP apps", "params": {"filter": "str", "all_users": "bool", "limit": "int"}},
                "install_uwp_app": {"description": "Install MSIX/APPX", "params": {"path": "str"}},
                "uninstall_uwp_app": {"description": "Uninstall UWP app", "params": {"app_name": "str", "package_full_name": "str"}},
                "get_uwp_info": {"description": "Get app info", "params": {"app_name": "str", "package_full_name": "str"}},
                "reset_uwp_app": {"description": "Reset app data", "params": {"app_name": "str"}},
                "repair_uwp_app": {"description": "Re-register/repair app", "params": {"app_name": "str"}},
                "list_packages": {"description": "List all packages", "params": {"include_provisioned": "bool", "limit": "int"}},
                "get_package_capabilities": {"description": "Get package capabilities", "params": {"app_name": "str"}},
                "enable_sideloading": {"description": "Enable app sideloading"},
                "register_package": {"description": "Register from manifest", "params": {"manifest_path": "str"}},
                "get_package_dependencies": {"description": "Get package dependencies", "params": {"app_name": "str"}},
            },
        }


plugin = WindowsUWPAppsPlugin()
