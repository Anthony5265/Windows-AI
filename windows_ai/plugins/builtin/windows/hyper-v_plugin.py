"""
Windows Hyper-V Integration - PRODUCTION

Provides comprehensive Hyper-V VM management capabilities including:
- VM lifecycle management (create, start, stop, delete)
- VM configuration and settings
- Virtual switch and network management  
- Checkpoint/snapshot management
- VM import/export
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsHyperVPlugin(IntegrationPlugin):
    """Windows Hyper-V integration plugin with comprehensive VM management."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_hyper-v",
            name="Windows Hyper-V",
            description="Hyper-V VM management - create, configure, start, stop, checkpoints, networking",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "hyperv", "virtualization", "vm"]
        )
        super().__init__(metadata)
        self.connected = False
        self._hyperv_available = False

    async def initialize(self) -> bool:
        """Initialize and check Hyper-V availability."""
        result = await self._run_powershell("Get-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V -Online | Select-Object -ExpandProperty State")
        self._hyperv_available = result["success"] and "Enabled" in result.get("output", "")
        if not self._hyperv_available:
            logger.warning("Hyper-V not enabled on this system")
        else:
            logger.info("Hyper-V is available")
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect (local access)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect."""
        self.connected = False
        return True

    async def _run_powershell(self, command: str, timeout: int = 60) -> Dict[str, Any]:
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

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute a Hyper-V operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}
        
        if not self._hyperv_available and action != "status":
            return {"success": False, "error": "Hyper-V not available. Enable it via Windows Features."}

        actions = {
            # VM operations
            "list_vms": self._list_vms,
            "get_vm": self._get_vm,
            "create_vm": self._create_vm,
            "start_vm": self._start_vm,
            "stop_vm": self._stop_vm,
            "restart_vm": self._restart_vm,
            "delete_vm": self._delete_vm,
            "suspend_vm": self._suspend_vm,
            "resume_vm": self._resume_vm,
            # VM configuration
            "set_vm_memory": self._set_vm_memory,
            "set_vm_processor": self._set_vm_processor,
            "add_vm_disk": self._add_vm_disk,
            "add_vm_network": self._add_vm_network,
            # Checkpoint operations
            "list_checkpoints": self._list_checkpoints,
            "create_checkpoint": self._create_checkpoint,
            "restore_checkpoint": self._restore_checkpoint,
            "delete_checkpoint": self._delete_checkpoint,
            # Virtual switch operations
            "list_switches": self._list_switches,
            "create_switch": self._create_switch,
            "delete_switch": self._delete_switch,
            # Export/Import
            "export_vm": self._export_vm,
            "import_vm": self._import_vm,
            # Status
            "status": self._get_status,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Hyper-V operation failed: {e}")
            return {"success": False, "error": str(e)}

    # VM operations
    async def _list_vms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all VMs."""
        command = "Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned, Uptime, Status | ConvertTo-Json"
        result = await self._run_powershell(command)
        if result["success"]:
            try:
                vms = json.loads(result["output"]) if result["output"] else []
                if isinstance(vms, dict):
                    vms = [vms]
                return {"success": True, "vms": vms, "count": len(vms)}
            except json.JSONDecodeError:
                return {"success": True, "vms": [], "raw_output": result["output"]}
        return result

    async def _get_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed VM information."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        command = f"Get-VM -Name '{name}' | Select-Object * | ConvertTo-Json -Depth 3"
        result = await self._run_powershell(command)
        if result["success"]:
            try:
                vm = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "vm": vm}
            except json.JSONDecodeError:
                return result
        return result

    async def _create_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        memory_mb = params.get("memory_mb", 2048)
        generation = params.get("generation", 2)
        vhd_path = params.get("vhd_path")
        new_vhd_size_gb = params.get("new_vhd_size_gb", 50)
        switch_name = params.get("switch_name")
        
        command = f"New-VM -Name '{name}' -MemoryStartupBytes {memory_mb}MB -Generation {generation}"
        
        if vhd_path:
            command += f" -VHDPath '{vhd_path}'"
        else:
            command += f" -NewVHDPath 'C:\\Hyper-V\\{name}\\{name}.vhdx' -NewVHDSizeBytes {new_vhd_size_gb}GB"
        
        if switch_name:
            command += f" -SwitchName '{switch_name}'"
        
        result = await self._run_powershell(command)
        if result["success"]:
            return {"success": True, "message": f"VM '{name}' created successfully"}
        return result

    async def _start_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        return await self._run_powershell(f"Start-VM -Name '{name}'")

    async def _stop_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        force = params.get("force", False)
        turnoff = params.get("turnoff", False)
        
        if turnoff:
            command = f"Stop-VM -Name '{name}' -TurnOff"
        elif force:
            command = f"Stop-VM -Name '{name}' -Force"
        else:
            command = f"Stop-VM -Name '{name}'"
        
        return await self._run_powershell(command)

    async def _restart_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart a VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        return await self._run_powershell(f"Restart-VM -Name '{name}' -Force")

    async def _delete_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        delete_vhd = params.get("delete_vhd", False)
        
        if delete_vhd:
            # Get VHD paths first
            vhd_cmd = f"Get-VMHardDiskDrive -VMName '{name}' | Select-Object -ExpandProperty Path"
            vhd_result = await self._run_powershell(vhd_cmd)
            
        result = await self._run_powershell(f"Remove-VM -Name '{name}' -Force")
        
        if result["success"] and delete_vhd and vhd_result.get("output"):
            for vhd_path in vhd_result["output"].split('\n'):
                if vhd_path.strip():
                    await self._run_powershell(f"Remove-Item -Path '{vhd_path.strip()}' -Force")
        
        return result

    async def _suspend_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suspend a VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        return await self._run_powershell(f"Suspend-VM -Name '{name}'")

    async def _resume_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resume a suspended VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        return await self._run_powershell(f"Resume-VM -Name '{name}'")

    # VM configuration
    async def _set_vm_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set VM memory configuration."""
        name = params.get("name")
        memory_mb = params.get("memory_mb")
        if not name or not memory_mb:
            return {"success": False, "error": "VM name and memory_mb required"}
        
        dynamic = params.get("dynamic", False)
        
        if dynamic:
            min_mb = params.get("min_mb", memory_mb)
            max_mb = params.get("max_mb", memory_mb * 2)
            command = f"Set-VMMemory -VMName '{name}' -DynamicMemoryEnabled $true -MinimumBytes {min_mb}MB -StartupBytes {memory_mb}MB -MaximumBytes {max_mb}MB"
        else:
            command = f"Set-VMMemory -VMName '{name}' -DynamicMemoryEnabled $false -StartupBytes {memory_mb}MB"
        
        return await self._run_powershell(command)

    async def _set_vm_processor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set VM processor configuration."""
        name = params.get("name")
        count = params.get("count", 2)
        if not name:
            return {"success": False, "error": "VM name required"}
        
        return await self._run_powershell(f"Set-VMProcessor -VMName '{name}' -Count {count}")

    async def _add_vm_disk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a virtual disk to a VM."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        vhd_path = params.get("vhd_path")
        size_gb = params.get("size_gb", 50)
        
        if not vhd_path:
            vhd_path = f"C:\\Hyper-V\\{name}\\disk-{size_gb}gb.vhdx"
            # Create new VHD
            create_result = await self._run_powershell(f"New-VHD -Path '{vhd_path}' -SizeBytes {size_gb}GB -Dynamic")
            if not create_result["success"]:
                return create_result
        
        return await self._run_powershell(f"Add-VMHardDiskDrive -VMName '{name}' -Path '{vhd_path}'")

    async def _add_vm_network(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a network adapter to a VM."""
        name = params.get("name")
        switch_name = params.get("switch_name")
        if not name or not switch_name:
            return {"success": False, "error": "VM name and switch_name required"}
        
        return await self._run_powershell(f"Add-VMNetworkAdapter -VMName '{name}' -SwitchName '{switch_name}'")

    # Checkpoint operations
    async def _list_checkpoints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List VM checkpoints."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        command = f"Get-VMCheckpoint -VMName '{name}' | Select-Object Name, CreationTime, ParentCheckpointName | ConvertTo-Json"
        result = await self._run_powershell(command)
        if result["success"]:
            try:
                checkpoints = json.loads(result["output"]) if result["output"] else []
                if isinstance(checkpoints, dict):
                    checkpoints = [checkpoints]
                return {"success": True, "checkpoints": checkpoints}
            except json.JSONDecodeError:
                return {"success": True, "checkpoints": []}
        return result

    async def _create_checkpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VM checkpoint."""
        name = params.get("name")
        checkpoint_name = params.get("checkpoint_name")
        if not name:
            return {"success": False, "error": "VM name required"}
        
        command = f"Checkpoint-VM -Name '{name}'"
        if checkpoint_name:
            command += f" -SnapshotName '{checkpoint_name}'"
        
        return await self._run_powershell(command)

    async def _restore_checkpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore a VM checkpoint."""
        name = params.get("name")
        checkpoint_name = params.get("checkpoint_name")
        if not name or not checkpoint_name:
            return {"success": False, "error": "VM name and checkpoint_name required"}
        
        return await self._run_powershell(f"Restore-VMCheckpoint -VMName '{name}' -Name '{checkpoint_name}' -Confirm:$false")

    async def _delete_checkpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a VM checkpoint."""
        name = params.get("name")
        checkpoint_name = params.get("checkpoint_name")
        if not name or not checkpoint_name:
            return {"success": False, "error": "VM name and checkpoint_name required"}
        
        return await self._run_powershell(f"Remove-VMCheckpoint -VMName '{name}' -Name '{checkpoint_name}' -Confirm:$false")

    # Virtual switch operations
    async def _list_switches(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List virtual switches."""
        command = "Get-VMSwitch | Select-Object Name, SwitchType, NetAdapterInterfaceDescription | ConvertTo-Json"
        result = await self._run_powershell(command)
        if result["success"]:
            try:
                switches = json.loads(result["output"]) if result["output"] else []
                if isinstance(switches, dict):
                    switches = [switches]
                return {"success": True, "switches": switches}
            except json.JSONDecodeError:
                return {"success": True, "switches": []}
        return result

    async def _create_switch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a virtual switch."""
        name = params.get("name")
        switch_type = params.get("type", "Internal")  # External, Internal, Private
        if not name:
            return {"success": False, "error": "Switch name required"}
        
        command = f"New-VMSwitch -Name '{name}' -SwitchType {switch_type}"
        
        if switch_type == "External":
            adapter = params.get("net_adapter")
            if adapter:
                command = f"New-VMSwitch -Name '{name}' -NetAdapterName '{adapter}'"
        
        return await self._run_powershell(command)

    async def _delete_switch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a virtual switch."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Switch name required"}
        return await self._run_powershell(f"Remove-VMSwitch -Name '{name}' -Force")

    # Export/Import
    async def _export_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export a VM."""
        name = params.get("name")
        path = params.get("path")
        if not name or not path:
            return {"success": False, "error": "VM name and export path required"}
        
        return await self._run_powershell(f"Export-VM -Name '{name}' -Path '{path}'", timeout=3600)

    async def _import_vm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import a VM."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Import path required"}
        
        command = f"Import-VM -Path '{path}'"
        
        copy = params.get("copy", False)
        if copy:
            command += " -Copy"
        
        generate_new_id = params.get("generate_new_id", False)
        if generate_new_id:
            command += " -GenerateNewId"
        
        return await self._run_powershell(command, timeout=1800)

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Hyper-V status."""
        return {
            "success": True,
            "hyperv_available": self._hyperv_available
        }

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Get the plugin schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_vms", "get_vm", "create_vm", "start_vm", "stop_vm",
                            "restart_vm", "delete_vm", "suspend_vm", "resume_vm",
                            "set_vm_memory", "set_vm_processor", "add_vm_disk", "add_vm_network",
                            "list_checkpoints", "create_checkpoint", "restore_checkpoint", "delete_checkpoint",
                            "list_switches", "create_switch", "delete_switch",
                            "export_vm", "import_vm", "status"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "memory_mb": {"type": "integer"},
                        "generation": {"type": "integer"},
                        "switch_name": {"type": "string"},
                        "checkpoint_name": {"type": "string"}
                    }
                }
            }
        }


plugin = WindowsHyperVPlugin()
