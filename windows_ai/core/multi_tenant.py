"""Multi-tenant support for enterprise deployments.

Tenant isolation, routing, and configuration management.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class TenantTier(str, Enum):
    """Tenant subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class DataResidency(str, Enum):
    """Data residency requirements."""
    US = "us"
    EU = "eu"
    APAC = "apac"
    MULTI = "multi"


@dataclass
class TenantConfig:
    """Tenant configuration."""
    tenant_id: str
    name: str
    tier: TenantTier
    region: str
    data_residency: DataResidency
    max_api_calls_per_month: int
    max_concurrent_connections: int
    max_storage_gb: int
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "tier": self.tier.value,
            "region": self.region,
            "data_residency": self.data_residency.value,
            "max_api_calls": self.max_api_calls_per_month,
            "max_connections": self.max_concurrent_connections,
            "max_storage_gb": self.max_storage_gb,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class TenantUsage:
    """Tenant usage metrics."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    api_calls_used: int
    storage_used_gb: float
    peak_concurrent_connections: int
    requests_by_endpoint: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)

    def usage_percent(self, max_api_calls: int) -> float:
        """Calculate API usage percentage."""
        if max_api_calls == 0:
            return 0.0
        return (self.api_calls_used / max_api_calls) * 100


@dataclass
class TenantContext:
    """Tenant execution context."""
    tenant_id: str
    user_id: str
    request_id: str
    permissions: Set[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission: str) -> bool:
        """Check if context has permission."""
        return permission in self.permissions


class TenantRegistry:
    """Registry and manager for multi-tenant infrastructure."""

    def __init__(self):
        """Initialize tenant registry."""
        self.tenants: Dict[str, TenantConfig] = {}
        self.tenant_data: Dict[str, Dict[str, Any]] = {}
        self.usage: Dict[str, TenantUsage] = {}
        self.contexts: List[TenantContext] = []

    async def register_tenant(
        self,
        name: str,
        tier: TenantTier = TenantTier.STARTER,
        region: str = "us-east-1",
        data_residency: DataResidency = DataResidency.US,
    ) -> TenantConfig:
        """Register a new tenant.

        Args:
            name: Tenant name
            tier: Subscription tier
            region: Cloud region
            data_residency: Data residency requirement

        Returns:
            Created tenant configuration
        """
        tenant_id = self._generate_tenant_id(name)

        # Tier-based resource limits
        tier_limits = {
            TenantTier.FREE: {"api": 10_000, "connections": 10, "storage": 1},
            TenantTier.STARTER: {"api": 100_000, "connections": 50, "storage": 10},
            TenantTier.PROFESSIONAL: {"api": 1_000_000, "connections": 200, "storage": 100},
            TenantTier.ENTERPRISE: {"api": 10_000_000, "connections": 1000, "storage": 1000},
        }

        limits = tier_limits.get(tier, tier_limits[TenantTier.STARTER])

        config = TenantConfig(
            tenant_id=tenant_id,
            name=name,
            tier=tier,
            region=region,
            data_residency=data_residency,
            max_api_calls_per_month=limits["api"],
            max_concurrent_connections=limits["connections"],
            max_storage_gb=limits["storage"],
            feature_flags=self._get_tier_features(tier),
        )

        self.tenants[tenant_id] = config
        self.tenant_data[tenant_id] = {}

        logger.info(f"Registered tenant: {name} ({tenant_id})")

        return config

    async def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant configuration or None
        """
        return self.tenants.get(tenant_id)

    async def update_tenant_config(
        self,
        tenant_id: str,
        updates: Dict[str, Any],
    ) -> Optional[TenantConfig]:
        """Update tenant configuration.

        Args:
            tenant_id: Tenant ID
            updates: Configuration updates

        Returns:
            Updated configuration or None
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        # Update allowed fields
        if "feature_flags" in updates:
            tenant.feature_flags.update(updates["feature_flags"])

        if "custom_settings" in updates:
            tenant.custom_settings.update(updates["custom_settings"])

        if "is_active" in updates:
            tenant.is_active = updates["is_active"]

        return tenant

    async def create_tenant_context(
        self,
        tenant_id: str,
        user_id: str,
        request_id: str,
        permissions: Set[str],
    ) -> TenantContext:
        """Create execution context for request.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            request_id: Request ID
            permissions: User permissions

        Returns:
            Tenant context
        """
        context = TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            permissions=permissions,
        )

        self.contexts.append(context)
        return context

    async def record_usage(
        self,
        tenant_id: str,
        api_calls: int,
        storage_gb: float = 0,
        endpoint: str = "",
    ):
        """Record tenant usage.

        Args:
            tenant_id: Tenant ID
            api_calls: Number of API calls
            storage_gb: Storage used
            endpoint: API endpoint
        """
        period_key = f"{datetime.now().strftime('%Y-%m')}"
        usage = self.usage.get(tenant_id)

        if not usage:
            usage = TenantUsage(
                tenant_id=tenant_id,
                period_start=datetime.now(),
                period_end=datetime.now(),
                api_calls_used=api_calls,
                storage_used_gb=storage_gb,
                peak_concurrent_connections=0,
            )
        else:
            usage.api_calls_used += api_calls
            usage.storage_used_gb += storage_gb

        if endpoint:
            usage.requests_by_endpoint[endpoint] = usage.requests_by_endpoint.get(endpoint, 0) + 1

        self.usage[tenant_id] = usage

    async def check_quota(self, tenant_id: str) -> Dict[str, Any]:
        """Check tenant quota usage.

        Args:
            tenant_id: Tenant ID

        Returns:
            Quota status
        """
        tenant = self.tenants.get(tenant_id)
        usage = self.usage.get(tenant_id)

        if not tenant:
            return {"error": "Tenant not found"}

        api_percent = 0
        storage_percent = 0

        if usage:
            api_percent = usage.usage_percent(tenant.max_api_calls_per_month)
            storage_percent = (usage.storage_used_gb / tenant.max_storage_gb * 100) if tenant.max_storage_gb > 0 else 0

        return {
            "tenant_id": tenant_id,
            "api_calls": {
                "used": usage.api_calls_used if usage else 0,
                "limit": tenant.max_api_calls_per_month,
                "percent": api_percent,
            },
            "storage": {
                "used_gb": usage.storage_used_gb if usage else 0,
                "limit_gb": tenant.max_storage_gb,
                "percent": storage_percent,
            },
            "within_quota": api_percent < 90 and storage_percent < 90,
        }

    async def isolate_tenant_data(
        self,
        tenant_id: str,
        key: str,
        value: Any,
    ):
        """Store tenant-isolated data.

        Args:
            tenant_id: Tenant ID
            key: Data key
            value: Data value
        """
        if tenant_id not in self.tenant_data:
            self.tenant_data[tenant_id] = {}

        self.tenant_data[tenant_id][key] = value

    async def get_tenant_data(self, tenant_id: str, key: str) -> Optional[Any]:
        """Retrieve tenant-isolated data.

        Args:
            tenant_id: Tenant ID
            key: Data key

        Returns:
            Data value or None
        """
        return self.tenant_data.get(tenant_id, {}).get(key)

    async def list_tenant_data(self, tenant_id: str) -> Dict[str, Any]:
        """List all data for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant data dictionary
        """
        return self.tenant_data.get(tenant_id, {})

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics.

        Returns:
            Registry statistics
        """
        tiers = {}
        for tenant in self.tenants.values():
            tier_name = tenant.tier.value
            tiers[tier_name] = tiers.get(tier_name, 0) + 1

        total_usage = sum(u.api_calls_used for u in self.usage.values())

        return {
            "total_tenants": len(self.tenants),
            "active_tenants": sum(1 for t in self.tenants.values() if t.is_active),
            "by_tier": tiers,
            "total_api_calls": total_usage,
            "storage_used_gb": sum(u.storage_used_gb for u in self.usage.values()),
            "active_contexts": len([c for c in self.contexts if c.created_at > datetime.now() - __import__("datetime").timedelta(hours=1)]),
        }

    def _generate_tenant_id(self, name: str) -> str:
        """Generate unique tenant ID."""
        hash_obj = hashlib.sha256(f"{name}_{datetime.now().timestamp()}".encode())
        return f"tenant_{hash_obj.hexdigest()[:12]}"

    def _get_tier_features(self, tier: TenantTier) -> Dict[str, bool]:
        """Get feature flags for tier."""
        features = {
            TenantTier.FREE: {
                "api_access": True,
                "analytics": False,
                "multi_user": False,
                "sso": False,
                "advanced_alerts": False,
            },
            TenantTier.STARTER: {
                "api_access": True,
                "analytics": True,
                "multi_user": True,
                "sso": False,
                "advanced_alerts": False,
            },
            TenantTier.PROFESSIONAL: {
                "api_access": True,
                "analytics": True,
                "multi_user": True,
                "sso": True,
                "advanced_alerts": True,
            },
            TenantTier.ENTERPRISE: {
                "api_access": True,
                "analytics": True,
                "multi_user": True,
                "sso": True,
                "advanced_alerts": True,
            },
        }

        return features.get(tier, features[TenantTier.STARTER])
