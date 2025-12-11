"""
Windows BitLocker Management Plugin - PRODUCTION

Provides comprehensive BitLocker drive encryption management including:
- Volume encryption status and configuration
- Enable/disable encryption
- Key protector management (TPM, recovery password, startup key)
- Recovery key backup and retrieval
- Auto-unlock management
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsBitLockerPlugin(Plugin):
    """Windows BitLocker management plugin with comprehensive drive encryption support."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_bitlocker",
            name="Windows BitLocker",
            description="BitLocker drive encryption management - status, encryption, recovery keys, TPM",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "bitlocker", "encryption", "security", "tpm", "drive"]
        )
        super().__init__(metadata)
        self._admin_available = False

    async def initialize(self) -> bool:
        """Initialize and check BitLocker availability."""
        result = await self._run_powershell("Get-Command Get-BitLockerVolume -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name", require_admin=False)
        self._admin_available = result["success"] and "Get-BitLockerVolume" in result.get("output", "")
        if not self._admin_available:
            logger.warning("BitLocker cmdlets not available - may need admin rights or feature not installed")
        self._initialized = True
        return True

    async def _run_powershell(self, command: str, timeout: int = 120, require_admin: bool = True) -> Dict[str, Any]:
        """Execute a PowerShell command."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='replace').strip(),
                "error": stderr.decode('utf-8', errors='replace').strip() if stderr else None,
                "return_code": process.returncode
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute(self, action: str = "status", parameters: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Execute a BitLocker operation."""
        if parameters is None:
            parameters = kwargs

        actions = {
            # Status and info
            "status": self._get_status,
            "get_volume": self._get_volume,
            "list_volumes": self._list_volumes,
            # Encryption operations
            "enable": self._enable_bitlocker,
            "disable": self._disable_bitlocker,
            "suspend": self._suspend_protection,
            "resume": self._resume_protection,
            "lock": self._lock_volume,
            "unlock": self._unlock_volume,
            # Key protector management
            "add_recovery_password": self._add_recovery_password,
            "add_tpm_protector": self._add_tpm_protector,
            "add_startup_key": self._add_startup_key,
            "remove_key_protector": self._remove_key_protector,
            "get_key_protectors": self._get_key_protectors,
            "backup_recovery_key": self._backup_recovery_key,
            # Auto-unlock
            "enable_auto_unlock": self._enable_auto_unlock,
            "disable_auto_unlock": self._disable_auto_unlock,
            # TPM
            "get_tpm_status": self._get_tpm_status,
            "clear_tpm": self._clear_tpm,
            # Encryption progress
            "get_encryption_percentage": self._get_encryption_percentage,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"BitLocker operation failed: {e}")
            return {"success": False, "error": str(e)}

    # Status and info
    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall BitLocker status."""
        cmd = "Get-BitLockerVolume | Select-Object MountPoint,VolumeStatus,EncryptionPercentage,ProtectionStatus,LockStatus,EncryptionMethod,VolumeType | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                volumes = json.loads(result["output"]) if result["output"] else []
                if isinstance(volumes, dict):
                    volumes = [volumes]
                return {"success": True, "volumes": volumes, "count": len(volumes)}
            except json.JSONDecodeError:
                return {"success": True, "volumes": [], "raw_output": result["output"]}
        return result

    async def _get_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed info for a specific volume."""
        mount_point = params.get("mount_point") or params.get("drive") or "C:"
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Get-BitLockerVolume -MountPoint '{mount_point}' | ConvertTo-Json -Depth 3"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                volume = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "volume": volume}
            except json.JSONDecodeError:
                return result
        return result

    async def _list_volumes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all BitLocker volumes."""
        return await self._get_status(params)

    # Encryption operations
    async def _enable_bitlocker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable BitLocker encryption on a volume."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        encryption_method = params.get("encryption_method", "XtsAes256")
        use_tpm = params.get("use_tpm", True)
        recovery_password = params.get("recovery_password", True)
        
        cmd = f"Enable-BitLocker -MountPoint '{mount_point}' -EncryptionMethod {encryption_method}"
        
        if use_tpm:
            cmd += " -TpmProtector"
        if recovery_password:
            cmd += " -RecoveryPasswordProtector"
        
        if params.get("skip_hardware_test"):
            cmd += " -SkipHardwareTest"
        
        result = await self._run_powershell(cmd, timeout=300)
        if result["success"]:
            return {"success": True, "message": f"BitLocker enabled on {mount_point}", "output": result["output"]}
        return result

    async def _disable_bitlocker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable BitLocker encryption on a volume."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Disable-BitLocker -MountPoint '{mount_point}'"
        result = await self._run_powershell(cmd, timeout=300)
        if result["success"]:
            return {"success": True, "message": f"BitLocker decryption started on {mount_point}"}
        return result

    async def _suspend_protection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suspend BitLocker protection temporarily."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        reboot_count = params.get("reboot_count", 1)
        cmd = f"Suspend-BitLocker -MountPoint '{mount_point}' -RebootCount {reboot_count}"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"BitLocker suspended on {mount_point} for {reboot_count} reboot(s)"}
        return result

    async def _resume_protection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resume BitLocker protection."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Resume-BitLocker -MountPoint '{mount_point}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"BitLocker protection resumed on {mount_point}"}
        return result

    async def _lock_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lock a BitLocker volume."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        force = "-ForceDismount" if params.get("force") else ""
        cmd = f"Lock-BitLocker -MountPoint '{mount_point}' {force}"
        return await self._run_powershell(cmd)

    async def _unlock_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock a BitLocker volume."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        password = params.get("password")
        recovery_password = params.get("recovery_password")
        recovery_key_path = params.get("recovery_key_path")
        
        if recovery_password:
            cmd = f"Unlock-BitLocker -MountPoint '{mount_point}' -RecoveryPassword '{recovery_password}'"
        elif recovery_key_path:
            cmd = f"Unlock-BitLocker -MountPoint '{mount_point}' -RecoveryKeyPath '{recovery_key_path}'"
        elif password:
            cmd = f"Unlock-BitLocker -MountPoint '{mount_point}' -Password (ConvertTo-SecureString '{password}' -AsPlainText -Force)"
        else:
            return {"success": False, "error": "password, recovery_password, or recovery_key_path required"}
        
        return await self._run_powershell(cmd)

    # Key protector management
    async def _add_recovery_password(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a recovery password protector."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Add-BitLockerKeyProtector -MountPoint '{mount_point}' -RecoveryPasswordProtector"
        result = await self._run_powershell(cmd)
        if result["success"]:
            key_cmd = f"(Get-BitLockerVolume -MountPoint '{mount_point}').KeyProtector | Where-Object {{$_.KeyProtectorType -eq 'RecoveryPassword'}} | Select-Object -Last 1 -ExpandProperty RecoveryPassword"
            key_result = await self._run_powershell(key_cmd)
            return {
                "success": True,
                "message": "Recovery password added",
                "recovery_password": key_result.get("output", "").strip() if key_result["success"] else None
            }
        return result

    async def _add_tpm_protector(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add TPM protector."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Add-BitLockerKeyProtector -MountPoint '{mount_point}' -TpmProtector"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "TPM protector added"}
        return result

    async def _add_startup_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add startup key protector."""
        mount_point = params.get("mount_point") or params.get("drive")
        key_path = params.get("key_path")
        if not mount_point or not key_path:
            return {"success": False, "error": "mount_point/drive and key_path required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Add-BitLockerKeyProtector -MountPoint '{mount_point}' -StartupKeyPath '{key_path}'"
        return await self._run_powershell(cmd)

    async def _remove_key_protector(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a key protector."""
        mount_point = params.get("mount_point") or params.get("drive")
        key_protector_id = params.get("key_protector_id")
        if not mount_point or not key_protector_id:
            return {"success": False, "error": "mount_point/drive and key_protector_id required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Remove-BitLockerKeyProtector -MountPoint '{mount_point}' -KeyProtectorId '{key_protector_id}'"
        return await self._run_powershell(cmd)

    async def _get_key_protectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all key protectors for a volume."""
        mount_point = params.get("mount_point") or params.get("drive") or "C:"
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"(Get-BitLockerVolume -MountPoint '{mount_point}').KeyProtector | Select-Object KeyProtectorId,KeyProtectorType,RecoveryPassword | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                protectors = json.loads(result["output"]) if result["output"] else []
                if isinstance(protectors, dict):
                    protectors = [protectors]
                return {"success": True, "key_protectors": protectors, "count": len(protectors)}
            except json.JSONDecodeError:
                return {"success": True, "key_protectors": [], "raw_output": result["output"]}
        return result

    async def _backup_recovery_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Backup recovery key to AD or file."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        backup_path = params.get("backup_path")
        backup_to_ad = params.get("backup_to_ad", False)
        
        if backup_to_ad:
            cmd = f"$kp = (Get-BitLockerVolume -MountPoint '{mount_point}').KeyProtector | Where-Object {{$_.KeyProtectorType -eq 'RecoveryPassword'}} | Select-Object -First 1; Backup-BitLockerKeyProtector -MountPoint '{mount_point}' -KeyProtectorId $kp.KeyProtectorId"
        elif backup_path:
            cmd = f"(Get-BitLockerVolume -MountPoint '{mount_point}').KeyProtector | Where-Object {{$_.KeyProtectorType -eq 'RecoveryPassword'}} | ForEach-Object {{ $_ | Select-Object KeyProtectorId,RecoveryPassword | ConvertTo-Json }} | Out-File '{backup_path}'"
        else:
            cmd = f"(Get-BitLockerVolume -MountPoint '{mount_point}').KeyProtector | Where-Object {{$_.KeyProtectorType -eq 'RecoveryPassword'}} | Select-Object KeyProtectorId,RecoveryPassword | ConvertTo-Json"
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": "Recovery key backed up", "output": result.get("output")}
        return result

    # Auto-unlock
    async def _enable_auto_unlock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable auto-unlock for a data volume."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Enable-BitLockerAutoUnlock -MountPoint '{mount_point}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Auto-unlock enabled for {mount_point}"}
        return result

    async def _disable_auto_unlock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable auto-unlock for a data volume."""
        mount_point = params.get("mount_point") or params.get("drive")
        if not mount_point:
            return {"success": False, "error": "mount_point/drive required"}
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"Disable-BitLockerAutoUnlock -MountPoint '{mount_point}'"
        result = await self._run_powershell(cmd)
        if result["success"]:
            return {"success": True, "message": f"Auto-unlock disabled for {mount_point}"}
        return result

    # TPM
    async def _get_tpm_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get TPM status."""
        cmd = "Get-Tpm | Select-Object TpmPresent,TpmReady,TpmEnabled,TpmActivated,TpmOwned,ManufacturerId,ManufacturerVersion | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                tpm = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "tpm": tpm}
            except json.JSONDecodeError:
                return result
        return result

    async def _clear_tpm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear TPM (requires confirmation)."""
        if not params.get("confirm"):
            return {"success": False, "error": "TPM clear requires confirm=True parameter"}
        
        cmd = "Clear-Tpm"
        return await self._run_powershell(cmd)

    # Encryption progress
    async def _get_encryption_percentage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get encryption progress for a volume."""
        mount_point = params.get("mount_point") or params.get("drive") or "C:"
        if not mount_point.endswith(":"):
            mount_point += ":"
        
        cmd = f"(Get-BitLockerVolume -MountPoint '{mount_point}').EncryptionPercentage"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                percentage = float(result["output"].strip()) if result["output"] else 0
                return {"success": True, "mount_point": mount_point, "encryption_percentage": percentage}
            except (ValueError, AttributeError):
                return result
        return result

    def get_schema(self) -> Dict[str, Any]:
        """Return the plugin schema."""
        return {
            "type": "object",
            "actions": {
                "status": {"description": "Get BitLocker status for all volumes"},
                "get_volume": {"description": "Get detailed volume info", "params": ["mount_point"]},
                "list_volumes": {"description": "List all BitLocker volumes"},
                "enable": {"description": "Enable BitLocker", "params": ["mount_point", "encryption_method", "use_tpm", "recovery_password"]},
                "disable": {"description": "Disable BitLocker", "params": ["mount_point"]},
                "suspend": {"description": "Suspend protection", "params": ["mount_point", "reboot_count"]},
                "resume": {"description": "Resume protection", "params": ["mount_point"]},
                "lock": {"description": "Lock volume", "params": ["mount_point", "force"]},
                "unlock": {"description": "Unlock volume", "params": ["mount_point", "password", "recovery_password", "recovery_key_path"]},
                "add_recovery_password": {"description": "Add recovery password", "params": ["mount_point"]},
                "add_tpm_protector": {"description": "Add TPM protector", "params": ["mount_point"]},
                "get_key_protectors": {"description": "Get key protectors", "params": ["mount_point"]},
                "backup_recovery_key": {"description": "Backup recovery key", "params": ["mount_point", "backup_path", "backup_to_ad"]},
                "enable_auto_unlock": {"description": "Enable auto-unlock", "params": ["mount_point"]},
                "disable_auto_unlock": {"description": "Disable auto-unlock", "params": ["mount_point"]},
                "get_tpm_status": {"description": "Get TPM status"},
                "get_encryption_percentage": {"description": "Get encryption progress", "params": ["mount_point"]}
            }
        }


plugin = WindowsBitLockerPlugin()
