"""
Windows Active Directory Integration - PRODUCTION

Provides comprehensive Active Directory management capabilities including:
- User management (create, modify, delete, search)
- Group management (create, modify, membership)
- Computer object management
- OU operations
- Password resets and account management
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType
import logging

logger = logging.getLogger(__name__)


class WindowsActiveDirectoryPlugin(IntegrationPlugin):
    """Windows Active Directory plugin with comprehensive AD management."""
    
    def __init__(self):
        metadata = PluginMetadata(
            id="windows_active_directory",
            name="Windows Active Directory",
            description="Active Directory management - users, groups, computers, OUs, password management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "active_directory", "ad", "users", "groups", "ldap"]
        )
        super().__init__(metadata)
        self.connected = False
        self._ad_available = False
        self._domain = None

    async def initialize(self) -> bool:
        """Initialize and check AD module availability."""
        result = await self._run_powershell("Get-Module -ListAvailable ActiveDirectory | Select-Object -ExpandProperty Name")
        self._ad_available = result["success"] and "ActiveDirectory" in result.get("output", "")
        if self._ad_available:
            domain_result = await self._run_powershell("(Get-ADDomain).DNSRoot")
            if domain_result["success"]:
                self._domain = domain_result["output"].strip()
                logger.info(f"AD domain: {self._domain}")
        else:
            logger.warning("Active Directory module not available")
        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect (may use alternate credentials)."""
        self.connected = True
        return True

    async def disconnect(self) -> bool:
        """Disconnect."""
        self.connected = False
        return True

    async def _run_powershell(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute a PowerShell command."""
        try:
            full_command = f"Import-Module ActiveDirectory -ErrorAction SilentlyContinue; {command}"
            process = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-Command", full_command,
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
        """Execute an Active Directory operation."""
        if not self.connected:
            return {"success": False, "error": "Not connected"}

        actions = {
            # User operations
            "list_users": self._list_users,
            "get_user": self._get_user,
            "create_user": self._create_user,
            "delete_user": self._delete_user,
            "enable_user": self._enable_user,
            "disable_user": self._disable_user,
            "unlock_user": self._unlock_user,
            "reset_password": self._reset_password,
            "set_user": self._set_user,
            "search_users": self._search_users,
            # Group operations
            "list_groups": self._list_groups,
            "get_group": self._get_group,
            "create_group": self._create_group,
            "delete_group": self._delete_group,
            "add_group_member": self._add_group_member,
            "remove_group_member": self._remove_group_member,
            "get_group_members": self._get_group_members,
            # Computer operations
            "list_computers": self._list_computers,
            "get_computer": self._get_computer,
            "disable_computer": self._disable_computer,
            "delete_computer": self._delete_computer,
            # OU operations
            "list_ous": self._list_ous,
            "create_ou": self._create_ou,
            "delete_ou": self._delete_ou,
            # Domain info
            "get_domain_info": self._get_domain_info,
            "get_domain_controllers": self._get_domain_controllers,
            "status": self._get_status,
        }

        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}. Available: {list(actions.keys())}"}

        try:
            return await actions[action](parameters)
        except Exception as e:
            logger.error(f"AD operation failed: {e}")
            return {"success": False, "error": str(e)}

    # User operations
    async def _list_users(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List AD users."""
        search_base = params.get("search_base", "")
        filter_str = params.get("filter", "*")
        properties = params.get("properties", ["Name", "SamAccountName", "EmailAddress", "Enabled", "LastLogonDate"])
        limit = params.get("limit", 100)
        
        props = ",".join(properties) if isinstance(properties, list) else properties
        cmd = f"Get-ADUser -Filter {{Name -like '{filter_str}'}} -Properties {props}"
        if search_base:
            cmd += f" -SearchBase '{search_base}'"
        cmd += f" | Select-Object -First {limit} {props} | ConvertTo-Json -Depth 2"
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                users = json.loads(result["output"]) if result["output"] else []
                if isinstance(users, dict):
                    users = [users]
                return {"success": True, "users": users, "count": len(users)}
            except json.JSONDecodeError:
                return {"success": True, "users": [], "raw_output": result["output"]}
        return result

    async def _get_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed user information."""
        identity = params.get("identity") or params.get("username") or params.get("sam_account_name")
        if not identity:
            return {"success": False, "error": "User identity required"}
        
        cmd = f"Get-ADUser -Identity '{identity}' -Properties * | ConvertTo-Json -Depth 3"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                user = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "user": user}
            except json.JSONDecodeError:
                return result
        return result

    async def _create_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AD user."""
        sam_account_name = params.get("sam_account_name") or params.get("username")
        name = params.get("name")
        if not sam_account_name or not name:
            return {"success": False, "error": "sam_account_name and name required"}
        
        given_name = params.get("given_name", "")
        surname = params.get("surname", "")
        email = params.get("email", "")
        password = params.get("password", "")
        path = params.get("path", "")
        enabled = params.get("enabled", True)
        
        cmd = f"New-ADUser -Name '{name}' -SamAccountName '{sam_account_name}'"
        if given_name:
            cmd += f" -GivenName '{given_name}'"
        if surname:
            cmd += f" -Surname '{surname}'"
        if email:
            cmd += f" -EmailAddress '{email}'"
        if path:
            cmd += f" -Path '{path}'"
        if password:
            cmd += f" -AccountPassword (ConvertTo-SecureString '{password}' -AsPlainText -Force)"
        cmd += f" -Enabled ${'$true' if enabled else '$false'}"
        
        result = await self._run_powershell(cmd)
        if result["success"] or not result.get("error"):
            return {"success": True, "message": f"User '{sam_account_name}' created"}
        return result

    async def _delete_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an AD user."""
        identity = params.get("identity") or params.get("username")
        if not identity:
            return {"success": False, "error": "User identity required"}
        
        confirm = "$false" if params.get("force", False) else "$true"
        cmd = f"Remove-ADUser -Identity '{identity}' -Confirm:{confirm}"
        return await self._run_powershell(cmd)

    async def _enable_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable an AD user account."""
        identity = params.get("identity") or params.get("username")
        if not identity:
            return {"success": False, "error": "User identity required"}
        return await self._run_powershell(f"Enable-ADAccount -Identity '{identity}'")

    async def _disable_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable an AD user account."""
        identity = params.get("identity") or params.get("username")
        if not identity:
            return {"success": False, "error": "User identity required"}
        return await self._run_powershell(f"Disable-ADAccount -Identity '{identity}'")

    async def _unlock_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock an AD user account."""
        identity = params.get("identity") or params.get("username")
        if not identity:
            return {"success": False, "error": "User identity required"}
        return await self._run_powershell(f"Unlock-ADAccount -Identity '{identity}'")

    async def _reset_password(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset user password."""
        identity = params.get("identity") or params.get("username")
        new_password = params.get("new_password") or params.get("password")
        if not identity or not new_password:
            return {"success": False, "error": "Identity and new_password required"}
        
        must_change = "$true" if params.get("must_change_at_logon", False) else "$false"
        cmd = f"Set-ADAccountPassword -Identity '{identity}' -NewPassword (ConvertTo-SecureString '{new_password}' -AsPlainText -Force) -Reset; "
        cmd += f"Set-ADUser -Identity '{identity}' -ChangePasswordAtLogon {must_change}"
        return await self._run_powershell(cmd)

    async def _set_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update AD user properties."""
        identity = params.get("identity") or params.get("username")
        if not identity:
            return {"success": False, "error": "User identity required"}
        
        cmd = f"Set-ADUser -Identity '{identity}'"
        if params.get("email"):
            cmd += f" -EmailAddress '{params['email']}'"
        if params.get("display_name"):
            cmd += f" -DisplayName '{params['display_name']}'"
        if params.get("title"):
            cmd += f" -Title '{params['title']}'"
        if params.get("department"):
            cmd += f" -Department '{params['department']}'"
        if params.get("company"):
            cmd += f" -Company '{params['company']}'"
        if params.get("office"):
            cmd += f" -Office '{params['office']}'"
        if params.get("manager"):
            cmd += f" -Manager '{params['manager']}'"
        
        return await self._run_powershell(cmd)

    async def _search_users(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for AD users."""
        search_term = params.get("search") or params.get("query") or "*"
        limit = params.get("limit", 100)
        
        cmd = f"Get-ADUser -Filter {{(Name -like '*{search_term}*') -or (SamAccountName -like '*{search_term}*') -or (EmailAddress -like '*{search_term}*')}} -Properties Name,SamAccountName,EmailAddress,Enabled | Select-Object -First {limit} Name,SamAccountName,EmailAddress,Enabled | ConvertTo-Json"
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                users = json.loads(result["output"]) if result["output"] else []
                if isinstance(users, dict):
                    users = [users]
                return {"success": True, "users": users, "count": len(users)}
            except json.JSONDecodeError:
                return {"success": True, "users": [], "raw_output": result["output"]}
        return result

    # Group operations
    async def _list_groups(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List AD groups."""
        filter_str = params.get("filter", "*")
        limit = params.get("limit", 100)
        
        cmd = f"Get-ADGroup -Filter {{Name -like '{filter_str}'}} | Select-Object -First {limit} Name,SamAccountName,GroupScope,GroupCategory | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                groups = json.loads(result["output"]) if result["output"] else []
                if isinstance(groups, dict):
                    groups = [groups]
                return {"success": True, "groups": groups, "count": len(groups)}
            except json.JSONDecodeError:
                return {"success": True, "groups": [], "raw_output": result["output"]}
        return result

    async def _get_group(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get group details."""
        identity = params.get("identity") or params.get("name")
        if not identity:
            return {"success": False, "error": "Group identity required"}
        
        cmd = f"Get-ADGroup -Identity '{identity}' -Properties * | ConvertTo-Json -Depth 2"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                group = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "group": group}
            except json.JSONDecodeError:
                return result
        return result

    async def _create_group(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AD group."""
        name = params.get("name")
        if not name:
            return {"success": False, "error": "Group name required"}
        
        scope = params.get("scope", "Global")
        category = params.get("category", "Security")
        path = params.get("path", "")
        description = params.get("description", "")
        
        cmd = f"New-ADGroup -Name '{name}' -GroupScope {scope} -GroupCategory {category}"
        if path:
            cmd += f" -Path '{path}'"
        if description:
            cmd += f" -Description '{description}'"
        
        result = await self._run_powershell(cmd)
        if result["success"] or not result.get("error"):
            return {"success": True, "message": f"Group '{name}' created"}
        return result

    async def _delete_group(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an AD group."""
        identity = params.get("identity") or params.get("name")
        if not identity:
            return {"success": False, "error": "Group identity required"}
        return await self._run_powershell(f"Remove-ADGroup -Identity '{identity}' -Confirm:$false")

    async def _add_group_member(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add member to group."""
        group = params.get("group")
        member = params.get("member") or params.get("user")
        if not group or not member:
            return {"success": False, "error": "Group and member required"}
        return await self._run_powershell(f"Add-ADGroupMember -Identity '{group}' -Members '{member}'")

    async def _remove_group_member(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove member from group."""
        group = params.get("group")
        member = params.get("member") or params.get("user")
        if not group or not member:
            return {"success": False, "error": "Group and member required"}
        return await self._run_powershell(f"Remove-ADGroupMember -Identity '{group}' -Members '{member}' -Confirm:$false")

    async def _get_group_members(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get group members."""
        identity = params.get("identity") or params.get("group")
        if not identity:
            return {"success": False, "error": "Group identity required"}
        
        cmd = f"Get-ADGroupMember -Identity '{identity}' | Select-Object Name,SamAccountName,objectClass | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                members = json.loads(result["output"]) if result["output"] else []
                if isinstance(members, dict):
                    members = [members]
                return {"success": True, "members": members, "count": len(members)}
            except json.JSONDecodeError:
                return {"success": True, "members": [], "raw_output": result["output"]}
        return result

    # Computer operations
    async def _list_computers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List AD computers."""
        filter_str = params.get("filter", "*")
        limit = params.get("limit", 100)
        
        cmd = f"Get-ADComputer -Filter {{Name -like '{filter_str}'}} -Properties OperatingSystem,LastLogonDate | Select-Object -First {limit} Name,DNSHostName,OperatingSystem,Enabled,LastLogonDate | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                computers = json.loads(result["output"]) if result["output"] else []
                if isinstance(computers, dict):
                    computers = [computers]
                return {"success": True, "computers": computers, "count": len(computers)}
            except json.JSONDecodeError:
                return {"success": True, "computers": [], "raw_output": result["output"]}
        return result

    async def _get_computer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get computer details."""
        identity = params.get("identity") or params.get("name")
        if not identity:
            return {"success": False, "error": "Computer identity required"}
        
        cmd = f"Get-ADComputer -Identity '{identity}' -Properties * | ConvertTo-Json -Depth 2"
        return await self._run_powershell(cmd)

    async def _disable_computer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable a computer account."""
        identity = params.get("identity") or params.get("name")
        if not identity:
            return {"success": False, "error": "Computer identity required"}
        return await self._run_powershell(f"Disable-ADAccount -Identity '{identity}'")

    async def _delete_computer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a computer account."""
        identity = params.get("identity") or params.get("name")
        if not identity:
            return {"success": False, "error": "Computer identity required"}
        return await self._run_powershell(f"Remove-ADComputer -Identity '{identity}' -Confirm:$false")

    # OU operations
    async def _list_ous(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List organizational units."""
        search_base = params.get("search_base", "")
        
        cmd = "Get-ADOrganizationalUnit -Filter * -Properties Description"
        if search_base:
            cmd += f" -SearchBase '{search_base}'"
        cmd += " | Select-Object Name,DistinguishedName,Description | ConvertTo-Json"
        
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                ous = json.loads(result["output"]) if result["output"] else []
                if isinstance(ous, dict):
                    ous = [ous]
                return {"success": True, "ous": ous, "count": len(ous)}
            except json.JSONDecodeError:
                return {"success": True, "ous": [], "raw_output": result["output"]}
        return result

    async def _create_ou(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an organizational unit."""
        name = params.get("name")
        path = params.get("path")
        if not name:
            return {"success": False, "error": "OU name required"}
        
        cmd = f"New-ADOrganizationalUnit -Name '{name}'"
        if path:
            cmd += f" -Path '{path}'"
        if params.get("description"):
            cmd += f" -Description '{params['description']}'"
        
        result = await self._run_powershell(cmd)
        if result["success"] or not result.get("error"):
            return {"success": True, "message": f"OU '{name}' created"}
        return result

    async def _delete_ou(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an organizational unit."""
        identity = params.get("identity") or params.get("distinguished_name")
        if not identity:
            return {"success": False, "error": "OU identity required"}
        
        cmd = f"Set-ADOrganizationalUnit -Identity '{identity}' -ProtectedFromAccidentalDeletion $false; "
        cmd += f"Remove-ADOrganizationalUnit -Identity '{identity}' -Confirm:$false"
        return await self._run_powershell(cmd)

    # Domain info
    async def _get_domain_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get domain information."""
        cmd = "Get-ADDomain | ConvertTo-Json -Depth 2"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                domain = json.loads(result["output"]) if result["output"] else None
                return {"success": True, "domain": domain}
            except json.JSONDecodeError:
                return result
        return result

    async def _get_domain_controllers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get domain controllers."""
        cmd = "Get-ADDomainController -Filter * | Select-Object Name,IPv4Address,Site,OperatingSystem,IsGlobalCatalog,IsReadOnly | ConvertTo-Json"
        result = await self._run_powershell(cmd)
        if result["success"]:
            try:
                dcs = json.loads(result["output"]) if result["output"] else []
                if isinstance(dcs, dict):
                    dcs = [dcs]
                return {"success": True, "domain_controllers": dcs, "count": len(dcs)}
            except json.JSONDecodeError:
                return {"success": True, "domain_controllers": [], "raw_output": result["output"]}
        return result

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get AD module and domain status."""
        return {
            "success": True,
            "ad_module_available": self._ad_available,
            "domain": self._domain,
            "connected": self.connected
        }

    async def shutdown(self):
        """Shutdown the plugin."""
        self._initialized = False

    def get_schema(self) -> Dict[str, Any]:
        """Return the plugin schema."""
        return {
            "type": "object",
            "actions": {
                "list_users": {"description": "List AD users", "params": ["search_base", "filter", "properties", "limit"]},
                "get_user": {"description": "Get user details", "params": ["identity"]},
                "create_user": {"description": "Create AD user", "params": ["sam_account_name", "name", "given_name", "surname", "email", "password", "path", "enabled"]},
                "delete_user": {"description": "Delete AD user", "params": ["identity", "force"]},
                "enable_user": {"description": "Enable user account", "params": ["identity"]},
                "disable_user": {"description": "Disable user account", "params": ["identity"]},
                "unlock_user": {"description": "Unlock user account", "params": ["identity"]},
                "reset_password": {"description": "Reset user password", "params": ["identity", "new_password", "must_change_at_logon"]},
                "list_groups": {"description": "List AD groups", "params": ["filter", "limit"]},
                "get_group": {"description": "Get group details", "params": ["identity"]},
                "create_group": {"description": "Create AD group", "params": ["name", "scope", "category", "path", "description"]},
                "add_group_member": {"description": "Add member to group", "params": ["group", "member"]},
                "remove_group_member": {"description": "Remove member from group", "params": ["group", "member"]},
                "list_computers": {"description": "List AD computers", "params": ["filter", "limit"]},
                "list_ous": {"description": "List organizational units", "params": ["search_base"]},
                "get_domain_info": {"description": "Get domain information"},
                "get_domain_controllers": {"description": "Get domain controllers"},
                "status": {"description": "Get AD status"}
            }
        }


plugin = WindowsActiveDirectoryPlugin()
