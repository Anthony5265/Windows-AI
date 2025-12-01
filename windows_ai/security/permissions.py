"""
Permission Manager for Windows AI
Manages access control and user permissions
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class PermissionLevel(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    EXECUTE = 3
    ADMIN = 4

class ResourceType(Enum):
    FILE = "file"
    DIRECTORY = "directory"
    API = "api"
    MODEL = "model"
    PLUGIN = "plugin"
    SYSTEM = "system"
    NETWORK = "network"

@dataclass
class Permission:
    resource_type: ResourceType
    resource_id: str
    level: PermissionLevel
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Role:
    name: str
    permissions: Set[str] = field(default_factory=set)
    inherit_from: Optional[str] = None

class PermissionManager:
    """Manages permissions and access control"""

    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, Set[str]] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize permission manager"""
        if self._initialized:
            return

        # Create default roles
        self._create_default_roles()

        self._initialized = True
        logger.info("Permission manager initialized")

    def _create_default_roles(self):
        """Create default roles"""
        # Guest role - minimal access
        self.roles["guest"] = Role(
            name="guest",
            permissions={
                "api:read",
                "model:use:basic"
            }
        )

        # User role - standard access
        self.roles["user"] = Role(
            name="user",
            permissions={
                "api:read",
                "api:write",
                "model:use:*",
                "plugin:use:*",
                "file:read:workspace",
                "file:write:workspace"
            },
            inherit_from="guest"
        )

        # Power user role
        self.roles["power_user"] = Role(
            name="power_user",
            permissions={
                "model:configure",
                "plugin:install",
                "system:read",
                "network:external"
            },
            inherit_from="user"
        )

        # Admin role - full access
        self.roles["admin"] = Role(
            name="admin",
            permissions={
                "system:*",
                "file:*",
                "api:*",
                "model:*",
                "plugin:*",
                "network:*"
            },
            inherit_from="power_user"
        )

    def create_role(self, name: str, permissions: Set[str], inherit_from: Optional[str] = None):
        """Create a new role"""
        self.roles[name] = Role(
            name=name,
            permissions=permissions,
            inherit_from=inherit_from
        )
        logger.info(f"Created role: {name}")

    def assign_role(self, user_id: str, role_name: str):
        """Assign a role to a user"""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' not found")

        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()

        self.user_roles[user_id].add(role_name)
        logger.info(f"Assigned role '{role_name}' to user '{user_id}'")

    def revoke_role(self, user_id: str, role_name: str):
        """Revoke a role from a user"""
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_name)

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user"""
        permissions = set()

        roles = self.user_roles.get(user_id, {"guest"})

        for role_name in roles:
            permissions.update(self._get_role_permissions(role_name))

        return permissions

    def _get_role_permissions(self, role_name: str) -> Set[str]:
        """Get all permissions for a role (including inherited)"""
        if role_name not in self.roles:
            return set()

        role = self.roles[role_name]
        permissions = role.permissions.copy()

        if role.inherit_from:
            permissions.update(self._get_role_permissions(role.inherit_from))

        return permissions

    def check_permission(
        self,
        user_id: str,
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if a user has permission for an action"""
        permissions = self.get_user_permissions(user_id)

        # Check for wildcard permission
        if f"{resource_type}:*" in permissions:
            return True

        # Check for specific action wildcard
        if f"{resource_type}:{action}:*" in permissions:
            return True

        # Check for exact permission
        if resource_id:
            if f"{resource_type}:{action}:{resource_id}" in permissions:
                return True
        else:
            if f"{resource_type}:{action}" in permissions:
                return True

        return False

    def require_permission(
        self,
        user_id: str,
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None
    ):
        """Require a permission, raise if not granted"""
        if not self.check_permission(user_id, resource_type, action, resource_id):
            raise PermissionError(
                f"Permission denied: {resource_type}:{action}"
                + (f":{resource_id}" if resource_id else "")
            )

    def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles"""
        return [
            {
                "name": role.name,
                "permissions": list(role.permissions),
                "inherit_from": role.inherit_from
            }
            for role in self.roles.values()
        ]

    def get_user_roles(self, user_id: str) -> List[str]:
        """Get roles for a user"""
        return list(self.user_roles.get(user_id, {"guest"}))
