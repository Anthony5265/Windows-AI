"""Rate limiting middleware for API endpoints"""

import time
import logging
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size

        # Storage for rate limit tracking
        self._minute_buckets: Dict[str, list] = defaultdict(list)
        self._hour_buckets: Dict[str, list] = defaultdict(list)
        self._burst_tokens: Dict[str, int] = defaultdict(lambda: burst_size)
        self._last_refill: Dict[str, float] = {}

    def _cleanup_old_requests(self, bucket: list, window_seconds: int):
        """Remove requests older than window"""
        cutoff = time.time() - window_seconds
        return [ts for ts in bucket if ts > cutoff]

    def _refill_burst_tokens(self, client_id: str):
        """Refill burst tokens over time"""
        now = time.time()
        last_refill = self._last_refill.get(client_id, now)
        elapsed = now - last_refill

        # Refill 1 token per second, up to burst_size
        tokens_to_add = int(elapsed)
        if tokens_to_add > 0:
            self._burst_tokens[client_id] = min(
                self.burst_size,
                self._burst_tokens[client_id] + tokens_to_add
            )
            self._last_refill[client_id] = now

    async def check_rate_limit(
        self,
        client_id: str,
        weight: int = 1
    ) -> tuple[bool, Optional[Dict[str, any]]]:
        """
        Check if request is within rate limits

        Args:
            client_id: Unique identifier for the client (IP, API key, user ID)
            weight: Cost of this request (default 1)

        Returns:
            (allowed, headers) tuple where:
                - allowed: Whether request should be allowed
                - headers: Rate limit headers to include in response
        """
        now = time.time()

        # Cleanup old requests
        self._minute_buckets[client_id] = self._cleanup_old_requests(
            self._minute_buckets[client_id], 60
        )
        self._hour_buckets[client_id] = self._cleanup_old_requests(
            self._hour_buckets[client_id], 3600
        )

        # Check minute limit
        minute_requests = len(self._minute_buckets[client_id])
        if minute_requests >= self.requests_per_minute:
            # Try burst tokens
            self._refill_burst_tokens(client_id)
            if self._burst_tokens[client_id] >= weight:
                self._burst_tokens[client_id] -= weight
            else:
                retry_after = 60 - (now - min(self._minute_buckets[client_id]))
                return False, {
                    'X-RateLimit-Limit': str(self.requests_per_minute),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(now + retry_after)),
                    'Retry-After': str(int(retry_after))
                }

        # Check hour limit
        hour_requests = len(self._hour_buckets[client_id])
        if hour_requests >= self.requests_per_hour:
            retry_after = 3600 - (now - min(self._hour_buckets[client_id]))
            return False, {
                'X-RateLimit-Limit': str(self.requests_per_hour),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(int(now + retry_after)),
                'Retry-After': str(int(retry_after))
            }

        # Add request to buckets
        for _ in range(weight):
            self._minute_buckets[client_id].append(now)
            self._hour_buckets[client_id].append(now)

        # Calculate remaining requests
        remaining_minute = self.requests_per_minute - len(self._minute_buckets[client_id])
        remaining_hour = self.requests_per_hour - len(self._hour_buckets[client_id])

        headers = {
            'X-RateLimit-Limit': str(self.requests_per_minute),
            'X-RateLimit-Remaining': str(min(remaining_minute, remaining_hour)),
            'X-RateLimit-Reset': str(int(now + 60)),
        }

        return True, headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        exempt_paths: Optional[list] = None,
        get_client_id: Optional[Callable] = None
    ):
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            burst_size=burst_size
        )
        self.exempt_paths = exempt_paths or ['/docs', '/redoc', '/openapi.json', '/health']
        self.get_client_id = get_client_id or self._default_get_client_id

    def _default_get_client_id(self, request: Request) -> str:
        """Get client ID from request (IP or API key)"""
        # Try to get API key first
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"key:{api_key}"

        # Try Authorization header
        auth = request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            return f"bearer:{auth[7:20]}"  # Use first 20 chars of token

        # Fall back to IP address
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        return f"ip:{request.client.host if request.client else 'unknown'}"

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Get client identifier
        client_id = self.get_client_id(request)

        # Check rate limit
        allowed, headers = await self.rate_limiter.check_rate_limit(client_id)

        if not allowed:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                headers=headers,
                media_type='application/json'
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if headers:
            for key, value in headers.items():
                response.headers[key] = value

        return response


class EndpointRateLimiter:
    """Decorator for rate limiting specific endpoints"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour
        )

    async def __call__(self, request: Request):
        """Check rate limit for endpoint"""
        # Get client ID
        api_key = request.headers.get('X-API-Key', '')
        client_id = f"key:{api_key}" if api_key else f"ip:{request.client.host}"

        # Check rate limit
        allowed, headers = await self.limiter.check_rate_limit(client_id)

        if not allowed:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=headers
            )

        return headers


# Pre-configured rate limiters for different use cases
standard_rate_limiter = EndpointRateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000
)

strict_rate_limiter = EndpointRateLimiter(
    requests_per_minute=10,
    requests_per_hour=100
)

generous_rate_limiter = EndpointRateLimiter(
    requests_per_minute=300,
    requests_per_hour=10000
)
