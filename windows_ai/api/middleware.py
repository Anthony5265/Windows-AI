"""Middleware for the Windows AI API server."""

import logging
import os
import time
from collections import defaultdict
from threading import Lock

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log request lifecycle without exposing query-string credentials."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.monotonic()
        logger.info("Request: %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request error: %s %s", request.method, request.url.path)
            raise
        process_time = time.monotonic() - start_time
        logger.info("Response: %s (%.3fs)", response.status_code, process_time)
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-process per-client sliding-window rate limiter."""

    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        if max_requests <= 0 or window <= 0:
            raise ValueError("max_requests and window must be positive")
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.monotonic()
        with self._lock:
            for ip, times in list(self.requests.items()):
                retained = [t for t in times if current_time - t < self.window]
                if retained:
                    self.requests[ip] = retained
                else:
                    self.requests.pop(ip, None)
            timestamps = self.requests[client_ip]
            if len(timestamps) >= self.max_requests:
                retry_after = max(1, int(self.window - (current_time - timestamps[0])) + 1)
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.max_requests),
                        "X-RateLimit-Remaining": "0",
                    },
                )
            timestamps.append(current_time)
            remaining = max(0, self.max_requests - len(timestamps))
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


def setup_cors(app):
    """Configure CORS from an explicit environment allow-list."""
    configured = [
        item.strip()
        for item in os.getenv("WINDOWS_AI_CORS_ORIGINS", "").split(",")
        if item.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_middleware(app):
    """Install the API middleware stack."""
    setup_cors(app)
    app.add_middleware(LoggingMiddleware)
