"""FastAPI middleware for security and rate limiting"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware

    Limits requests per IP address to prevent brute force attacks
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host

        # Track requests per IP
        now = datetime.utcnow()
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []

        # Remove old requests (older than 1 minute)
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if now - req_time < timedelta(minutes=1)
        ]

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add current request
        self.request_counts[client_ip].append(now)

        # Process request
        response = await call_next(request)
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Strict rate limiting for auth endpoints

    Limits to 5 login attempts per minute to prevent brute force
    """

    def __init__(self, app, max_attempts: int = 5):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.attempts: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        # Only apply to auth endpoints
        if not request.url.path.startswith("/api/auth/"):
            return await call_next(request)

        # Only limit POST requests (login, register)
        if request.method != "POST":
            return await call_next(request)

        client_ip = request.client.host
        now = datetime.utcnow()

        # Track attempts per IP
        if client_ip not in self.attempts:
            self.attempts[client_ip] = []

        # Remove old attempts (older than 1 minute)
        self.attempts[client_ip] = [
            attempt_time for attempt_time in self.attempts[client_ip]
            if now - attempt_time < timedelta(minutes=1)
        ]

        # Check if exceeded limit
        if len(self.attempts[client_ip]) >= self.max_attempts:
            logger.warning(f"Auth rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many authentication attempts. Please try again in 1 minute.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )

        # Add current attempt
        self.attempts[client_ip].append(now)

        # Process request
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        return response
