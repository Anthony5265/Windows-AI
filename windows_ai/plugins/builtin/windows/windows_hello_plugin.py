"""
Windows Hello Biometric Authentication Integration - PRODUCTION
Manage Windows Hello: PIN, face, fingerprint, security devices, and enrollment status.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsHelloPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_hello",
            name="Windows Hello",
            description=(
                "Manage Windows Hello biometric authentication: check enrollment status, "
                "list enrolled methods (face/fingerprint/PIN), manage security devices, and test Hello."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "hello", "biometric", "authentication", "face", "fingerprint", "pin"],
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
            "get_hello_status": self._get_hello_status,
            "list_enrolled_methods": self._list_enrolled_methods,
            "enroll_face": self._enroll_face,
            "enroll_fingerprint": self._enroll_fingerprint,
            "enroll_pin": self._enroll_pin,
            "remove_enrollment": self._remove_enrollment,
            "test_hello": self._test_hello,
            "get_security_devices": self._get_security_devices,
            "get_biometric_policy": self._get_biometric_policy,
            "set_biometric_policy": self._set_biometric_policy,
            "get_ngc_keys": self._get_ngc_keys,
        }

        handler = actions.get(action)
        if handler is None:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions)}"}
        return await handler(parameters)

    async def _run_ps(self, cmd: str, timeout: int = 30) -> Dict[str, Any]:
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

    async def _get_hello_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Windows Hello overall status and configuration."""
        cmd = r"""
$result = @{}

# Check if Windows Hello is configured (NGC folder)
$ngcPath = "$env:SystemRoot\ServiceProfiles\LocalService\AppData\Local\Microsoft\Ngc"
$result["ngc_path_exists"] = (Test-Path $ngcPath)

# Check Biometric service
$bioSvc = Get-Service -Name "WbioSrvc" -ErrorAction SilentlyContinue
$result["biometric_service_status"] = if ($bioSvc) { $bioSvc.Status.ToString() } else { "not_found" }
$result["biometric_service_start_type"] = if ($bioSvc) { $bioSvc.StartType.ToString() } else { "unknown" }

# Check Hello policy settings
$policyPath = "HKLM:\SOFTWARE\Policies\Microsoft\Biometrics"
$result["biometrics_policy_disabled"] = $false
if (Test-Path $policyPath) {
    $disabled = (Get-ItemProperty -Path $policyPath -Name "Enabled" -ErrorAction SilentlyContinue).Enabled
    $result["biometrics_policy_disabled"] = ($disabled -eq 0)
}

# Check for biometric hardware
$biometricDevices = Get-PnpDevice -Class "Biometric" -ErrorAction SilentlyContinue
$result["biometric_devices"] = @($biometricDevices | ForEach-Object {
    @{ "name" = $_.FriendlyName; "status" = $_.Status.ToString() }
})
$result["biometric_device_count"] = $result["biometric_devices"].Count

# Check TPM
$tpm = Get-WmiObject -Namespace "root\CIMV2\Security\MicrosoftTpm" -Class "Win32_Tpm" -ErrorAction SilentlyContinue
$result["tpm_present"] = ($tpm -ne $null)
$result["tpm_enabled"] = if ($tpm) { $tpm.IsEnabled_InitialValue } else { $false }
$result["tpm_activated"] = if ($tpm) { $tpm.IsActivated_InitialValue } else { $false }
$result["tpm_spec_version"] = if ($tpm) { $tpm.SpecVersion } else { "unknown" }

# PIN status
$ngcUserPath = "$env:SystemRoot\ServiceProfiles\LocalService\AppData\Local\Microsoft\Ngc"
$result["pin_enrolled"] = (Test-Path $ngcUserPath) -and (@(Get-ChildItem $ngcUserPath -ErrorAction SilentlyContinue).Count -gt 0)

$result | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _list_enrolled_methods(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List enrolled Windows Hello authentication methods."""
        cmd = r"""
$methods = @()

# Check biometric service
$bioSvc = Get-Service -Name "WbioSrvc" -ErrorAction SilentlyContinue

# Check for fingerprint readers
$fpDevices = Get-PnpDevice -Class "Biometric" -ErrorAction SilentlyContinue |
    Where-Object { $_.FriendlyName -like "*fingerprint*" -or $_.FriendlyName -like "*finger*" }
if (@($fpDevices).Count -gt 0) {
    $methods += @{
        "method" = "fingerprint"
        "available" = $true
        "device_count" = @($fpDevices).Count
        "devices" = @($fpDevices | ForEach-Object { @{ "name"=$_.FriendlyName; "status"=$_.Status.ToString() } })
    }
}

# Check for IR/face cameras
$faceDevices = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object { $_.FriendlyName -like "*IR*Camera*" -or $_.FriendlyName -like "*infrared*" -or $_.FriendlyName -like "*RealSense*" }
if (@($faceDevices).Count -gt 0) {
    $methods += @{
        "method" = "face"
        "available" = $true
        "device_count" = @($faceDevices).Count
        "devices" = @($faceDevices | ForEach-Object { @{ "name"=$_.FriendlyName; "status"=$_.Status.ToString() } })
    }
}

# Check for PIN
$ngcPath = "$env:SystemRoot\ServiceProfiles\LocalService\AppData\Local\Microsoft\Ngc"
$pinEnrolled = (Test-Path $ngcPath) -and (@(Get-ChildItem $ngcPath -ErrorAction SilentlyContinue).Count -gt 0)
$methods += @{
    "method" = "pin"
    "available" = $true
    "enrolled" = $pinEnrolled
}

# Security keys
$secKeyDevices = Get-PnpDevice -ErrorAction SilentlyContinue |
    Where-Object { $_.FriendlyName -like "*Security Key*" -or $_.FriendlyName -like "*FIDO*" -or $_.FriendlyName -like "*YubiKey*" }
if (@($secKeyDevices).Count -gt 0) {
    $methods += @{
        "method" = "security_key"
        "available" = $true
        "device_count" = @($secKeyDevices).Count
    }
}

@{ "methods" = $methods; "count" = $methods.Count } | ConvertTo-Json -Depth 4
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _enroll_face(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Launch Windows Hello face enrollment UI."""
        cmd = r"""
try {
    # Launch Windows Hello face setup via ms-settings URI
    Start-Process "ms-settings:signinoptions-launchfaceenrollment" -ErrorAction Stop
    Write-Output "Face enrollment UI launched"
} catch {
    # Fallback to general sign-in options
    Start-Process "ms-settings:signinoptions" -ErrorAction SilentlyContinue
    Write-Output "Opened Sign-in options (face enrollment may be available)"
}
"""
        result = await self._run_ps(cmd)
        result["note"] = "Face enrollment requires IR camera hardware. Follow on-screen instructions."
        return result

    async def _enroll_fingerprint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Launch Windows Hello fingerprint enrollment UI."""
        cmd = r"""
try {
    Start-Process "ms-settings:signinoptions-launchfingerprintenrollment" -ErrorAction Stop
    Write-Output "Fingerprint enrollment UI launched"
} catch {
    Start-Process "ms-settings:signinoptions" -ErrorAction SilentlyContinue
    Write-Output "Opened Sign-in options"
}
"""
        result = await self._run_ps(cmd)
        result["note"] = "Fingerprint enrollment requires a fingerprint reader. Follow on-screen instructions."
        return result

    async def _enroll_pin(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Launch Windows Hello PIN setup UI."""
        cmd = r"""
try {
    Start-Process "ms-settings:signinoptions-launchpinchange" -ErrorAction Stop
    Write-Output "PIN setup UI launched"
} catch {
    Start-Process "ms-settings:signinoptions" -ErrorAction SilentlyContinue
    Write-Output "Opened Sign-in options"
}
"""
        result = await self._run_ps(cmd)
        result["note"] = "Follow the on-screen instructions to set up or change your PIN."
        return result

    async def _remove_enrollment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a Windows Hello enrollment (requires admin for NGC cleanup)."""
        method = params.get("method", "all")
        cmd = r"""
$result = @{}
# Clearing NGC keys removes PIN and biometric credentials
$ngcPath = "$env:SystemRoot\ServiceProfiles\LocalService\AppData\Local\Microsoft\Ngc"
if (Test-Path $ngcPath) {
    try {
        # Take ownership and clear NGC folder (requires admin)
        $acl = Get-Acl $ngcPath
        $acl.SetOwner([System.Security.Principal.WindowsIdentity]::GetCurrent().User)
        Set-Acl $ngcPath $acl
        Remove-Item "$ngcPath\*" -Recurse -Force -ErrorAction SilentlyContinue
        $result["status"] = "NGC keys cleared - PIN and biometric enrollments removed"
    } catch {
        $result["status"] = "failed"
        $result["error"] = $_.Exception.Message
        $result["note"] = "Admin rights required to clear NGC folder"
    }
} else {
    $result["status"] = "NGC folder not found - no enrollments to remove"
}
$result | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        result["warning"] = "Removing enrollments will require re-enrolling Windows Hello methods."
        return result

    async def _test_hello(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test Windows Hello availability and functionality."""
        cmd = r"""
$result = @{}

# Test biometric service
$bioSvc = Get-Service "WbioSrvc" -ErrorAction SilentlyContinue
$result["biometric_service_running"] = ($bioSvc -and $bioSvc.Status -eq "Running")

# Test TPM
$tpm = Get-WmiObject -Namespace "root\CIMV2\Security\MicrosoftTpm" -Class "Win32_Tpm" -ErrorAction SilentlyContinue
$result["tpm_available"] = ($tpm -ne $null)
$result["tpm_ready"] = ($tpm -and $tpm.IsEnabled_InitialValue -and $tpm.IsActivated_InitialValue)

# Check Windows Hello registry
$helloPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
$result["winlogon_accessible"] = (Test-Path $helloPath)

# Check credential provider
$credProv = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers" -ErrorAction SilentlyContinue
$result["credential_providers"] = @($credProv | ForEach-Object { $_.PSChildName }) | Select-Object -First 10

$result["hello_capable"] = ($result["tpm_available"] -and $result["biometric_service_running"])
$result | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_security_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get security devices (TPM, smart cards, FIDO keys, biometrics)."""
        cmd = r"""
$devices = @()

# Biometric devices
$biometrics = Get-PnpDevice -Class "Biometric" -ErrorAction SilentlyContinue
foreach ($d in $biometrics) {
    $devices += @{ "type"="biometric"; "name"=$d.FriendlyName; "status"=$d.Status.ToString(); "device_id"=$d.DeviceID }
}

# Smart card readers
$smartCards = Get-PnpDevice -Class "SmartCardReader" -ErrorAction SilentlyContinue
foreach ($d in $smartCards) {
    $devices += @{ "type"="smart_card"; "name"=$d.FriendlyName; "status"=$d.Status.ToString() }
}

# FIDO/Security keys (via HID)
$hidDevices = Get-PnpDevice -Class "HIDClass" -ErrorAction SilentlyContinue |
    Where-Object { $_.FriendlyName -like "*Security Key*" -or $_.FriendlyName -like "*FIDO*" -or $_.FriendlyName -like "*YubiKey*" }
foreach ($d in $hidDevices) {
    $devices += @{ "type"="security_key"; "name"=$d.FriendlyName; "status"=$d.Status.ToString() }
}

# TPM
$tpm = Get-WmiObject -Namespace "root\CIMV2\Security\MicrosoftTpm" -Class "Win32_Tpm" -ErrorAction SilentlyContinue
if ($tpm) {
    $devices += @{ "type"="tpm"; "name"="Trusted Platform Module"; "version"=$tpm.SpecVersion
                   "enabled"=$tpm.IsEnabled_InitialValue; "activated"=$tpm.IsActivated_InitialValue }
}

@{ "security_devices" = $devices; "count" = $devices.Count } | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_biometric_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Windows Hello/Biometric policy settings."""
        cmd = r"""
$result = @{}
$bioPath = "HKLM:\SOFTWARE\Policies\Microsoft\Biometrics"
if (Test-Path $bioPath) {
    $props = Get-ItemProperty -Path $bioPath -ErrorAction SilentlyContinue
    $result["biometrics_enabled"] = ($props.Enabled -ne 0)
    $credPath = "$bioPath\Credential Provider"
    if (Test-Path $credPath) {
        $credProps = Get-ItemProperty -Path $credPath -ErrorAction SilentlyContinue
        $result["domain_users_allowed"] = ($credProps.Enabled -ne 0)
    }
} else {
    $result["policy_configured"] = $false
    $result["biometrics_enabled"] = $true  # Default: enabled
}
$result | ConvertTo-Json
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _set_biometric_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable or disable biometric authentication via policy."""
        enabled = params.get("enabled", True)
        val = 1 if enabled else 0
        cmd = f"""
$path = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Biometrics"
if (-not (Test-Path $path)) {{ New-Item -Path $path -Force | Out-Null }}
Set-ItemProperty -Path $path -Name "Enabled" -Value {val} -Type DWord -Force
Write-Output "Biometrics policy set to: $( if ({val} -eq 1) {{ "enabled" }} else {{ "disabled" }} )"
"""
        return await self._run_ps(cmd)

    async def _get_ngc_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about NGC (Next Generation Credentials) keys."""
        cmd = r"""
$ngcPath = "$env:SystemRoot\ServiceProfiles\LocalService\AppData\Local\Microsoft\Ngc"
if (Test-Path $ngcPath) {
    $dirs = @(Get-ChildItem $ngcPath -Directory -ErrorAction SilentlyContinue)
    @{
        "ngc_path" = $ngcPath
        "key_containers" = $dirs.Count
        "container_ids" = @($dirs | ForEach-Object { $_.Name })
        "total_size_kb" = [math]::Round((Get-ChildItem $ngcPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1KB, 1)
    } | ConvertTo-Json -Depth 2
} else {
    @{ "ngc_path" = $ngcPath; "exists" = $false; "key_containers" = 0 } | ConvertTo-Json
}
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
                "get_hello_status": {"description": "Get Windows Hello status"},
                "list_enrolled_methods": {"description": "List enrolled Hello methods"},
                "enroll_face": {"description": "Launch face enrollment UI"},
                "enroll_fingerprint": {"description": "Launch fingerprint enrollment UI"},
                "enroll_pin": {"description": "Launch PIN setup UI"},
                "remove_enrollment": {"description": "Remove Hello enrollments", "params": {"method": "str"}},
                "test_hello": {"description": "Test Hello availability"},
                "get_security_devices": {"description": "List security devices (TPM, biometrics, FIDO keys)"},
                "get_biometric_policy": {"description": "Get biometric policy settings"},
                "set_biometric_policy": {"description": "Set biometric policy", "params": {"enabled": "bool"}},
                "get_ngc_keys": {"description": "Get NGC key containers info"},
            },
        }


plugin = WindowsHelloPlugin()
