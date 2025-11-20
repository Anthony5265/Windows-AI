"""Middleware for API server"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting (simple implementation)"""

    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        current_time = time.time()
        self.requests = {
            ip: [t for t in times if current_time - t < self.window]
            for ip, times in self.requests.items()
        }

        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.max_requests:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429,
                    headers={"Retry-After": str(self.window)}
                )

        # Add request timestamp
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.max_requests - len(self.requests.get(client_ip, []))
        )

        return response

def setup_cors(app):
    """Setup CORS middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_middleware(app):
    """Setup all middleware"""
    # CORS
    setup_cors(app)

    # Logging
    app.add_middleware(LoggingMiddleware)

    # Rate limiting (disabled by default, enable in production)
    # app.add_middleware(RateLimitMiddleware, max_requests=100, window=60)
