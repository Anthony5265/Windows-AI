"""Caching system with multiple backend support (Redis, in-memory)"""

import asyncio
import logging
import json
import pickle
import time
from typing import Any, Optional, Dict, Callable
from datetime import timedelta
from abc import ABC, abstractmethod
from collections import OrderedDict
import hashlib

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract cache backend"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL (seconds)"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass

    @abstractmethod
    async def clear(self):
        """Clear all cache entries"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class InMemoryCache(CacheBackend):
    """
    In-memory LRU cache with TTL support

    Features:
    - LRU eviction policy
    - Per-key TTL
    - Size-based eviction
    - Thread-safe operations
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._ttl: Dict[str, float] = {}
        self._lock = asyncio.Lock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            # Check if key exists and not expired
            if key in self._cache:
                if self._is_expired(key):
                    # Remove expired entry
                    del self._cache[key]
                    del self._ttl[key]
                    self.misses += 1
                    return None

                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self.hits += 1
                return self._cache[key]

            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        async with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            self._cache[key] = value
            self._cache.move_to_end(key)

            # Set TTL
            ttl = ttl or self.default_ttl
            if ttl > 0:
                self._ttl[key] = time.time() + ttl

            # Evict if over size limit
            while len(self._cache) > self.max_size:
                # Remove least recently used
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                if oldest_key in self._ttl:
                    del self._ttl[oldest_key]
                self.evictions += 1

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._ttl:
                    del self._ttl[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self._lock:
            if key in self._cache:
                if self._is_expired(key):
                    del self._cache[key]
                    del self._ttl[key]
                    return False
                return True
            return False

    async def clear(self):
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._ttl.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'backend': 'memory',
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }

    def _is_expired(self, key: str) -> bool:
        """Check if key is expired"""
        if key not in self._ttl:
            return False
        return time.time() > self._ttl[key]


class RedisCache(CacheBackend):
    """
    Redis-backed cache

    Requires redis-py (aioredis) to be installed
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "windows_ai:",
        default_ttl: int = 3600
    ):
        self.redis_url = redis_url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.redis = None

        # Statistics
        self.hits = 0
        self.misses = 0

    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if self.redis is None:
            try:
                import redis.asyncio as aioredis
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=False
                )
                logger.info(f"Connected to Redis: {self.redis_url}")
            except ImportError:
                raise ImportError("redis package required for RedisCache. Install with: pip install redis")

    def _make_key(self, key: str) -> str:
        """Make prefixed key"""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        await self._ensure_connection()

        try:
            value = await self.redis.get(self._make_key(key))
            if value is not None:
                self.hits += 1
                return pickle.loads(value)
            self.misses += 1
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis"""
        await self._ensure_connection()

        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            await self.redis.setex(
                self._make_key(key),
                ttl,
                serialized
            )
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value from Redis"""
        await self._ensure_connection()

        try:
            result = await self.redis.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        await self._ensure_connection()

        try:
            return await self.redis.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def clear(self):
        """Clear all cache entries with prefix"""
        await self._ensure_connection()

        try:
            # Find all keys with prefix
            pattern = f"{self.prefix}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        try:
            await self._ensure_connection()
            info = await self.redis.info()
            return {
                'backend': 'redis',
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests,
                'redis_used_memory': info.get('used_memory_human'),
                'redis_connected_clients': info.get('connected_clients')
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                'backend': 'redis',
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }


class Cache:
    """
    High-level cache interface with automatic serialization

    Features:
    - Automatic key hashing
    - Namespace support
    - Decorator for caching function results
    - Multiple backend support
    """

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        namespace: str = "default"
    ):
        self.backend = backend or InMemoryCache()
        self.namespace = namespace

    def _make_key(self, key: str) -> str:
        """Make namespaced key"""
        return f"{self.namespace}:{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        value = await self.backend.get(self._make_key(key))
        return value if value is not None else default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        await self.backend.set(self._make_key(key), value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        return await self.backend.delete(self._make_key(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.backend.exists(self._make_key(key))

    async def clear(self):
        """Clear all cache entries"""
        await self.backend.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.backend.get_stats()

    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = ""
    ):
        """
        Decorator to cache function results

        Usage:
            cache = Cache()

            @cache.cached(ttl=300)
            async def expensive_function(x, y):
                return x + y
        """
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_parts = [key_prefix or func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

                # Check cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit: {func.__name__}")
                    return cached_value

                # Execute function
                logger.debug(f"Cache miss: {func.__name__}")
                result = await func(*args, **kwargs)

                # Store in cache
                await self.set(cache_key, result, ttl)

                return result

            return wrapper
        return decorator


# Global cache instances
_global_cache: Optional[Cache] = None


def get_cache(namespace: str = "default") -> Cache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        # Try Redis first, fall back to in-memory
        try:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            backend = RedisCache(redis_url=redis_url)
            logger.info("Using Redis cache backend")
        except Exception as e:
            logger.info(f"Redis not available, using in-memory cache: {e}")
            backend = InMemoryCache()

        _global_cache = Cache(backend=backend, namespace=namespace)

    return _global_cache
