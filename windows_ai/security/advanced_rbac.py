"""Advanced Role-Based Access Control (RBAC).

Fine-grained permissions, role hierarchy, and delegation.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Permission levels."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class ResourceType(str, Enum):
    """Resource types in the system."""
    QUERY = "query"
    PLUGIN = "plugin"
    DASHBOARD = "dashboard"
    REPORT = "report"
    CONFIGURATION = "configuration"
    USER = "user"
    ROLE = "role"


@dataclass
class Permission:
    """Individual permission."""
    permission_id: str
    resource_type: ResourceType
    level: PermissionLevel
    resource_id: Optional[str] = None  # Specific resource or all
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def matches(self, resource_type: ResourceType, level: PermissionLevel, resource_id: Optional[str] = None) -> bool:
        """Check if permission matches criteria."""
        if self.resource_type != resource_type:
            return False

        if level not in [self.level, PermissionLevel.ADMIN]:
            return False

        if self.resource_id and resource_id and self.resource_id != resource_id:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "permission_id": self.permission_id,
            "resource_type": self.resource_type.value,
            "level": self.level.value,
            "resource_id": self.resource_id,
            "conditions": self.conditions,
        }


@dataclass
class Role:
    """Role definition."""
    role_id: str
    name: str
    description: str
    permissions: Set[str]
    parent_role_id: Optional[str] = None
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "permissions_count": len(self.permissions),
            "parent_role_id": self.parent_role_id,
            "is_system_role": self.is_system_role,
        }


@dataclass
class User:
    """User with roles and permissions."""
    user_id: str
    username: str
    email: str
    roles: Set[str]
    direct_permissions: Set[str] = field(default_factory=set)
    delegated_roles: Dict[str, datetime] = field(default_factory=dict)  # role_id -> expiry
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles_count": len(self.roles),
            "direct_permissions_count": len(self.direct_permissions),
            "delegated_roles_count": len(self.delegated_roles),
            "is_active": self.is_active,
        }


class AdvancedRBAC:
    """Advanced RBAC system."""

    def __init__(self):
        """Initialize RBAC."""
        self.permissions: Dict[str, Permission] = {}
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.audit_log: List[Dict[str, Any]] = []

    async def create_permission(
        self,
        resource_type: ResourceType,
        level: PermissionLevel,
        resource_id: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Permission:
        """Create a permission.

        Args:
            resource_type: Type of resource
            level: Permission level
            resource_id: Specific resource ID or None for all
            conditions: Additional conditions

        Returns:
            Created permission
        """
        permission_id = f"perm_{resource_type.value}_{level.value}_{resource_id or 'all'}"

        permission = Permission(
            permission_id=permission_id,
            resource_type=resource_type,
            level=level,
            resource_id=resource_id,
            conditions=conditions or {},
        )

        self.permissions[permission_id] = permission
        self._log_action("permission_created", {"permission_id": permission_id})

        return permission

    async def create_role(
        self,
        name: str,
        description: str,
        permissions: Optional[Set[str]] = None,
        parent_role_id: Optional[str] = None,
        is_system_role: bool = False,
    ) -> Role:
        """Create a role.

        Args:
            name: Role name
            description: Role description
            permissions: Permission IDs
            parent_role_id: Parent role for inheritance
            is_system_role: Whether this is a system role

        Returns:
            Created role
        """
        role_id = f"role_{name.lower().replace(' ', '_')}"

        # Include parent permissions
        all_permissions = set(permissions or [])
        if parent_role_id and parent_role_id in self.roles:
            parent = self.roles[parent_role_id]
            all_permissions.update(parent.permissions)

        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            permissions=all_permissions,
            parent_role_id=parent_role_id,
            is_system_role=is_system_role,
        )

        self.roles[role_id] = role
        self._log_action("role_created", {"role_id": role_id, "name": name})

        return role

    async def create_user(
        self,
        username: str,
        email: str,
        roles: Optional[Set[str]] = None,
    ) -> User:
        """Create a user.

        Args:
            username: Username
            email: Email address
            roles: Role IDs to assign

        Returns:
            Created user
        """
        user_id = f"user_{username.lower()}"

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            roles=roles or set(),
        )

        self.users[user_id] = user
        self._log_action("user_created", {"user_id": user_id, "username": username})

        return user

    async def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        temporary: bool = False,
        expiry_hours: Optional[int] = None,
    ) -> bool:
        """Assign role to user.

        Args:
            user_id: User ID
            role_id: Role ID
            temporary: Whether assignment is temporary
            expiry_hours: Hours until expiry (if temporary)

        Returns:
            Success status
        """
        user = self.users.get(user_id)
        role = self.roles.get(role_id)

        if not user or not role:
            return False

        if temporary and expiry_hours:
            expiry = datetime.now() + timedelta(hours=expiry_hours)
            user.delegated_roles[role_id] = expiry
        else:
            user.roles.add(role_id)

        self._log_action("role_assigned", {
            "user_id": user_id,
            "role_id": role_id,
            "temporary": temporary,
        })

        return True

    async def grant_permission_to_user(
        self,
        user_id: str,
        permission_id: str,
    ) -> bool:
        """Grant permission directly to user.

        Args:
            user_id: User ID
            permission_id: Permission ID

        Returns:
            Success status
        """
        user = self.users.get(user_id)
        permission = self.permissions.get(permission_id)

        if not user or not permission:
            return False

        user.direct_permissions.add(permission_id)
        self._log_action("permission_granted", {
            "user_id": user_id,
            "permission_id": permission_id,
        })

        return True

    async def check_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        level: PermissionLevel,
        resource_id: Optional[str] = None,
    ) -> bool:
        """Check if user has permission.

        Args:
            user_id: User ID
            resource_type: Resource type
            level: Permission level
            resource_id: Specific resource ID

        Returns:
            True if user has permission
        """
        user = self.users.get(user_id)

        if not user or not user.is_active:
            return False

        # Clean up expired delegated roles
        now = datetime.now()
        user.delegated_roles = {
            role_id: expiry
            for role_id, expiry in user.delegated_roles.items()
            if expiry > now
        }

        # Check all roles (direct + delegated)
        all_roles = user.roles | set(user.delegated_roles.keys())

        for role_id in all_roles:
            role = self.roles.get(role_id)
            if not role:
                continue

            for perm_id in role.permissions:
                perm = self.permissions.get(perm_id)
                if perm and perm.matches(resource_type, level, resource_id):
                    return True

        # Check direct permissions
        for perm_id in user.direct_permissions:
            perm = self.permissions.get(perm_id)
            if perm and perm.matches(resource_type, level, resource_id):
                return True

        return False

    async def delegate_role(
        self,
        delegator_id: str,
        delegatee_id: str,
        role_id: str,
        hours: int = 24,
    ) -> bool:
        """Delegate role from one user to another.

        Args:
            delegator_id: User delegating
            delegatee_id: User receiving delegation
            role_id: Role ID
            hours: Duration of delegation

        Returns:
            Success status
        """
        delegator = self.users.get(delegator_id)
        delegatee = self.users.get(delegatee_id)

        if not delegator or not delegatee:
            return False

        # Check if delegator has the role
        if role_id not in delegator.roles:
            return False

        return await self.assign_role_to_user(
            delegatee_id,
            role_id,
            temporary=True,
            expiry_hours=hours,
        )

    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user.

        Args:
            user_id: User ID

        Returns:
            Set of permission IDs
        """
        user = self.users.get(user_id)

        if not user:
            return set()

        all_permissions = set(user.direct_permissions)

        for role_id in user.roles | set(user.delegated_roles.keys()):
            role = self.roles.get(role_id)
            if role:
                all_permissions.update(role.permissions)

        return all_permissions

    async def create_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Create audit report.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Audit report
        """
        relevant_logs = [
            log for log in self.audit_log
            if start_date <= log.get("timestamp", datetime.now()) <= end_date
        ]

        actions_summary = {}
        for log in relevant_logs:
            action = log.get("action", "unknown")
            actions_summary[action] = actions_summary.get(action, 0) + 1

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_actions": len(relevant_logs),
            "actions_summary": actions_summary,
            "audit_log": relevant_logs[-100:],  # Last 100 entries
        }

    def _log_action(self, action: str, details: Dict[str, Any]):
        """Log RBAC action.

        Args:
            action: Action name
            details: Action details
        """
        self.audit_log.append({
            "action": action,
            "timestamp": datetime.now(),
            "details": details,
        })

    async def get_rbac_status(self) -> Dict[str, Any]:
        """Get RBAC system status.

        Returns:
            RBAC status summary
        """
        return {
            "total_permissions": len(self.permissions),
            "total_roles": len(self.roles),
            "system_roles": sum(1 for r in self.roles.values() if r.is_system_role),
            "total_users": len(self.users),
            "active_users": sum(1 for u in self.users.values() if u.is_active),
            "audit_log_entries": len(self.audit_log),
            "roles_with_inheritance": sum(1 for r in self.roles.values() if r.parent_role_id),
        }
