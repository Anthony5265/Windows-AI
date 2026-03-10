"""
Windows COM Automation Integration - PRODUCTION
Full COM automation support: create/invoke objects, enumerate registered servers, manage COM properties.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsCOMAutomationPlugin(IntegrationPlugin):
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_com_automation",
            name="Windows COM Automation",
            description=(
                "Windows COM automation: create COM objects, invoke methods, get/set properties, "
                "list registered servers, query the COM registry, and automate COM-enabled applications."
            ),
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "com", "automation", "ole", "activex", "scripting"],
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
            # Original actions
            "get": self._get,
            "set": self._set,
            "list": self._list,
            "execute": self._execute_command,
            # New enhanced actions
            "list_com_objects": self._list_com_objects,
            "create_com_object": self._create_com_object,
            "invoke_com_method": self._invoke_com_method,
            "get_com_properties": self._get_com_properties,
            "list_registered_servers": self._list_registered_servers,
            "get_com_object_info": self._get_com_object_info,
            "invoke_wsh": self._invoke_wsh,
            "run_vbscript": self._run_vbscript,
            "shell_execute": self._shell_execute,
            "get_clsid": self._get_clsid,
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

    # --- Original generic actions (preserved) ---

    async def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        command = params.get("command", "Get-Process")
        return await self._run_ps(command)

    async def _set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        command = params.get("command", "")
        return await self._run_ps(command)

    async def _list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get(params)

    async def _execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await self._get(params)

    # --- New enhanced COM actions ---

    async def _list_com_objects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List registered COM objects (ProgIDs) from the registry."""
        filter_str = params.get("filter", "")
        limit = params.get("limit", 100)
        cmd = f"""
$progIds = @()
Get-ChildItem "HKCR:\\" -ErrorAction SilentlyContinue |
    Where-Object {{ $_.PSChildName -match "\\." -and (-not "{filter_str}" -or $_.PSChildName -like "*{filter_str}*") }} |
    Select-Object -First {limit} | ForEach-Object {{
        $clsidPath = Join-Path $_.PSPath "CLSID"
        $clsid = if (Test-Path $clsidPath) {{
            (Get-ItemProperty -Path $clsidPath -ErrorAction SilentlyContinue)."(default)"
        }} else {{ "" }}
        $progIds += @{{
            "prog_id" = $_.PSChildName
            "clsid" = $clsid
            "path" = $_.PSPath
        }}
    }}
@{{ "com_objects" = $progIds; "count" = $progIds.Count }} | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd, timeout=60)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _create_com_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a COM object and return its available methods/properties."""
        prog_id = params.get("prog_id")
        if not prog_id:
            return {"success": False, "error": "Parameter 'prog_id' is required"}

        safe_id = prog_id.replace("'", "").replace(";", "")
        cmd = f"""
try {{
    $obj = New-Object -ComObject '{safe_id}' -ErrorAction Stop
    $type = $obj.GetType()
    $methods = @($type.GetMethods() | Where-Object {{ $_.IsPublic }} | ForEach-Object {{ $_.Name }} | Select-Object -Unique | Sort-Object | Select-Object -First 50)
    $props = @($type.GetProperties() | Where-Object {{ $_.CanRead }} | ForEach-Object {{ $_.Name }} | Sort-Object | Select-Object -First 50)
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($obj) | Out-Null
    @{{
        "success" = $true
        "prog_id" = "{safe_id}"
        "type_name" = $type.FullName
        "methods" = $methods
        "properties" = $props
        "method_count" = $methods.Count
        "property_count" = $props.Count
    }} | ConvertTo-Json -Depth 2
}} catch {{
    @{{ "success" = $false; "error" = $_.Exception.Message; "prog_id" = "{safe_id}" }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _invoke_com_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a COM object and invoke a method on it."""
        prog_id = params.get("prog_id")
        method_name = params.get("method_name")
        method_args = params.get("args", [])
        if not prog_id or not method_name:
            return {"success": False, "error": "Parameters 'prog_id' and 'method_name' are required"}

        safe_id = prog_id.replace("'", "").replace(";", "")
        safe_method = method_name.replace("'", "").replace(";", "")
        # Build args string safely
        args_parts = []
        for arg in method_args[:10]:
            if isinstance(arg, str):
                args_parts.append(f'"{arg.replace(chr(34), chr(39))}"')
            elif isinstance(arg, bool):
                args_parts.append("$true" if arg else "$false")
            elif isinstance(arg, (int, float)):
                args_parts.append(str(arg))
        args_str = ", ".join(args_parts)

        cmd = f"""
try {{
    $obj = New-Object -ComObject '{safe_id}' -ErrorAction Stop
    $result = $obj.{safe_method}({args_str})
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($obj) | Out-Null
    @{{
        "success" = $true
        "prog_id" = "{safe_id}"
        "method" = "{safe_method}"
        "result" = ($result | ConvertTo-Json -Depth 2 -ErrorAction SilentlyContinue)
        "result_type" = if ($result) {{ $result.GetType().Name }} else {{ "null" }}
    }} | ConvertTo-Json -Depth 2
}} catch {{
    @{{ "success" = $false; "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_com_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get properties of a COM object."""
        prog_id = params.get("prog_id")
        property_names = params.get("properties", [])
        if not prog_id:
            return {"success": False, "error": "Parameter 'prog_id' is required"}

        safe_id = prog_id.replace("'", "").replace(";", "")
        if property_names:
            prop_reads = "\n".join([
                f'    $props["{p.replace(chr(34), chr(39))}"] = $obj.{p.replace(";", "").replace(chr(34), "")}'
                for p in property_names[:20]
            ])
            props_block = f"$props = @{{}}\n{prop_reads}\n    $props"
        else:
            props_block = r"""
    $props = @{}
    $obj.GetType().GetProperties() | Where-Object { $_.CanRead } | Select-Object -First 30 | ForEach-Object {
        try { $props[$_.Name] = $obj.($_.Name) } catch { $props[$_.Name] = "error: $($_.Exception.Message)" }
    }
    $props
"""
        cmd = f"""
try {{
    $obj = New-Object -ComObject '{safe_id}' -ErrorAction Stop
    {props_block} | ConvertTo-Json -Depth 2
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($obj) | Out-Null
}} catch {{
    @{{ "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _list_registered_servers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List registered COM servers from HKCR\\CLSID."""
        filter_str = params.get("filter", "")
        limit = params.get("limit", 100)
        server_type = params.get("server_type", "all")  # "inproc", "local", "all"
        cmd = f"""
$servers = @()
Get-ChildItem "HKCR:\\CLSID" -ErrorAction SilentlyContinue | Select-Object -First 500 | ForEach-Object {{
    $clsid = $_.PSChildName
    $name = (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue)."(default)"
    if (-not "{filter_str}" -or $name -like "*{filter_str}*" -or $clsid -like "*{filter_str}*") {{
        $server = @{{ "clsid" = $clsid; "name" = $name }}
        $inprocPath = Join-Path $_.PSPath "InprocServer32"
        $localPath = Join-Path $_.PSPath "LocalServer32"
        if (Test-Path $inprocPath) {{
            $server["inproc_server"] = (Get-ItemProperty $inprocPath -ErrorAction SilentlyContinue)."(default)"
            $server["threading_model"] = (Get-ItemProperty $inprocPath -Name "ThreadingModel" -ErrorAction SilentlyContinue).ThreadingModel
        }}
        if (Test-Path $localPath) {{
            $server["local_server"] = (Get-ItemProperty $localPath -ErrorAction SilentlyContinue)."(default)"
        }}
        $include = (
            "{server_type}" -eq "all" -or
            ("{server_type}" -eq "inproc" -and $server["inproc_server"]) -or
            ("{server_type}" -eq "local" -and $server["local_server"])
        )
        if ($include) {{ $servers += $server }}
    }}
}}
$limited = $servers | Select-Object -First {limit}
@{{ "servers" = $limited; "count" = $limited.Count; "total_found" = $servers.Count }} | ConvertTo-Json -Depth 2
"""
        result = await self._run_ps(cmd, timeout=120)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_com_object_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed info about a COM object by ProgID or CLSID."""
        prog_id = params.get("prog_id")
        clsid = params.get("clsid")
        if not prog_id and not clsid:
            return {"success": False, "error": "Either 'prog_id' or 'clsid' is required"}

        if prog_id:
            safe_id = prog_id.replace("'", "").replace(";", "")
            cmd = f"""
$clsidPath = "HKCR:\\{safe_id}\\CLSID"
$clsid = if (Test-Path $clsidPath) {{ (Get-ItemProperty $clsidPath -ErrorAction SilentlyContinue)."(default)" }} else {{ "" }}
"""
        else:
            safe_clsid = clsid.replace("'", "").replace(";", "")
            if not safe_clsid.startswith("{"):
                safe_clsid = "{" + safe_clsid + "}"
            cmd = f'$clsid = "{safe_clsid}"\n'

        cmd += r"""
if ($clsid) {
    $clsidRegPath = "HKCR:\CLSID\$clsid"
    if (Test-Path $clsidRegPath) {
        $props = Get-ItemProperty $clsidRegPath -ErrorAction SilentlyContinue
        $inproc = Get-ItemProperty "$clsidRegPath\InprocServer32" -ErrorAction SilentlyContinue
        $local = Get-ItemProperty "$clsidRegPath\LocalServer32" -ErrorAction SilentlyContinue
        $progId = Get-ItemProperty "$clsidRegPath\ProgID" -ErrorAction SilentlyContinue
        @{
            "clsid" = $clsid
            "name" = $props."(default)"
            "prog_id" = if ($progId) { $progId."(default)" } else { "" }
            "inproc_server" = if ($inproc) { $inproc."(default)" } else { "" }
            "local_server" = if ($local) { $local."(default)" } else { "" }
            "threading_model" = if ($inproc) { $inproc.ThreadingModel } else { "" }
        } | ConvertTo-Json
    } else { @{ "error" = "CLSID not found in registry" } | ConvertTo-Json }
} else { @{ "error" = "Could not resolve CLSID" } | ConvertTo-Json }
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _invoke_wsh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Windows Script Host (WScript.Shell) commands."""
        command = params.get("command")
        wsh_method = params.get("method", "Run")
        wait = params.get("wait", True)
        if not command:
            return {"success": False, "error": "Parameter 'command' is required"}

        safe_cmd = command.replace("'", "").replace(";", "")
        wait_val = 1 if wait else 0
        cmd = f"""
try {{
    $wsh = New-Object -ComObject WScript.Shell -ErrorAction Stop
    $result = $wsh.{wsh_method}('{safe_cmd}', {wait_val}, $false)
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wsh) | Out-Null
    @{{ "success" = $true; "result" = $result; "command" = "{safe_cmd}" }} | ConvertTo-Json
}} catch {{
    @{{ "success" = $false; "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _run_vbscript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a VBScript snippet via cscript.exe."""
        script = params.get("script")
        if not script:
            return {"success": False, "error": "Parameter 'script' is required"}

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".vbs", delete=False, mode="w", encoding="utf-8") as f:
            f.write(script)
            script_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "cscript", "//NoLogo", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode(errors="replace").strip(),
                "error": stderr.decode(errors="replace").strip(),
                "returncode": proc.returncode,
            }
        except FileNotFoundError:
            return {"success": False, "error": "cscript.exe not available"}
        except asyncio.TimeoutError:
            return {"success": False, "error": "VBScript timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass

    async def _shell_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Use Shell.Application COM object to execute shell operations."""
        verb = params.get("verb", "open")
        path = params.get("path")
        args = params.get("args", "")
        if not path:
            return {"success": False, "error": "Parameter 'path' is required"}

        safe_path = path.replace("'", "").replace(";", "")
        safe_verb = verb.replace("'", "")
        safe_args = str(args).replace("'", "")
        cmd = f"""
try {{
    $shell = New-Object -ComObject Shell.Application -ErrorAction Stop
    $shell.ShellExecute('{safe_path}', '{safe_args}', '', '{safe_verb}', 1)
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($shell) | Out-Null
    @{{ "success" = $true; "path" = "{safe_path}"; "verb" = "{safe_verb}" }} | ConvertTo-Json
}} catch {{
    @{{ "success" = $false; "error" = $_.Exception.Message }} | ConvertTo-Json
}}
"""
        result = await self._run_ps(cmd)
        if result["success"] and result["output"]:
            try:
                result["data"] = json.loads(result["output"])
            except json.JSONDecodeError:
                result["data"] = {"raw": result["output"]}
        return result

    async def _get_clsid(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Look up CLSID for a given ProgID."""
        prog_id = params.get("prog_id")
        if not prog_id:
            return {"success": False, "error": "Parameter 'prog_id' is required"}
        safe_id = prog_id.replace("'", "").replace(";", "")
        cmd = f"""
$clsidPath = "HKCR:\\{safe_id}\\CLSID"
if (Test-Path $clsidPath) {{
    $clsid = (Get-ItemProperty $clsidPath -ErrorAction SilentlyContinue)."(default)"
    @{{ "prog_id" = "{safe_id}"; "clsid" = $clsid }} | ConvertTo-Json
}} else {{
    @{{ "error" = "ProgID not found"; "prog_id" = "{safe_id}" }} | ConvertTo-Json
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
                "get": {"description": "Run PowerShell command (legacy)", "params": {"command": "str"}},
                "set": {"description": "Run PowerShell set command (legacy)", "params": {"command": "str"}},
                "list": {"description": "Alias for get"},
                "execute": {"description": "Alias for get"},
                "list_com_objects": {"description": "List registered COM ProgIDs", "params": {"filter": "str", "limit": "int"}},
                "create_com_object": {"description": "Create COM object and inspect it", "params": {"prog_id": "str"}},
                "invoke_com_method": {"description": "Invoke COM method", "params": {"prog_id": "str", "method_name": "str", "args": "list"}},
                "get_com_properties": {"description": "Get COM object properties", "params": {"prog_id": "str", "properties": "list"}},
                "list_registered_servers": {"description": "List HKCR CLSID servers", "params": {"filter": "str", "server_type": "all|inproc|local", "limit": "int"}},
                "get_com_object_info": {"description": "Get COM object details", "params": {"prog_id": "str", "clsid": "str"}},
                "invoke_wsh": {"description": "Run WScript.Shell command", "params": {"command": "str", "method": "str", "wait": "bool"}},
                "run_vbscript": {"description": "Execute VBScript via cscript", "params": {"script": "str"}},
                "shell_execute": {"description": "Shell.Application ShellExecute", "params": {"path": "str", "verb": "str", "args": "str"}},
                "get_clsid": {"description": "Resolve CLSID for ProgID", "params": {"prog_id": "str"}},
            },
        }


plugin = WindowsCOMAutomationPlugin()
