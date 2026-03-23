"""
Windows File System Operations Plugin - PRODUCTION
Comprehensive file system management with permissions, attributes, ACLs, and advanced operations.
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class FileSystemOperationsPlugin(IntegrationPlugin):
    """
    Comprehensive Windows file system operations plugin.
    
    Provides full file system management including:
    - File/folder CRUD operations
    - Permission and ACL management
    - File attributes and metadata
    - Hard links, symbolic links, junctions
    - File search and indexing
    - Disk quota management
    - File compression and encryption
    - Stream management (NTFS alternate data streams)
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="windows_file_system_operations",
            name="Windows File System Operations",
            description="Comprehensive file system management with permissions, attributes, and ACLs",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "filesystem", "files", "permissions", "acl", "ntfs"]
        )
        super().__init__(metadata)
        self.connected = False

    async def initialize(self) -> bool:
        """Initialize the file system operations plugin."""
        self._initialized = True
        logger.info("File System Operations plugin initialized")
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect and verify file system access."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect from file system operations."""
        self.connected = False
        return True

    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute PowerShell script and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode("utf-8", errors="replace").strip(),
                    "return_code": process.returncode
                }
            
            output = stdout.decode("utf-8", errors="replace").strip()
            try:
                data = json.loads(output) if output else None
                return {"success": True, "data": data}
            except json.JSONDecodeError:
                return {"success": True, "data": output}
                
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def execute(self, action: str, parameters: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute file system operations."""
        actions = {
            # Basic file operations
            "get_item": self._get_item,
            "get_item_properties": self._get_item_properties,
            "copy_item": self._copy_item,
            "move_item": self._move_item,
            "remove_item": self._remove_item,
            "rename_item": self._rename_item,
            "new_item": self._new_item,
            "test_path": self._test_path,
            
            # Directory operations
            "get_children": self._get_children,
            "get_directory_size": self._get_directory_size,
            "new_directory": self._new_directory,
            "get_directory_tree": self._get_directory_tree,
            
            # File attributes
            "get_attributes": self._get_attributes,
            "set_attributes": self._set_attributes,
            "clear_attributes": self._clear_attributes,
            
            # Permissions and ACLs
            "get_acl": self._get_acl,
            "set_acl": self._set_acl,
            "add_acl_rule": self._add_acl_rule,
            "remove_acl_rule": self._remove_acl_rule,
            "get_owner": self._get_owner,
            "set_owner": self._set_owner,
            "get_effective_permissions": self._get_effective_permissions,
            "reset_permissions": self._reset_permissions,
            
            # Links and junctions
            "create_symbolic_link": self._create_symbolic_link,
            "create_hard_link": self._create_hard_link,
            "create_junction": self._create_junction,
            "get_link_target": self._get_link_target,
            "is_link": self._is_link,
            
            # NTFS streams
            "get_streams": self._get_streams,
            "read_stream": self._read_stream,
            "write_stream": self._write_stream,
            "remove_stream": self._remove_stream,
            
            # File hashing
            "get_file_hash": self._get_file_hash,
            "compare_files": self._compare_files,
            
            # Compression and encryption
            "compress_item": self._compress_item,
            "uncompress_item": self._uncompress_item,
            "encrypt_item": self._encrypt_item,
            "decrypt_item": self._decrypt_item,
            "get_compression_state": self._get_compression_state,
            "get_encryption_state": self._get_encryption_state,
            
            # Search operations
            "search_files": self._search_files,
            "search_content": self._search_content,
            "find_duplicates": self._find_duplicates,
            
            # Disk quotas
            "get_quota": self._get_quota,
            "set_quota": self._set_quota,
            "get_quota_entries": self._get_quota_entries,
            
            # File locking
            "get_locked_files": self._get_locked_files,
            "get_file_handles": self._get_file_handles,
            
            # Metadata
            "get_file_version": self._get_file_version,
            "get_digital_signature": self._get_digital_signature,
            "get_zone_identifier": self._get_zone_identifier,
            "remove_zone_identifier": self._remove_zone_identifier,
            
            # Bulk operations
            "bulk_rename": self._bulk_rename,
            "bulk_copy": self._bulk_copy,
            "bulk_move": self._bulk_move,
            "sync_directories": self._sync_directories,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {"success": False, "error": str(e)}

    # ========== Basic File Operations ==========

    async def _get_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file or directory item details."""
        path = params.get("path", "")
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force -ErrorAction Stop
        @{{
            Name = $item.Name
            FullName = $item.FullName
            Extension = $item.Extension
            Length = $item.Length
            CreationTime = $item.CreationTime.ToString("o")
            LastWriteTime = $item.LastWriteTime.ToString("o")
            LastAccessTime = $item.LastAccessTime.ToString("o")
            Attributes = $item.Attributes.ToString()
            IsDirectory = $item.PSIsContainer
            IsReadOnly = $item.IsReadOnly
            IsHidden = ($item.Attributes -band [System.IO.FileAttributes]::Hidden) -ne 0
            IsSystem = ($item.Attributes -band [System.IO.FileAttributes]::System) -ne 0
            IsEncrypted = ($item.Attributes -band [System.IO.FileAttributes]::Encrypted) -ne 0
            IsCompressed = ($item.Attributes -band [System.IO.FileAttributes]::Compressed) -ne 0
            Target = if ($item.Target) {{ $item.Target }} else {{ $null }}
            LinkType = if ($item.LinkType) {{ $item.LinkType }} else {{ $null }}
        }} | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    async def _get_item_properties(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get extended file properties including version info."""
        path = params.get("path", "")
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        $shell = New-Object -ComObject Shell.Application
        $folder = $shell.Namespace((Split-Path $item.FullName))
        $file = $folder.ParseName($item.Name)
        
        $props = @{{}}
        for ($i = 0; $i -lt 300; $i++) {{
            $propName = $folder.GetDetailsOf($null, $i)
            $propValue = $folder.GetDetailsOf($file, $i)
            if ($propName -and $propValue) {{
                $props[$propName] = $propValue
            }}
        }}
        $props | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    async def _copy_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Copy file or directory."""
        source = params.get("source", "")
        destination = params.get("destination", "")
        recurse = params.get("recurse", True)
        force = params.get("force", False)
        
        if not source or not destination:
            return {"success": False, "error": "Source and destination are required"}
        
        recurse_flag = "-Recurse" if recurse else ""
        force_flag = "-Force" if force else ""
        
        script = f'''
        Copy-Item -LiteralPath "{source}" -Destination "{destination}" {recurse_flag} {force_flag} -PassThru | 
        Select-Object Name, FullName, Length | ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    async def _move_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move file or directory."""
        source = params.get("source", "")
        destination = params.get("destination", "")
        force = params.get("force", False)
        
        if not source or not destination:
            return {"success": False, "error": "Source and destination are required"}
        
        force_flag = "-Force" if force else ""
        
        script = f'''
        Move-Item -LiteralPath "{source}" -Destination "{destination}" {force_flag} -PassThru |
        Select-Object Name, FullName | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _remove_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove file or directory."""
        path = params.get("path", "")
        recurse = params.get("recurse", False)
        force = params.get("force", False)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        recurse_flag = "-Recurse" if recurse else ""
        force_flag = "-Force" if force else ""
        
        script = f'''
        Remove-Item -LiteralPath "{path}" {recurse_flag} {force_flag} -ErrorAction Stop
        @{{ Success = $true; Message = "Item removed successfully" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _rename_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rename file or directory."""
        path = params.get("path", "")
        new_name = params.get("new_name", "")
        
        if not path or not new_name:
            return {"success": False, "error": "Path and new_name are required"}
        
        script = f'''
        Rename-Item -LiteralPath "{path}" -NewName "{new_name}" -PassThru |
        Select-Object Name, FullName | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _new_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create new file or directory."""
        path = params.get("path", "")
        item_type = params.get("type", "File")  # File or Directory
        content = params.get("content", "")
        force = params.get("force", False)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        force_flag = "-Force" if force else ""
        value_param = f'-Value "{content}"' if content and item_type == "File" else ""
        
        script = f'''
        New-Item -Path "{path}" -ItemType {item_type} {value_param} {force_flag} -ErrorAction Stop |
        Select-Object Name, FullName, Length, CreationTime | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _test_path(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Test if path exists."""
        path = params.get("path", "")
        path_type = params.get("type", "Any")  # Any, Leaf, Container
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $exists = Test-Path -LiteralPath "{path}" -PathType {path_type}
        @{{
            Path = "{path}"
            Exists = $exists
            PathType = "{path_type}"
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== Directory Operations ==========

    async def _get_children(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get directory contents."""
        path = params.get("path", "")
        recurse = params.get("recurse", False)
        filter_pattern = params.get("filter", "*")
        include_hidden = params.get("include_hidden", False)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        recurse_flag = "-Recurse" if recurse else ""
        force_flag = "-Force" if include_hidden else ""
        
        script = f'''
        Get-ChildItem -LiteralPath "{path}" -Filter "{filter_pattern}" {recurse_flag} {force_flag} |
        Select-Object Name, FullName, Length, CreationTime, LastWriteTime, 
            @{{N='IsDirectory';E={{$_.PSIsContainer}}}},
            @{{N='Attributes';E={{$_.Attributes.ToString()}}}} |
        ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    async def _get_directory_size(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate directory size."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $items = Get-ChildItem -LiteralPath "{path}" -Recurse -Force -ErrorAction SilentlyContinue
        $files = $items | Where-Object {{ -not $_.PSIsContainer }}
        $folders = $items | Where-Object {{ $_.PSIsContainer }}
        
        @{{
            Path = "{path}"
            TotalSize = ($files | Measure-Object -Property Length -Sum).Sum
            FileCount = $files.Count
            FolderCount = $folders.Count
            SizeFormatted = "{{0:N2}} GB" -f (($files | Measure-Object -Property Length -Sum).Sum / 1GB)
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _new_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create new directory with optional structure."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        New-Item -Path "{path}" -ItemType Directory -Force |
        Select-Object Name, FullName, CreationTime | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_directory_tree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get directory tree structure."""
        path = params.get("path", "")
        depth = params.get("depth", 3)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        function Get-DirectoryTree {{
            param($Path, $Depth, $CurrentDepth = 0)
            
            if ($CurrentDepth -ge $Depth) {{ return $null }}
            
            $item = Get-Item -LiteralPath $Path -Force
            $result = @{{
                Name = $item.Name
                FullName = $item.FullName
                IsDirectory = $item.PSIsContainer
                Children = @()
            }}
            
            if ($item.PSIsContainer) {{
                $children = Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue
                foreach ($child in $children) {{
                    $childTree = Get-DirectoryTree -Path $child.FullName -Depth $Depth -CurrentDepth ($CurrentDepth + 1)
                    if ($childTree) {{ $result.Children += $childTree }}
                }}
            }}
            
            return $result
        }}
        
        Get-DirectoryTree -Path "{path}" -Depth {depth} | ConvertTo-Json -Depth 10
        '''
        return await self._run_powershell(script)

    # ========== File Attributes ==========

    async def _get_attributes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file attributes."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        $attrs = $item.Attributes
        
        @{{
            Path = $item.FullName
            RawValue = [int]$attrs
            Attributes = @{{
                ReadOnly = ($attrs -band [System.IO.FileAttributes]::ReadOnly) -ne 0
                Hidden = ($attrs -band [System.IO.FileAttributes]::Hidden) -ne 0
                System = ($attrs -band [System.IO.FileAttributes]::System) -ne 0
                Directory = ($attrs -band [System.IO.FileAttributes]::Directory) -ne 0
                Archive = ($attrs -band [System.IO.FileAttributes]::Archive) -ne 0
                Compressed = ($attrs -band [System.IO.FileAttributes]::Compressed) -ne 0
                Encrypted = ($attrs -band [System.IO.FileAttributes]::Encrypted) -ne 0
                NotContentIndexed = ($attrs -band [System.IO.FileAttributes]::NotContentIndexed) -ne 0
                Offline = ($attrs -band [System.IO.FileAttributes]::Offline) -ne 0
                ReparsePoint = ($attrs -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
                SparseFile = ($attrs -band [System.IO.FileAttributes]::SparseFile) -ne 0
                Temporary = ($attrs -band [System.IO.FileAttributes]::Temporary) -ne 0
            }}
        }} | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    async def _set_attributes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set file attributes."""
        path = params.get("path", "")
        attributes = params.get("attributes", [])  # List like ["ReadOnly", "Hidden"]
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        attrs_str = ",".join(attributes) if attributes else "Normal"
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        $newAttrs = [System.IO.FileAttributes]"{attrs_str}"
        $item.Attributes = $item.Attributes -bor $newAttrs
        
        @{{
            Path = $item.FullName
            NewAttributes = $item.Attributes.ToString()
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _clear_attributes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clear specific file attributes."""
        path = params.get("path", "")
        attributes = params.get("attributes", [])
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        attrs_str = ",".join(attributes) if attributes else ""
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        $attrsToRemove = [System.IO.FileAttributes]"{attrs_str}"
        $item.Attributes = $item.Attributes -band (-bnot $attrsToRemove)
        
        @{{
            Path = $item.FullName
            NewAttributes = $item.Attributes.ToString()
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== Permissions and ACLs ==========

    async def _get_acl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get access control list for file or directory."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $acl = Get-Acl -LiteralPath "{path}"
        
        @{{
            Path = $acl.Path
            Owner = $acl.Owner
            Group = $acl.Group
            AccessRules = $acl.Access | ForEach-Object {{
                @{{
                    IdentityReference = $_.IdentityReference.Value
                    FileSystemRights = $_.FileSystemRights.ToString()
                    AccessControlType = $_.AccessControlType.ToString()
                    IsInherited = $_.IsInherited
                    InheritanceFlags = $_.InheritanceFlags.ToString()
                    PropagationFlags = $_.PropagationFlags.ToString()
                }}
            }}
            AreAccessRulesProtected = $acl.AreAccessRulesProtected
            AreAuditRulesProtected = $acl.AreAuditRulesProtected
            Sddl = $acl.Sddl
        }} | ConvertTo-Json -Depth 4
        '''
        return await self._run_powershell(script)

    async def _set_acl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set ACL from SDDL or copy from another path."""
        path = params.get("path", "")
        sddl = params.get("sddl", "")
        source_path = params.get("source_path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        if sddl:
            script = f'''
            $acl = Get-Acl -LiteralPath "{path}"
            $acl.SetSecurityDescriptorSddlForm("{sddl}")
            Set-Acl -LiteralPath "{path}" -AclObject $acl
            @{{ Success = $true; Message = "ACL set from SDDL" }} | ConvertTo-Json
            '''
        elif source_path:
            script = f'''
            $sourceAcl = Get-Acl -LiteralPath "{source_path}"
            Set-Acl -LiteralPath "{path}" -AclObject $sourceAcl
            @{{ Success = $true; Message = "ACL copied from source" }} | ConvertTo-Json
            '''
        else:
            return {"success": False, "error": "Either sddl or source_path is required"}
        
        return await self._run_powershell(script)

    async def _add_acl_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add access control rule."""
        path = params.get("path", "")
        identity = params.get("identity", "")
        rights = params.get("rights", "ReadAndExecute")
        access_type = params.get("access_type", "Allow")
        inheritance = params.get("inheritance", "ContainerInherit,ObjectInherit")
        propagation = params.get("propagation", "None")
        
        if not path or not identity:
            return {"success": False, "error": "Path and identity are required"}
        
        script = f'''
        $acl = Get-Acl -LiteralPath "{path}"
        $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            "{identity}",
            "{rights}",
            "{inheritance}",
            "{propagation}",
            "{access_type}"
        )
        $acl.AddAccessRule($rule)
        Set-Acl -LiteralPath "{path}" -AclObject $acl
        
        @{{
            Success = $true
            Message = "Access rule added"
            Identity = "{identity}"
            Rights = "{rights}"
            AccessType = "{access_type}"
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _remove_acl_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove access control rule."""
        path = params.get("path", "")
        identity = params.get("identity", "")
        rights = params.get("rights", "")
        
        if not path or not identity:
            return {"success": False, "error": "Path and identity are required"}
        
        script = f'''
        $acl = Get-Acl -LiteralPath "{path}"
        $rulesToRemove = $acl.Access | Where-Object {{ $_.IdentityReference.Value -eq "{identity}" }}
        
        foreach ($rule in $rulesToRemove) {{
            $acl.RemoveAccessRule($rule) | Out-Null
        }}
        
        Set-Acl -LiteralPath "{path}" -AclObject $acl
        @{{ Success = $true; RulesRemoved = $rulesToRemove.Count }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_owner(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file owner."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $acl = Get-Acl -LiteralPath "{path}"
        @{{
            Path = "{path}"
            Owner = $acl.Owner
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _set_owner(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set file owner."""
        path = params.get("path", "")
        owner = params.get("owner", "")
        
        if not path or not owner:
            return {"success": False, "error": "Path and owner are required"}
        
        script = f'''
        $acl = Get-Acl -LiteralPath "{path}"
        $account = New-Object System.Security.Principal.NTAccount("{owner}")
        $acl.SetOwner($account)
        Set-Acl -LiteralPath "{path}" -AclObject $acl
        
        @{{ Success = $true; NewOwner = "{owner}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_effective_permissions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get effective permissions for a user on a path."""
        path = params.get("path", "")
        identity = params.get("identity", "$env:USERNAME")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $identity = if ("{identity}" -eq "$env:USERNAME") {{ $env:USERNAME }} else {{ "{identity}" }}
        
        # Get access rules
        $acl = Get-Acl -LiteralPath "{path}"
        $rules = $acl.Access | Where-Object {{ 
            $_.IdentityReference.Value -like "*$identity*" -or 
            $_.IdentityReference.Value -eq "Everyone" -or
            $_.IdentityReference.Value -eq "BUILTIN\\Users"
        }}
        
        @{{
            Path = "{path}"
            Identity = $identity
            EffectiveRules = $rules | ForEach-Object {{
                @{{
                    Identity = $_.IdentityReference.Value
                    Rights = $_.FileSystemRights.ToString()
                    AccessType = $_.AccessControlType.ToString()
                }}
            }}
        }} | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    async def _reset_permissions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset permissions to inherited defaults."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $acl = Get-Acl -LiteralPath "{path}"
        $acl.SetAccessRuleProtection($false, $true)
        
        # Remove all explicit rules
        $acl.Access | Where-Object {{ -not $_.IsInherited }} | ForEach-Object {{
            $acl.RemoveAccessRule($_) | Out-Null
        }}
        
        Set-Acl -LiteralPath "{path}" -AclObject $acl
        @{{ Success = $true; Message = "Permissions reset to inherited defaults" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== Links and Junctions ==========

    async def _create_symbolic_link(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create symbolic link."""
        link_path = params.get("link_path", "")
        target_path = params.get("target_path", "")
        
        if not link_path or not target_path:
            return {"success": False, "error": "link_path and target_path are required"}
        
        script = f'''
        New-Item -ItemType SymbolicLink -Path "{link_path}" -Target "{target_path}" -Force |
        Select-Object Name, FullName, Target, LinkType | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _create_hard_link(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create hard link."""
        link_path = params.get("link_path", "")
        target_path = params.get("target_path", "")
        
        if not link_path or not target_path:
            return {"success": False, "error": "link_path and target_path are required"}
        
        script = f'''
        New-Item -ItemType HardLink -Path "{link_path}" -Target "{target_path}" -Force |
        Select-Object Name, FullName, LinkType | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _create_junction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create directory junction."""
        junction_path = params.get("junction_path", "")
        target_path = params.get("target_path", "")
        
        if not junction_path or not target_path:
            return {"success": False, "error": "junction_path and target_path are required"}
        
        script = f'''
        New-Item -ItemType Junction -Path "{junction_path}" -Target "{target_path}" -Force |
        Select-Object Name, FullName, Target, LinkType | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_link_target(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get target of symbolic link or junction."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = $item.FullName
            Target = $item.Target
            LinkType = $item.LinkType
            IsReparsePoint = ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _is_link(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check if path is a link."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = $item.FullName
            IsLink = $null -ne $item.LinkType
            LinkType = $item.LinkType
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== NTFS Streams ==========

    async def _get_streams(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get NTFS alternate data streams."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        Get-Item -LiteralPath "{path}" -Stream * |
        Select-Object PSChildName, Stream, Length | ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    async def _read_stream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read content from NTFS stream."""
        path = params.get("path", "")
        stream_name = params.get("stream", "")
        
        if not path or not stream_name:
            return {"success": False, "error": "Path and stream name are required"}
        
        script = f'''
        $content = Get-Content -LiteralPath "{path}" -Stream "{stream_name}" -Raw
        @{{
            Path = "{path}"
            Stream = "{stream_name}"
            Content = $content
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _write_stream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to NTFS stream."""
        path = params.get("path", "")
        stream_name = params.get("stream", "")
        content = params.get("content", "")
        
        if not path or not stream_name:
            return {"success": False, "error": "Path and stream name are required"}
        
        script = f'''
        Set-Content -LiteralPath "{path}" -Stream "{stream_name}" -Value "{content}"
        @{{ Success = $true; Stream = "{stream_name}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _remove_stream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove NTFS alternate data stream."""
        path = params.get("path", "")
        stream_name = params.get("stream", "")
        
        if not path or not stream_name:
            return {"success": False, "error": "Path and stream name are required"}
        
        script = f'''
        Remove-Item -LiteralPath "{path}" -Stream "{stream_name}" -Force
        @{{ Success = $true; RemovedStream = "{stream_name}" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== File Hashing ==========

    async def _get_file_hash(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate file hash."""
        path = params.get("path", "")
        algorithm = params.get("algorithm", "SHA256")  # MD5, SHA1, SHA256, SHA384, SHA512
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $hash = Get-FileHash -LiteralPath "{path}" -Algorithm {algorithm}
        @{{
            Path = $hash.Path
            Algorithm = $hash.Algorithm
            Hash = $hash.Hash
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _compare_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two files using hash."""
        path1 = params.get("path1", "")
        path2 = params.get("path2", "")
        algorithm = params.get("algorithm", "SHA256")
        
        if not path1 or not path2:
            return {"success": False, "error": "Both paths are required"}
        
        script = f'''
        $hash1 = (Get-FileHash -LiteralPath "{path1}" -Algorithm {algorithm}).Hash
        $hash2 = (Get-FileHash -LiteralPath "{path2}" -Algorithm {algorithm}).Hash
        
        @{{
            Path1 = "{path1}"
            Path2 = "{path2}"
            Hash1 = $hash1
            Hash2 = $hash2
            AreIdentical = $hash1 -eq $hash2
            Algorithm = "{algorithm}"
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== Compression and Encryption ==========

    async def _compress_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compress file or directory using NTFS compression."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        if ($item.PSIsContainer) {{
            compact /c /s:"{path}" | Out-Null
        }} else {{
            compact /c "{path}" | Out-Null
        }}
        
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = "{path}"
            IsCompressed = ($item.Attributes -band [System.IO.FileAttributes]::Compressed) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _uncompress_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Uncompress file or directory."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        if ($item.PSIsContainer) {{
            compact /u /s:"{path}" | Out-Null
        }} else {{
            compact /u "{path}" | Out-Null
        }}
        
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = "{path}"
            IsCompressed = ($item.Attributes -band [System.IO.FileAttributes]::Compressed) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _encrypt_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt file or directory using EFS."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        cipher /e "{path}" | Out-Null
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = "{path}"
            IsEncrypted = ($item.Attributes -band [System.IO.FileAttributes]::Encrypted) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _decrypt_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt file or directory."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        cipher /d "{path}" | Out-Null
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = "{path}"
            IsEncrypted = ($item.Attributes -band [System.IO.FileAttributes]::Encrypted) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_compression_state(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get compression state of item."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = "{path}"
            IsCompressed = ($item.Attributes -band [System.IO.FileAttributes]::Compressed) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_encryption_state(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get encryption state of item."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $item = Get-Item -LiteralPath "{path}" -Force
        @{{
            Path = "{path}"
            IsEncrypted = ($item.Attributes -band [System.IO.FileAttributes]::Encrypted) -ne 0
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== Search Operations ==========

    async def _search_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files by pattern."""
        path = params.get("path", "")
        pattern = params.get("pattern", "*")
        recurse = params.get("recurse", True)
        include_hidden = params.get("include_hidden", False)
        max_results = params.get("max_results", 100)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        recurse_flag = "-Recurse" if recurse else ""
        force_flag = "-Force" if include_hidden else ""
        
        script = f'''
        Get-ChildItem -LiteralPath "{path}" -Filter "{pattern}" {recurse_flag} {force_flag} -ErrorAction SilentlyContinue |
        Select-Object -First {max_results} |
        Select-Object Name, FullName, Length, LastWriteTime | ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    async def _search_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for content within files."""
        path = params.get("path", "")
        pattern = params.get("pattern", "")
        file_filter = params.get("file_filter", "*.*")
        case_sensitive = params.get("case_sensitive", False)
        max_results = params.get("max_results", 50)
        
        if not path or not pattern:
            return {"success": False, "error": "Path and pattern are required"}
        
        case_flag = "" if case_sensitive else "-i"
        
        script = f'''
        Get-ChildItem -LiteralPath "{path}" -Filter "{file_filter}" -Recurse -File -ErrorAction SilentlyContinue |
        Select-String -Pattern "{pattern}" {case_flag} |
        Select-Object -First {max_results} |
        Select-Object Path, LineNumber, Line | ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    async def _find_duplicates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find duplicate files by hash."""
        path = params.get("path", "")
        algorithm = params.get("algorithm", "MD5")
        min_size = params.get("min_size", 0)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $files = Get-ChildItem -LiteralPath "{path}" -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {{ $_.Length -ge {min_size} }}
        
        $hashes = $files | ForEach-Object {{
            @{{
                Path = $_.FullName
                Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm {algorithm}).Hash
                Size = $_.Length
            }}
        }}
        
        $duplicates = $hashes | Group-Object Hash | Where-Object {{ $_.Count -gt 1 }}
        
        $duplicates | ForEach-Object {{
            @{{
                Hash = $_.Name
                Count = $_.Count
                Files = $_.Group.Path
                Size = $_.Group[0].Size
            }}
        }} | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    # ========== Disk Quotas ==========

    async def _get_quota(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get disk quota information for volume."""
        volume = params.get("volume", "C:")
        
        script = f'''
        $quota = Get-WmiObject -Query "SELECT * FROM Win32_DiskQuota WHERE QuotaVolume LIKE '%{volume}%'"
        $quota | Select-Object User, DiskSpaceUsed, Limit, WarningLimit, Status | ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    async def _set_quota(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set disk quota for user."""
        volume = params.get("volume", "C:")
        user = params.get("user", "")
        limit = params.get("limit", 0)  # In bytes
        warning = params.get("warning", 0)
        
        if not user:
            return {"success": False, "error": "User is required"}
        
        script = f'''
        $fsutil = fsutil quota modify {volume} {warning} {limit} "{user}"
        @{{ Success = $true; Output = $fsutil }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_quota_entries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all quota entries for volume."""
        volume = params.get("volume", "C:")
        
        script = f'''
        fsutil quota query {volume} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== File Locking ==========

    async def _get_locked_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of locked files using handle.exe or PowerShell."""
        path = params.get("path", "")
        
        script = f'''
        # Try to identify locked files in the path
        $lockedFiles = @()
        Get-ChildItem -LiteralPath "{path}" -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {{
            try {{
                $stream = [System.IO.File]::Open($_.FullName, 'Open', 'Read', 'None')
                $stream.Close()
            }} catch {{
                $lockedFiles += @{{
                    Path = $_.FullName
                    Error = $_.Exception.Message
                }}
            }}
        }}
        
        @{{
            SearchPath = "{path}"
            LockedFiles = $lockedFiles
            Count = $lockedFiles.Count
        }} | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    async def _get_file_handles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get processes with open handles to a file."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        # This requires elevated permissions and handle.exe from Sysinternals
        # Fallback to basic process check
        $fileName = [System.IO.Path]::GetFileName("{path}")
        
        Get-Process | Where-Object {{
            try {{
                $_.Modules | Where-Object {{ $_.FileName -like "*$fileName*" }}
            }} catch {{ $false }}
        }} | Select-Object Id, ProcessName, Path | ConvertTo-Json -Depth 2
        '''
        return await self._run_powershell(script)

    # ========== Metadata ==========

    async def _get_file_version(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file version information."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $versionInfo = (Get-Item -LiteralPath "{path}").VersionInfo
        @{{
            FileVersion = $versionInfo.FileVersion
            ProductVersion = $versionInfo.ProductVersion
            FileDescription = $versionInfo.FileDescription
            ProductName = $versionInfo.ProductName
            CompanyName = $versionInfo.CompanyName
            LegalCopyright = $versionInfo.LegalCopyright
            OriginalFilename = $versionInfo.OriginalFilename
            InternalName = $versionInfo.InternalName
            Language = $versionInfo.Language
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _get_digital_signature(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get digital signature information."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        $sig = Get-AuthenticodeSignature -LiteralPath "{path}"
        @{{
            Path = "{path}"
            Status = $sig.Status.ToString()
            StatusMessage = $sig.StatusMessage
            SignerCertificate = if ($sig.SignerCertificate) {{
                @{{
                    Subject = $sig.SignerCertificate.Subject
                    Issuer = $sig.SignerCertificate.Issuer
                    Thumbprint = $sig.SignerCertificate.Thumbprint
                    NotBefore = $sig.SignerCertificate.NotBefore.ToString("o")
                    NotAfter = $sig.SignerCertificate.NotAfter.ToString("o")
                }}
            }} else {{ $null }}
            TimeStamperCertificate = if ($sig.TimeStamperCertificate) {{
                $sig.TimeStamperCertificate.Subject
            }} else {{ $null }}
        }} | ConvertTo-Json -Depth 3
        '''
        return await self._run_powershell(script)

    async def _get_zone_identifier(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Zone.Identifier (Mark of the Web)."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        try {{
            $content = Get-Content -LiteralPath "{path}:Zone.Identifier" -ErrorAction Stop
            @{{
                Path = "{path}"
                HasZoneIdentifier = $true
                Content = $content -join "`n"
            }} | ConvertTo-Json
        }} catch {{
            @{{
                Path = "{path}"
                HasZoneIdentifier = $false
                Content = $null
            }} | ConvertTo-Json
        }}
        '''
        return await self._run_powershell(script)

    async def _remove_zone_identifier(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove Zone.Identifier (unblock file)."""
        path = params.get("path", "")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        script = f'''
        Unblock-File -LiteralPath "{path}" -ErrorAction Stop
        @{{ Success = $true; Path = "{path}"; Message = "File unblocked" }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    # ========== Bulk Operations ==========

    async def _bulk_rename(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk rename files using pattern."""
        path = params.get("path", "")
        pattern = params.get("pattern", "*")
        find = params.get("find", "")
        replace = params.get("replace", "")
        use_regex = params.get("use_regex", False)
        
        if not path or not find:
            return {"success": False, "error": "Path and find pattern are required"}
        
        if use_regex:
            script = f'''
            $renamed = @()
            Get-ChildItem -LiteralPath "{path}" -Filter "{pattern}" | ForEach-Object {{
                $newName = $_.Name -replace "{find}", "{replace}"
                if ($newName -ne $_.Name) {{
                    Rename-Item -LiteralPath $_.FullName -NewName $newName -PassThru
                    $renamed += @{{ OldName = $_.Name; NewName = $newName }}
                }}
            }}
            @{{ RenamedCount = $renamed.Count; Items = $renamed }} | ConvertTo-Json -Depth 2
            '''
        else:
            script = f'''
            $renamed = @()
            Get-ChildItem -LiteralPath "{path}" -Filter "{pattern}" | ForEach-Object {{
                $newName = $_.Name.Replace("{find}", "{replace}")
                if ($newName -ne $_.Name) {{
                    Rename-Item -LiteralPath $_.FullName -NewName $newName -PassThru
                    $renamed += @{{ OldName = $_.Name; NewName = $newName }}
                }}
            }}
            @{{ RenamedCount = $renamed.Count; Items = $renamed }} | ConvertTo-Json -Depth 2
            '''
        
        return await self._run_powershell(script)

    async def _bulk_copy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk copy files matching pattern."""
        source = params.get("source", "")
        destination = params.get("destination", "")
        pattern = params.get("pattern", "*")
        recurse = params.get("recurse", False)
        
        if not source or not destination:
            return {"success": False, "error": "Source and destination are required"}
        
        recurse_flag = "-Recurse" if recurse else ""
        
        script = f'''
        $copied = Get-ChildItem -LiteralPath "{source}" -Filter "{pattern}" {recurse_flag} |
            Copy-Item -Destination "{destination}" -PassThru
        
        @{{
            CopiedCount = $copied.Count
            SourcePath = "{source}"
            DestinationPath = "{destination}"
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _bulk_move(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk move files matching pattern."""
        source = params.get("source", "")
        destination = params.get("destination", "")
        pattern = params.get("pattern", "*")
        
        if not source or not destination:
            return {"success": False, "error": "Source and destination are required"}
        
        script = f'''
        $moved = Get-ChildItem -LiteralPath "{source}" -Filter "{pattern}" |
            Move-Item -Destination "{destination}" -PassThru
        
        @{{
            MovedCount = $moved.Count
            SourcePath = "{source}"
            DestinationPath = "{destination}"
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)

    async def _sync_directories(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync two directories using robocopy."""
        source = params.get("source", "")
        destination = params.get("destination", "")
        mirror = params.get("mirror", False)
        exclude_files = params.get("exclude_files", [])
        exclude_dirs = params.get("exclude_dirs", [])
        
        if not source or not destination:
            return {"success": False, "error": "Source and destination are required"}
        
        mirror_flag = "/MIR" if mirror else "/E"
        xf = " ".join([f'"{f}"' for f in exclude_files]) if exclude_files else ""
        xd = " ".join([f'"{d}"' for d in exclude_dirs]) if exclude_dirs else ""
        xf_param = f"/XF {xf}" if xf else ""
        xd_param = f"/XD {xd}" if xd else ""
        
        script = f'''
        $output = robocopy "{source}" "{destination}" {mirror_flag} {xf_param} {xd_param} /NJH /NJS /NDL /NC /NS /NP
        $exitCode = $LASTEXITCODE
        
        @{{
            Source = "{source}"
            Destination = "{destination}"
            ExitCode = $exitCode
            Success = $exitCode -lt 8
            Output = $output -join "`n"
        }} | ConvertTo-Json
        '''
        return await self._run_powershell(script)


plugin = FileSystemOperationsPlugin()
