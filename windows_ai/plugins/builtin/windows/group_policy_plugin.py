"""
Windows Group Policy Management Integration - PRODUCTION
List, apply, refresh, back up, and restore Group Policy settings.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsGroupPolicyPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_group_policy",
            name="Windows Group Policy",
            description=(
                "Manage Windows Group Policy: list applied policies, force refresh, read individual "
                "policy settings, backup/restore GPO, and view resultant set of policy (RSoP)."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "group_policy", "gpo", "security", "administration"],
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
            "list_policies": self._list_policies,
            "refresh_policy": self._refresh_policy,
            "get_policy": self._get_policy,
            "apply_policy": self._apply_policy,
            "backup_policies": self._backup_policies,
            "restore_policies": self._restore_policies,
            "get_policy_results": self._get_policy_results,
            "get_rsop": self._get_rsop,
            "list_gpos": self._list_gpos,
            "get_security_policy": self._get_security_policy,
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

    async def _list_policies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List applied Group Policies from registry (local and domain)."""
        scope = params.get("scope", "both")  # "machine", "user", or "both"
        cmd = r"""
$result = @{ 'machine_policies' = @(); 'user_policies' = @() }

# Machine policies
$machPath = 'HKLM:\SOFTWARE\Policies'
if (Test-Path $machPath) {
    $result['machine_policies'] = @(Get-ChildItem -Path $machPath -Recurse -ErrorAction SilentlyContinue |
        Select-Object PSPath, PSChildName |
        ForEach-Object { @{ 'path' = $_.PSPath; 'key' = $_.PSChildName } } |
        Select-Object -First 100)
}

# User policies
$userPath = 'HKCU:\SOFTWARE\Policies'
if (Test-Path $userPath) {
    $result['user_policies'] = @(Get-ChildItem -Path $userPath -Recurse -ErrorAction SilentlyContinue |
        Select-Object PSPath, PSChildName |
        ForEach-Object { @{ 'path' = $_.PSPath; 'key' = $_.PSChildName } } |
        Select-Object -First 100)
}

$result['machine_policy_count'] = $result['machine_policies'].Count
$result['user_policy_count'] = $result['user_policies'].Count
$result | ConvertTo-Json -Depth 3
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _refresh_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Force Group Policy refresh (gpupdate)."""
        force = params.get("force", False)
        scope = params.get("scope", "all")  # "computer", "user", or "all"
        args = ["/force"] if force else []

        if scope == "computer":
            args.extend(["/target:Computer"])
        elif scope == "user":
            args.extend(["/target:User"])

        try:
            proc = await asyncio.create_subprocess_exec(
                "gpupdate", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "scope": scope,
                "forced": force,
            }
        except FileNotFoundError:
            return {"success": False, "error": "gpupdate.exe not available"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "gpupdate timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific policy setting from registry."""
        path = params.get("path")
        name = params.get("name")
        if not path:
            return {"success": False, "error": "Parameter 'path' (registry path) is required"}

        safe_path = path.replace("'", "''")
        name_filter = f"-Name '{name.replace(chr(39), chr(39)+chr(39))}'" if name else ""
        cmd = f"""
if (Test-Path '{safe_path}') {{
    $props = Get-ItemProperty -Path '{safe_path}' {name_filter} -ErrorAction SilentlyContinue
    if ($props) {{
        $props | Select-Object * -ExcludeProperty PSPath, PSParentPath, PSChildName, PSProvider, PSDrive |
            ConvertTo-Json -Depth 2
    }} else {{ Write-Output '{{}}' }}
}} else {{
    Write-Output '{{"error": "Path not found"}}'
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _apply_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a registry-based policy setting."""
        path = params.get("path")
        name = params.get("name")
        value = params.get("value")
        value_type = params.get("type", "DWord")

        if not path or name is None or value is None:
            return {"success": False, "error": "Parameters 'path', 'name', and 'value' are required"}

        safe_path = path.replace("'", "''")
        safe_name = str(name).replace("'", "''")
        safe_value = str(value).replace("'", "''")
        valid_types = {"DWord", "String", "ExpandString", "Binary", "MultiString", "QWord"}
        if value_type not in valid_types:
            value_type = "DWord"

        cmd = f"""
if (-not (Test-Path '{safe_path}')) {{
    New-Item -Path '{safe_path}' -Force | Out-Null
}}
Set-ItemProperty -Path '{safe_path}' -Name '{safe_name}' -Value '{safe_value}' -Type {value_type} -Force
Write-Output 'Policy applied: {safe_name} = {safe_value}'
"""
        return await self._run_ps(cmd)

    async def _backup_policies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Backup local Group Policy to a file."""
        output_path = params.get("output_path", r"C:\Temp\GPOBackup.reg")
        safe_path = output_path.replace('"', "")

        # Export machine and user policy registry keys
        cmd = fr"""
$outDir = Split-Path '{safe_path}' -Parent
if (-not (Test-Path $outDir)) {{ New-Item -Path $outDir -ItemType Directory -Force | Out-Null }}
reg export "HKLM\SOFTWARE\Policies" '{safe_path}_machine.reg' /y 2>&1
reg export "HKCU\SOFTWARE\Policies" '{safe_path}_user.reg' /y 2>&1
Write-Output "Backed up to {safe_path}_machine.reg and {safe_path}_user.reg"
"""
        result = await self._run_ps(cmd)
        result["backup_paths"] = [f"{safe_path}_machine.reg", f"{safe_path}_user.reg"]
        return result

    async def _restore_policies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore Group Policy from a backup file."""
        backup_path = params.get("backup_path")
        if not backup_path:
            return {"success": False, "error": "Parameter 'backup_path' is required"}
        safe_path = backup_path.replace('"', "").replace("'", "''")
        cmd = f"""
if (Test-Path '{safe_path}') {{
    reg import '{safe_path}' 2>&1
    Write-Output 'Policy restored from {safe_path}'
}} else {{
    Write-Error 'Backup file not found: {safe_path}'
}}
"""
        return await self._run_ps(cmd)

    async def _get_policy_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Resultant Set of Policy (RSoP) information."""
        cmd = r"""
try {
    # Try using gpresult for RSoP summary
    $gpresult = gpresult /r /scope:computer 2>&1
    @{ 'rsop_summary' = ($gpresult -join "`n") } | ConvertTo-Json
} catch {
    @{ 'error' = $_.Exception.Message } | ConvertTo-Json
}
"""
        result = await self._run_ps(cmd, timeout=90)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_rsop(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate RSoP HTML report."""
        output_path = params.get("output_path", r"C:\Temp\rsop.html")
        safe_path = output_path.replace('"', "")
        try:
            proc = await asyncio.create_subprocess_exec(
                "gpresult", "/h", safe_path, "/f",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "report_path": safe_path,
            }
        except FileNotFoundError:
            return {"success": False, "error": "gpresult.exe not available"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "gpresult timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _list_gpos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Group Policy Objects (requires RSAT or domain environment)."""
        cmd = r"""
try {
    Import-Module GroupPolicy -ErrorAction Stop
    $gpos = Get-GPO -All -ErrorAction SilentlyContinue | Select-Object DisplayName, Id, GpoStatus, CreationTime, ModificationTime
    @($gpos) | ConvertTo-Json -Depth 2
} catch {
    # Fallback: list local GPO info
    $result = @{
        'note' = 'GroupPolicy module not available. Showing local policy registry keys.'
        'local_machine_policies' = @(Get-ChildItem 'HKLM:\SOFTWARE\Policies' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty PSChildName)
    }
    $result | ConvertTo-Json -Depth 2
}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_security_policy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export and read local security policy settings."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".inf", delete=False, mode="w") as f:
            inf_path = f.name

        try:
            cmd = f"secedit /export /cfg '{inf_path}' /quiet 2>&1; Write-Output 'Exported'"
            result = await self._run_ps(cmd)
            if os.path.exists(inf_path):
                with open(inf_path, "r", errors="replace") as f:
                    content = f.read()
                result["security_policy"] = content
                os.unlink(inf_path)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(inf_path):
                try:
                    os.unlink(inf_path)
                except OSError:
                    pass

    async def shutdown(self):
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "actions": {
                "list_policies": {"description": "List applied policies from registry"},
                "refresh_policy": {"description": "Force gpupdate", "params": {"force": "bool", "scope": "all|computer|user"}},
                "get_policy": {"description": "Read specific policy", "params": {"path": "str", "name": "str"}},
                "apply_policy": {"description": "Set policy value", "params": {"path": "str", "name": "str", "value": "any", "type": "str"}},
                "backup_policies": {"description": "Backup policies to file", "params": {"output_path": "str"}},
                "restore_policies": {"description": "Restore from backup", "params": {"backup_path": "str"}},
                "get_policy_results": {"description": "Get RSoP summary (gpresult /r)"},
                "get_rsop": {"description": "Generate RSoP HTML report", "params": {"output_path": "str"}},
                "list_gpos": {"description": "List Group Policy Objects"},
                "get_security_policy": {"description": "Export local security policy"},
            },
        }


plugin = WindowsGroupPolicyPlugin()
