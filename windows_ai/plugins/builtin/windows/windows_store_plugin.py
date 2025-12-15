"""
Windows Store Plugin for Windows AI
Comprehensive Microsoft Store and UWP package management
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional, List

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType


class WindowsStorePlugin(IntegrationPlugin):
    """Plugin for Microsoft Store and AppX/MSIX package management"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows-store",
            name="Windows Store Manager",
            description="Comprehensive Microsoft Store and UWP package management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "store", "appx", "msix", "uwp", "packages"],
        )
        super().__init__(metadata)
        self.logger = logging.getLogger(__name__)
        self._actions = {
            # Package listing and info
            "list_packages": self._list_packages,
            "list_all_packages": self._list_all_packages,
            "get_package": self._get_package,
            "get_package_manifest": self._get_package_manifest,
            "search_packages": self._search_packages,
            "get_package_files": self._get_package_files,
            "get_package_location": self._get_package_location,
            # Package installation
            "install_package": self._install_package,
            "install_from_store": self._install_from_store,
            "install_appx": self._install_appx,
            "install_msix": self._install_msix,
            "install_bundle": self._install_bundle,
            "install_dev_package": self._install_dev_package,
            "register_package": self._register_package,
            # Package removal
            "remove_package": self._remove_package,
            "remove_all_versions": self._remove_all_versions,
            "remove_provisioned": self._remove_provisioned,
            # Package updates
            "check_updates": self._check_updates,
            "update_package": self._update_package,
            "update_all_packages": self._update_all_packages,
            # Provisioned packages
            "list_provisioned": self._list_provisioned,
            "add_provisioned": self._add_provisioned,
            "remove_provisioned_package": self._remove_provisioned_package,
            # Package staging
            "stage_package": self._stage_package,
            "list_staged": self._list_staged,
            # Volume management
            "list_volumes": self._list_volumes,
            "get_volume": self._get_volume,
            "set_default_volume": self._set_default_volume,
            "move_package": self._move_package,
            # Developer mode
            "enable_dev_mode": self._enable_dev_mode,
            "disable_dev_mode": self._disable_dev_mode,
            "get_dev_mode_status": self._get_dev_mode_status,
            "enable_sideloading": self._enable_sideloading,
            # App execution aliases
            "list_aliases": self._list_aliases,
            "get_alias": self._get_alias,
            # Capabilities
            "get_capabilities": self._get_capabilities,
            "list_restricted_capabilities": self._list_restricted_capabilities,
            # Dependencies
            "get_dependencies": self._get_dependencies,
            "get_dependents": self._get_dependents,
            # App reset and repair
            "reset_package": self._reset_package,
            "repair_package": self._repair_package,
            # Store cache
            "reset_store_cache": self._reset_store_cache,
            "clear_store_cache": self._clear_store_cache,
            # App launch
            "launch_app": self._launch_app,
            "get_app_uri": self._get_app_uri,
            # Logs and diagnostics
            "get_package_log": self._get_package_log,
            "get_install_errors": self._get_install_errors,
            # Store status
            "get_store_status": self._get_store_status,
            "check_store_connectivity": self._check_store_connectivity,
        }

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info("Initializing Windows Store plugin")
        return True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Windows Store operations"""
        action = kwargs.get("action", "list_packages")
        params = kwargs.get("params", {})
        
        if action in self._actions:
            try:
                return await self._actions[action](**params)
            except Exception as e:
                self.logger.error(f"Error executing {action}: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Unknown action: {action}", "available_actions": list(self._actions.keys())}

    async def _run_powershell(self, command: str, as_admin: bool = False) -> Dict[str, Any]:
        """Run a PowerShell command and return results"""
        try:
            if as_admin:
                full_cmd = f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -Command {command}' -Wait"
            else:
                full_cmd = command
            
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", full_cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {"success": True, "output": stdout.decode("utf-8", errors="replace").strip()}
            else:
                return {"success": False, "error": stderr.decode("utf-8", errors="replace").strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Package listing and info
    async def _list_packages(self, publisher: str = None, name_filter: str = None, **kwargs) -> Dict[str, Any]:
        """List installed packages for current user"""
        filter_cmd = ""
        if publisher:
            filter_cmd += f" | Where-Object {{ $_.Publisher -like '*{publisher}*' }}"
        if name_filter:
            filter_cmd += f" | Where-Object {{ $_.Name -like '*{name_filter}*' }}"
        
        cmd = f"""
        Get-AppxPackage{filter_cmd} | 
        Select-Object Name, PackageFullName, Version, Publisher, InstallLocation, Status, Architecture |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _list_all_packages(self, **kwargs) -> Dict[str, Any]:
        """List all packages for all users"""
        cmd = """
        Get-AppxPackage -AllUsers | 
        Select-Object Name, PackageFullName, Version, Publisher, InstallLocation, PackageUserInformation |
        ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_package(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get detailed info about a specific package"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            [PSCustomObject]@{{
                Name = $pkg.Name
                PackageFullName = $pkg.PackageFullName
                Version = $pkg.Version.ToString()
                Publisher = $pkg.Publisher
                PublisherId = $pkg.PublisherId
                Architecture = $pkg.Architecture.ToString()
                InstallLocation = $pkg.InstallLocation
                IsFramework = $pkg.IsFramework
                IsBundle = $pkg.IsBundle
                IsDevelopmentMode = $pkg.IsDevelopmentMode
                IsPartiallyStaged = $pkg.IsPartiallyStaged
                NonRemovable = $pkg.NonRemovable
                SignatureKind = $pkg.SignatureKind.ToString()
                Status = $pkg.Status.ToString()
                Dependencies = @($pkg.Dependencies | ForEach-Object {{ $_.FullName }})
            }} | ConvertTo-Json -Depth 2
        }} else {{
            throw "Package not found: {package_name}"
        }}
        """
        return await self._run_powershell(cmd)

    async def _get_package_manifest(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get package manifest content"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            $manifestPath = Join-Path $pkg.InstallLocation 'AppxManifest.xml'
            if (Test-Path $manifestPath) {{
                Get-Content $manifestPath -Raw
            }} else {{
                throw "Manifest not found"
            }}
        }} else {{
            throw "Package not found: {package_name}"
        }}
        """
        return await self._run_powershell(cmd)

    async def _search_packages(self, query: str, include_system: bool = False, **kwargs) -> Dict[str, Any]:
        """Search packages by name or publisher"""
        all_users = "-AllUsers" if include_system else ""
        cmd = f"""
        Get-AppxPackage {all_users} | 
        Where-Object {{ $_.Name -like '*{query}*' -or $_.Publisher -like '*{query}*' }} |
        Select-Object Name, PackageFullName, Version, Publisher |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_package_files(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """List files in a package"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            Get-ChildItem $pkg.InstallLocation -Recurse -File | 
            Select-Object -First 100 Name, FullName, Length, LastWriteTime |
            ConvertTo-Json -Depth 2
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    async def _get_package_location(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get package installation location"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            [PSCustomObject]@{{
                Name = $pkg.Name
                InstallLocation = $pkg.InstallLocation
                Exists = (Test-Path $pkg.InstallLocation)
            }} | ConvertTo-Json
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    # Package installation
    async def _install_package(self, path: str, **kwargs) -> Dict[str, Any]:
        """Install a package from path (AppX or MSIX)"""
        cmd = f"""
        Add-AppxPackage -Path '{path}'
        @{{ success = $true; message = "Package installed successfully" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _install_from_store(self, product_id: str, **kwargs) -> Dict[str, Any]:
        """Install app from Microsoft Store by product ID"""
        cmd = f"""
        $uri = "ms-windows-store://pdp/?ProductId={product_id}"
        Start-Process $uri
        @{{ success = $true; message = "Store opened for product {product_id}" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _install_appx(self, path: str, dependencies: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Install AppX package with optional dependencies"""
        deps_cmd = ""
        if dependencies:
            deps_list = "', '".join(dependencies)
            deps_cmd = f"-DependencyPath '{deps_list}'"
        
        cmd = f"""
        Add-AppxPackage -Path '{path}' {deps_cmd}
        @{{ success = $true; message = "AppX package installed" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _install_msix(self, path: str, allow_unsigned: bool = False, **kwargs) -> Dict[str, Any]:
        """Install MSIX package"""
        unsigned_flag = "-AllowUnsigned" if allow_unsigned else ""
        cmd = f"""
        Add-AppxPackage -Path '{path}' {unsigned_flag}
        @{{ success = $true; message = "MSIX package installed" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _install_bundle(self, path: str, **kwargs) -> Dict[str, Any]:
        """Install AppX bundle"""
        cmd = f"""
        Add-AppxPackage -Path '{path}'
        @{{ success = $true; message = "Bundle installed" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _install_dev_package(self, path: str, **kwargs) -> Dict[str, Any]:
        """Install development package with sideloading"""
        cmd = f"""
        Add-AppxPackage -Path '{path}' -AllowUnsigned -DevelopmentMode
        @{{ success = $true; message = "Development package installed" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _register_package(self, manifest_path: str, **kwargs) -> Dict[str, Any]:
        """Register a package from manifest"""
        cmd = f"""
        Add-AppxPackage -Register '{manifest_path}' -DisableDevelopmentMode
        @{{ success = $true; message = "Package registered" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Package removal
    async def _remove_package(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Remove a package"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            Remove-AppxPackage -Package $pkg.PackageFullName
            @{{ success = $true; message = "Package removed: $($pkg.Name)" }} | ConvertTo-Json
        }} else {{
            throw "Package not found: {package_name}"
        }}
        """
        return await self._run_powershell(cmd)

    async def _remove_all_versions(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Remove all versions of a package"""
        cmd = f"""
        $packages = Get-AppxPackage -Name '*{package_name}*'
        $count = $packages.Count
        $packages | Remove-AppxPackage
        @{{ success = $true; message = "Removed $count packages" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _remove_provisioned(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Remove provisioned package"""
        cmd = f"""
        $pkg = Get-AppxProvisionedPackage -Online | Where-Object {{ $_.PackageName -like '*{package_name}*' }} | Select-Object -First 1
        if ($pkg) {{
            Remove-AppxProvisionedPackage -Online -PackageName $pkg.PackageName
            @{{ success = $true; message = "Provisioned package removed" }} | ConvertTo-Json
        }} else {{
            throw "Provisioned package not found"
        }}
        """
        return await self._run_powershell(cmd)

    # Package updates
    async def _check_updates(self, **kwargs) -> Dict[str, Any]:
        """Check for available updates"""
        cmd = """
        $namespace = "Windows.ApplicationModel.Store.Preview.InstallControl"
        Add-Type -AssemblyName "$namespace"
        @{ success = $true; message = "Update check initiated via Store" } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _update_package(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Update a specific package"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            Add-AppxPackage -Path $pkg.InstallLocation -Update
            @{{ success = $true; message = "Update initiated for $($pkg.Name)" }} | ConvertTo-Json
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    async def _update_all_packages(self, **kwargs) -> Dict[str, Any]:
        """Trigger update for all packages via Store"""
        cmd = """
        Start-Process "ms-windows-store://downloadsandupdates"
        @{ success = $true; message = "Store updates page opened" } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Provisioned packages
    async def _list_provisioned(self, **kwargs) -> Dict[str, Any]:
        """List provisioned packages (for new users)"""
        cmd = """
        Get-AppxProvisionedPackage -Online | 
        Select-Object DisplayName, PackageName, Version, Architecture |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _add_provisioned(self, path: str, **kwargs) -> Dict[str, Any]:
        """Add provisioned package"""
        cmd = f"""
        Add-AppxProvisionedPackage -Online -PackagePath '{path}'
        @{{ success = $true; message = "Provisioned package added" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _remove_provisioned_package(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Remove provisioned package by name"""
        cmd = f"""
        Get-AppxProvisionedPackage -Online | 
        Where-Object {{ $_.DisplayName -like '*{package_name}*' }} |
        Remove-AppxProvisionedPackage -Online
        @{{ success = $true; message = "Provisioned package removed" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # Package staging
    async def _stage_package(self, path: str, **kwargs) -> Dict[str, Any]:
        """Stage a package for installation"""
        cmd = f"""
        Add-AppxPackage -Path '{path}' -Stage
        @{{ success = $true; message = "Package staged" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _list_staged(self, **kwargs) -> Dict[str, Any]:
        """List staged packages"""
        cmd = """
        Get-AppxPackage -PackageTypeFilter Main | 
        Where-Object { $_.IsPartiallyStaged -eq $true } |
        Select-Object Name, PackageFullName, Status |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    # Volume management
    async def _list_volumes(self, **kwargs) -> Dict[str, Any]:
        """List package volumes"""
        cmd = """
        Get-AppxVolume | 
        Select-Object Name, PackageStorePath, IsSystemVolume, IsOffline, SupportsHardLinks |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_volume(self, volume_path: str, **kwargs) -> Dict[str, Any]:
        """Get specific volume info"""
        cmd = f"""
        Get-AppxVolume -Path '{volume_path}' | 
        Select-Object * |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _set_default_volume(self, volume_path: str, **kwargs) -> Dict[str, Any]:
        """Set default volume for new packages"""
        cmd = f"""
        Set-AppxDefaultVolume -Path '{volume_path}'
        @{{ success = $true; message = "Default volume set" }} | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _move_package(self, package_name: str, volume_path: str, **kwargs) -> Dict[str, Any]:
        """Move package to different volume"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            Move-AppxPackage -Package $pkg.PackageFullName -Volume '{volume_path}'
            @{{ success = $true; message = "Package moved" }} | ConvertTo-Json
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    # Developer mode
    async def _enable_dev_mode(self, **kwargs) -> Dict[str, Any]:
        """Enable developer mode"""
        cmd = """
        $key = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock"
        Set-ItemProperty -Path $key -Name "AllowDevelopmentWithoutDevLicense" -Value 1 -Type DWord
        @{ success = $true; message = "Developer mode enabled" } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _disable_dev_mode(self, **kwargs) -> Dict[str, Any]:
        """Disable developer mode"""
        cmd = """
        $key = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock"
        Set-ItemProperty -Path $key -Name "AllowDevelopmentWithoutDevLicense" -Value 0 -Type DWord
        @{ success = $true; message = "Developer mode disabled" } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _get_dev_mode_status(self, **kwargs) -> Dict[str, Any]:
        """Get developer mode status"""
        cmd = """
        $key = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock"
        $devMode = (Get-ItemProperty -Path $key -Name "AllowDevelopmentWithoutDevLicense" -ErrorAction SilentlyContinue).AllowDevelopmentWithoutDevLicense
        $sideload = (Get-ItemProperty -Path $key -Name "AllowAllTrustedApps" -ErrorAction SilentlyContinue).AllowAllTrustedApps
        [PSCustomObject]@{
            DeveloperModeEnabled = [bool]$devMode
            SideloadingEnabled = [bool]$sideload
        } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _enable_sideloading(self, **kwargs) -> Dict[str, Any]:
        """Enable app sideloading"""
        cmd = """
        $key = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock"
        Set-ItemProperty -Path $key -Name "AllowAllTrustedApps" -Value 1 -Type DWord
        @{ success = $true; message = "Sideloading enabled" } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    # App execution aliases
    async def _list_aliases(self, **kwargs) -> Dict[str, Any]:
        """List app execution aliases"""
        cmd = """
        Get-AppxPackage | ForEach-Object {
            $pkg = $_
            $manifest = Join-Path $pkg.InstallLocation "AppxManifest.xml"
            if (Test-Path $manifest) {
                $xml = [xml](Get-Content $manifest)
                $aliases = $xml.Package.Applications.Application.Extensions.Extension | 
                    Where-Object { $_.Category -eq 'windows.appExecutionAlias' }
                if ($aliases) {
                    [PSCustomObject]@{
                        PackageName = $pkg.Name
                        Aliases = @($aliases.AppExecutionAlias.ExecutionAlias.Alias)
                    }
                }
            }
        } | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def _get_alias(self, alias_name: str, **kwargs) -> Dict[str, Any]:
        """Get package for an alias"""
        cmd = f"""
        $aliasPath = "$env:LOCALAPPDATA\\Microsoft\\WindowsApps\\{alias_name}.exe"
        if (Test-Path $aliasPath) {{
            $target = (Get-Item $aliasPath).Target
            [PSCustomObject]@{{
                Alias = '{alias_name}'
                Path = $aliasPath
                Exists = $true
                Target = $target
            }} | ConvertTo-Json
        }} else {{
            [PSCustomObject]@{{
                Alias = '{alias_name}'
                Exists = $false
            }} | ConvertTo-Json
        }}
        """
        return await self._run_powershell(cmd)

    # Capabilities
    async def _get_capabilities(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get package capabilities"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            $manifest = Join-Path $pkg.InstallLocation "AppxManifest.xml"
            $xml = [xml](Get-Content $manifest)
            [PSCustomObject]@{{
                PackageName = $pkg.Name
                Capabilities = @($xml.Package.Capabilities.Capability.Name)
                DeviceCapabilities = @($xml.Package.Capabilities.DeviceCapability.Name)
                RestrictedCapabilities = @($xml.Package.Capabilities.rescap_Capability.Name)
            }} | ConvertTo-Json -Depth 2
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    async def _list_restricted_capabilities(self, **kwargs) -> Dict[str, Any]:
        """List all restricted capabilities in use"""
        cmd = """
        $restrictedCaps = @{}
        Get-AppxPackage | ForEach-Object {
            $pkg = $_
            $manifest = Join-Path $pkg.InstallLocation "AppxManifest.xml"
            if (Test-Path $manifest) {
                $xml = [xml](Get-Content $manifest)
                $caps = $xml.Package.Capabilities.GetElementsByTagName("*") | 
                    Where-Object { $_.LocalName -like "*Capability" -and $_.Name }
                foreach ($cap in $caps) {
                    $capName = $cap.Name
                    if (-not $restrictedCaps[$capName]) {
                        $restrictedCaps[$capName] = @()
                    }
                    $restrictedCaps[$capName] += $pkg.Name
                }
            }
        }
        $restrictedCaps | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    # Dependencies
    async def _get_dependencies(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get package dependencies"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            [PSCustomObject]@{{
                PackageName = $pkg.Name
                Dependencies = @($pkg.Dependencies | ForEach-Object {{
                    [PSCustomObject]@{{
                        FullName = $_.FullName
                        Name = $_.Name
                        Publisher = $_.Publisher
                        Version = $_.Version.ToString()
                    }}
                }})
            }} | ConvertTo-Json -Depth 3
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    async def _get_dependents(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get packages that depend on this package"""
        cmd = f"""
        $targetPkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($targetPkg) {{
            $dependents = Get-AppxPackage | Where-Object {{
                $_.Dependencies | Where-Object {{ $_.FullName -eq $targetPkg.PackageFullName }}
            }} | Select-Object Name, PackageFullName, Version
            [PSCustomObject]@{{
                PackageName = $targetPkg.Name
                Dependents = @($dependents)
            }} | ConvertTo-Json -Depth 3
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    # App reset and repair
    async def _reset_package(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Reset package to default state"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            Reset-AppxPackage -Package $pkg.PackageFullName
            @{{ success = $true; message = "Package reset: $($pkg.Name)" }} | ConvertTo-Json
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    async def _repair_package(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Attempt to repair a package"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            Add-AppxPackage -Register (Join-Path $pkg.InstallLocation "AppxManifest.xml") -DisableDevelopmentMode -ForceApplicationShutdown
            @{{ success = $true; message = "Package repaired: $($pkg.Name)" }} | ConvertTo-Json
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    # Store cache
    async def _reset_store_cache(self, **kwargs) -> Dict[str, Any]:
        """Reset Windows Store cache using wsreset"""
        cmd = """
        Start-Process wsreset.exe -Wait
        @{ success = $true; message = "Store cache reset" } | ConvertTo-Json
        """
        return await self._run_powershell(cmd)

    async def _clear_store_cache(self, **kwargs) -> Dict[str, Any]:
        """Clear Store cache files"""
        cmd = """
        $cachePath = "$env:LOCALAPPDATA\\Packages\\Microsoft.WindowsStore_8wekyb3d8bbwe\\LocalCache"
        if (Test-Path $cachePath) {
            Remove-Item "$cachePath\\*" -Recurse -Force
            @{ success = $true; message = "Cache cleared" } | ConvertTo-Json
        } else {
            @{ success = $true; message = "Cache path not found" } | ConvertTo-Json
        }
        """
        return await self._run_powershell(cmd)

    # App launch
    async def _launch_app(self, app_id: str = None, package_name: str = None, **kwargs) -> Dict[str, Any]:
        """Launch an app by ID or package name"""
        if app_id:
            cmd = f"""
            Start-Process "shell:AppsFolder\\{app_id}"
            @{{ success = $true; message = "App launched: {app_id}" }} | ConvertTo-Json
            """
        elif package_name:
            cmd = f"""
            $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
            if ($pkg) {{
                $manifest = Join-Path $pkg.InstallLocation "AppxManifest.xml"
                $xml = [xml](Get-Content $manifest)
                $appId = $xml.Package.Applications.Application.Id
                $familyName = $pkg.PackageFamilyName
                Start-Process "shell:AppsFolder\\$familyName!$appId"
                @{{ success = $true; message = "App launched: $($pkg.Name)" }} | ConvertTo-Json
            }} else {{
                throw "Package not found"
            }}
            """
        else:
            return {"success": False, "error": "Provide either app_id or package_name"}
        
        return await self._run_powershell(cmd)

    async def _get_app_uri(self, package_name: str, **kwargs) -> Dict[str, Any]:
        """Get the launch URI for an app"""
        cmd = f"""
        $pkg = Get-AppxPackage -Name '*{package_name}*' | Select-Object -First 1
        if ($pkg) {{
            $manifest = Join-Path $pkg.InstallLocation "AppxManifest.xml"
            $xml = [xml](Get-Content $manifest)
            $appId = $xml.Package.Applications.Application.Id
            [PSCustomObject]@{{
                PackageName = $pkg.Name
                FamilyName = $pkg.PackageFamilyName
                AppId = $appId
                LaunchUri = "shell:AppsFolder\\$($pkg.PackageFamilyName)!$appId"
            }} | ConvertTo-Json
        }} else {{
            throw "Package not found"
        }}
        """
        return await self._run_powershell(cmd)

    # Logs and diagnostics
    async def _get_package_log(self, max_events: int = 50, **kwargs) -> Dict[str, Any]:
        """Get package deployment logs"""
        cmd = f"""
        Get-WinEvent -LogName 'Microsoft-Windows-AppXDeployment/Operational' -MaxEvents {max_events} |
        Select-Object TimeCreated, Id, LevelDisplayName, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    async def _get_install_errors(self, hours: int = 24, **kwargs) -> Dict[str, Any]:
        """Get recent installation errors"""
        cmd = f"""
        $startTime = (Get-Date).AddHours(-{hours})
        Get-WinEvent -FilterHashtable @{{
            LogName = 'Microsoft-Windows-AppXDeployment/Operational'
            Level = 2  # Error
            StartTime = $startTime
        }} -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, Message |
        ConvertTo-Json -Depth 2
        """
        return await self._run_powershell(cmd)

    # Store status
    async def _get_store_status(self, **kwargs) -> Dict[str, Any]:
        """Get Microsoft Store app status"""
        cmd = """
        $store = Get-AppxPackage -Name "Microsoft.WindowsStore"
        if ($store) {
            [PSCustomObject]@{
                Name = $store.Name
                Version = $store.Version.ToString()
                Status = $store.Status.ToString()
                InstallLocation = $store.InstallLocation
                Architecture = $store.Architecture.ToString()
            } | ConvertTo-Json
        } else {
            @{ error = "Microsoft Store not found" } | ConvertTo-Json
        }
        """
        return await self._run_powershell(cmd)

    async def _check_store_connectivity(self, **kwargs) -> Dict[str, Any]:
        """Check connectivity to Microsoft Store"""
        cmd = """
        $urls = @(
            "https://storeedgefd.dsx.mp.microsoft.com/",
            "https://login.live.com/",
            "https://displaycatalog.mp.microsoft.com/"
        )
        $results = @{}
        foreach ($url in $urls) {
            try {
                $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
                $results[$url] = @{
                    Status = "OK"
                    StatusCode = $response.StatusCode
                }
            } catch {
                $results[$url] = @{
                    Status = "Failed"
                    Error = $_.Exception.Message
                }
            }
        }
        [PSCustomObject]@{
            Timestamp = (Get-Date -Format "o")
            Connectivity = $results
        } | ConvertTo-Json -Depth 3
        """
        return await self._run_powershell(cmd)

    async def cleanup(self):
        """Cleanup plugin resources"""
        self.logger.info("Cleaning up Windows Store plugin")
