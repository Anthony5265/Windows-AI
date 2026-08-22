"""Rate limiting primitives for API endpoints."""

import hashlib
import logging
import time
from collections import defaultdict
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe-enough in-process sliding-window limiter with burst tokens."""

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000, burst_size: int = 10):
        if requests_per_minute <= 0 or requests_per_hour <= 0 or burst_size <= 0:
            raise ValueError("rate limits and burst_size must be positive")
        if requests_per_minute > requests_per_hour:
            raise ValueError("requests_per_minute cannot exceed requests_per_hour")
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self._minute_buckets: Dict[str, list] = defaultdict(list)
        self._hour_buckets: Dict[str, list] = defaultdict(list)
        self._burst_tokens: Dict[str, int] = defaultdict(lambda: burst_size)
        self._last_refill: Dict[str, float] = {}

    def _cleanup_old_requests(self, bucket: list, window_seconds: int):
        cutoff = time.monotonic() - window_seconds
        return [ts for ts in bucket if ts > cutoff]

    def _refill_burst_tokens(self, client_id: str):
        now = time.monotonic()
        last_refill = self._last_refill.get(client_id, now)
        elapsed = now - last_refill
        tokens_to_add = int(elapsed)
        if tokens_to_add > 0:
            self._burst_tokens[client_id] = min(self.burst_size, self._burst_tokens[client_id] + tokens_to_add)
            self._last_refill[client_id] = now

    async def check_rate_limit(self, client_id: str, weight: int = 1) -> tuple[bool, Optional[Dict[str, Any]]]:
        if not client_id:
            raise ValueError("client_id must not be empty")
        if weight <= 0:
            raise ValueError("weight must be positive")
        if weight > self.requests_per_hour:
            return False, {"X-RateLimit-Limit": str(self.requests_per_hour), "X-RateLimit-Remaining": "0", "Retry-After": "3600"}
        now = time.monotonic()
        self._minute_buckets[client_id] = self._cleanup_old_requests(self._minute_buckets[client_id], 60)
        self._hour_buckets[client_id] = self._cleanup_old_requests(self._hour_buckets[client_id], 3600)
        minute_requests = len(self._minute_buckets[client_id])
        hour_requests = len(self._hour_buckets[client_id])
        if hour_requests + weight > self.requests_per_hour:
            retry_after = max(1, int(3600 - (now - self._hour_buckets[client_id][0])) + 1) if self._hour_buckets[client_id] else 3600
            return False, {"X-RateLimit-Limit": str(self.requests_per_hour), "X-RateLimit-Remaining": "0", "Retry-After": str(retry_after)}
        if minute_requests + weight > self.requests_per_minute:
            self._refill_burst_tokens(client_id)
            if self._burst_tokens[client_id] < weight:
                retry_after = max(1, int(60 - (now - self._minute_buckets[client_id][0])) + 1) if self._minute_buckets[client_id] else 60
                return False, {"X-RateLimit-Limit": str(self.requests_per_minute), "X-RateLimit-Remaining": "0", "Retry-After": str(retry_after)}
            self._burst_tokens[client_id] -= weight
        for _ in range(weight):
            self._minute_buckets[client_id].append(now)
            self._hour_buckets[client_id].append(now)
        remaining = min(self.requests_per_minute - len(self._minute_buckets[client_id]), self.requests_per_hour - len(self._hour_buckets[client_id]))
        return True, {"X-RateLimit-Limit": str(self.requests_per_minute), "X-RateLimit-Remaining": str(max(0, remaining)), "X-RateLimit-Reset": str(int(time.time() + 60))}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000, burst_size: int = 10, exempt_paths: Optional[list] = None, get_client_id: Optional[Callable] = None):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute, requests_per_hour, burst_size)
        self.exempt_paths = exempt_paths or ["/docs", "/redoc", "/openapi.json", "/health"]
        self.get_client_id = get_client_id or self._default_get_client_id

    def _default_get_client_id(self, request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return "key:" + hashlib.sha256(api_key.encode()).hexdigest()
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return "bearer:" + hashlib.sha256(auth[7:].encode()).hexdigest()
        forwarded = request.headers.get("X-Forwarded-For", "")
        client = forwarded.split(",", 1)[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        return "ip:" + client

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        allowed, headers = await self.rate_limiter.check_rate_limit(self.get_client_id(request))
        if not allowed:
            logger.warning("Rate limit exceeded")
            return Response(content='{"error":"Rate limit exceeded"}', status_code=HTTP_429_TOO_MANY_REQUESTS, headers=headers, media_type="application/json")
        response = await call_next(request)
        for key, value in (headers or {}).items():
            response.headers[key] = value
        return response


class EndpointRateLimiter:
    """Dependency/decorator helper for endpoint-specific limits."""

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.limiter = RateLimiter(requests_per_minute=requests_per_minute, requests_per_hour=requests_per_hour)

    async def __call__(self, request: Request):
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            client_id = "key:" + hashlib.sha256(api_key.encode()).hexdigest()
        else:
            client_id = f"ip:{request.client.host if request.client else 'unknown'}"
        allowed, headers = await self.limiter.check_rate_limit(client_id)
        if not allowed:
            raise HTTPException(status_code=HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded", headers=headers)
        return headers


standard_rate_limiter = EndpointRateLimiter(60, 1000)
strict_rate_limiter = EndpointRateLimiter(10, 100)
generous_rate_limiter = EndpointRateLimiter(300, 10000)
