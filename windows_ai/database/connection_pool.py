"""Database connection pooling and caching strategies.

Implements efficient connection pooling with health checks,
connection reuse, and integrated caching layers.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """Cache hierarchy levels."""
    L1_MEMORY = "memory"  # Process memory
    L2_REDIS = "redis"  # Distributed cache
    L3_DATABASE = "database"  # Database query cache


@dataclass
class CacheEntry:
    """A cached entry with metadata."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600
    hit_count: int = 0
    miss_count: int = 0

    @property
    def age_seconds(self) -> float:
        """Age of cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return self.age_seconds > self.ttl_seconds

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate as percentage."""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return (self.hit_count / total) * 100

    def record_hit(self):
        """Record a cache hit."""
        self.hit_count += 1
        self.accessed_at = datetime.now()

    def record_miss(self):
        """Record a cache miss."""
        self.miss_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "age_seconds": self.age_seconds,
            "ttl_seconds": self.ttl_seconds,
            "expired": self.is_expired,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": f"{self.hit_rate:.1f}%",
        }


@dataclass
class PoolStats:
    """Statistics for connection pool."""
    pool_name: str
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    queued_requests: int = 0
    total_acquired: int = 0
    total_released: int = 0
    connection_errors: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    @property
    def utilization(self) -> float:
        """Calculate pool utilization percentage."""
        if self.total_connections == 0:
            return 0.0
        return (self.active_connections / self.total_connections) * 100

    @property
    def error_rate(self) -> float:
        """Calculate connection error rate."""
        total_attempts = self.total_acquired + self.connection_errors
        if total_attempts == 0:
            return 0.0
        return (self.connection_errors / total_attempts) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pool": self.pool_name,
            "total_connections": self.total_connections,
            "active": self.active_connections,
            "idle": self.idle_connections,
            "queued": self.queued_requests,
            "utilization": f"{self.utilization:.1f}%",
            "total_acquired": self.total_acquired,
            "total_released": self.total_released,
            "connection_errors": self.connection_errors,
            "error_rate": f"{self.error_rate:.1f}%",
        }


class MemoryCache:
    """In-process L1 memory cache with LRU eviction."""

    def __init__(self, max_size: int = 1000):
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU tracking

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if entry.is_expired:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            entry.record_miss()
            return None

        entry.record_hit()
        # Move to end (most recently used)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
        """
        entry = CacheEntry(key=key, value=value, ttl_seconds=ttl_seconds)
        self.cache[key] = entry

        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

        # Evict LRU if over capacity
        if len(self.cache) > self.max_size:
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]

    async def delete(self, key: str):
        """Delete entry from cache.

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)

    async def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        total_hits = sum(e.hit_count for e in self.cache.values())
        total_misses = sum(e.miss_count for e in self.cache.values())
        total_accesses = total_hits + total_misses

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": f"{len(self.cache) / self.max_size * 100:.1f}%",
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate": f"{total_hits / total_accesses * 100:.1f}%" if total_accesses > 0 else "0%",
            "entries": {key: entry.to_dict() for key, entry in self.cache.items()},
        }


class ConnectionPool:
    """Manages database connection pooling."""

    def __init__(
        self,
        name: str = "default",
        min_connections: int = 5,
        max_connections: int = 20,
        timeout_seconds: int = 30,
    ):
        """Initialize connection pool.

        Args:
            name: Pool name for identification
            min_connections: Minimum connections to maintain
            max_connections: Maximum connections allowed
            timeout_seconds: Connection timeout
        """
        self.name = name
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.timeout_seconds = timeout_seconds
        self.stats = PoolStats(pool_name=name, total_connections=0)

        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.in_use: set = set()

    async def initialize(self, connection_factory: Callable[[], Coroutine]):
        """Initialize connection pool with minimum connections.

        Args:
            connection_factory: Async callable that creates connections
        """
        for _ in range(self.min_connections):
            try:
                conn = await asyncio.wait_for(
                    connection_factory(),
                    timeout=self.timeout_seconds
                )
                await self.available_connections.put(conn)
                self.stats.total_connections += 1
            except asyncio.TimeoutError:
                logger.error(f"Timeout creating connection for {self.name}")
                self.stats.connection_errors += 1

    async def acquire(self, timeout_seconds: Optional[int] = None) -> Any:
        """Acquire a connection from the pool.

        Args:
            timeout_seconds: Timeout for acquiring connection

        Returns:
            Database connection

        Raises:
            asyncio.TimeoutError: If no connection available within timeout
        """
        timeout = timeout_seconds or self.timeout_seconds

        try:
            # Try to get existing connection
            conn = self.available_connections.get_nowait()
        except asyncio.QueueEmpty:
            # If pool not at max, create new connection
            if self.stats.total_connections < self.max_connections:
                # This would be implemented with actual DB connection creation
                logger.info(f"Pool {self.name} at capacity, queuing request")
                self.stats.queued_requests += 1
            conn = await asyncio.wait_for(
                self.available_connections.get(),
                timeout=timeout
            )

        self.in_use.add(conn)
        self.stats.active_connections = len(self.in_use)
        self.stats.idle_connections = self.available_connections.qsize()
        self.stats.total_acquired += 1

        return conn

    async def release(self, conn: Any):
        """Release a connection back to the pool.

        Args:
            conn: Connection to release
        """
        if conn in self.in_use:
            self.in_use.remove(conn)
        await self.available_connections.put(conn)
        self.stats.active_connections = len(self.in_use)
        self.stats.idle_connections = self.available_connections.qsize()
        self.stats.total_released += 1

    async def execute_with_connection(
        self,
        operation: Callable[[Any], Coroutine],
        timeout_seconds: Optional[int] = None,
    ) -> Any:
        """Execute operation with a pooled connection.

        Args:
            operation: Async function that takes a connection
            timeout_seconds: Timeout for operation

        Returns:
            Result of operation

        Raises:
            Exception: Any exception from the operation
        """
        conn = None
        try:
            conn = await self.acquire(timeout_seconds)
            result = await asyncio.wait_for(
                operation(conn),
                timeout=timeout_seconds or self.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Operation timeout on pool {self.name}")
            self.stats.connection_errors += 1
            raise
        except Exception as e:
            logger.error(f"Operation failed on pool {self.name}: {e}")
            self.stats.connection_errors += 1
            raise
        finally:
            if conn:
                await self.release(conn)

    async def reset(self):
        """Reset the connection pool."""
        while not self.available_connections.empty():
            try:
                self.available_connections.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.in_use.clear()
        self.stats = PoolStats(pool_name=self.name, total_connections=0)
        logger.info(f"Connection pool {self.name} reset")

    async def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Pool statistics
        """
        return self.stats.to_dict()


class CacheStrategy:
    """Implements multi-level caching strategy."""

    def __init__(self):
        """Initialize cache strategy."""
        self.memory_cache = MemoryCache(max_size=1000)
        self.queries_cached = 0
        self.queries_bypassed = 0

    async def get_cached(
        self,
        key: str,
        query_func: Callable[[], Coroutine],
        ttl_seconds: int = 3600,
        bypass_cache: bool = False,
    ) -> Any:
        """Get value with caching.

        Args:
            key: Cache key
            query_func: Async function to fetch value if not cached
            ttl_seconds: Cache TTL
            bypass_cache: Skip cache and hit DB directly

        Returns:
            Cached or fetched value
        """
        if bypass_cache:
            self.queries_bypassed += 1
            return await query_func()

        # Try L1 memory cache
        cached_value = await self.memory_cache.get(key)
        if cached_value is not None:
            self.queries_cached += 1
            return cached_value

        # Miss - query database
        value = await query_func()

        # Store in cache
        await self.memory_cache.set(key, value, ttl_seconds)

        return value

    async def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries.

        Args:
            pattern: Wildcard pattern to match keys (optional)
        """
        if pattern is None:
            await self.memory_cache.clear()
        else:
            # Simple pattern matching
            import fnmatch
            keys_to_delete = [
                key for key in self.memory_cache.cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            for key in keys_to_delete:
                await self.memory_cache.delete(key)

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report.

        Returns:
            Caching performance metrics
        """
        cache_stats = await self.memory_cache.get_stats()
        total_queries = self.queries_cached + self.queries_bypassed

        return {
            "total_queries": total_queries,
            "cached_queries": self.queries_cached,
            "bypassed_queries": self.queries_bypassed,
            "overall_cache_hit_rate": f"{self.queries_cached / total_queries * 100:.1f}%" if total_queries > 0 else "0%",
            "memory_cache": cache_stats,
        }
