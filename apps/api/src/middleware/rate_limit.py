"""
Rate Limiting Middleware for Code Weaver Pro API

Implements token bucket algorithm with support for:
- Per-IP rate limiting
- Per-user rate limiting (when authenticated)
- Different limits for different endpoints
- Redis backend for distributed rate limiting
- In-memory fallback for local development
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import time
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit rule"""
    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    burst: int = 0  # Additional burst capacity


# Default rate limits by endpoint pattern
DEFAULT_LIMITS: Dict[str, RateLimitConfig] = {
    # LLM endpoints - most expensive
    "/api/generate": RateLimitConfig(requests=10, window=60, burst=2),
    "/api/chat": RateLimitConfig(requests=20, window=60, burst=5),

    # Project endpoints - moderate
    "/api/projects": RateLimitConfig(requests=60, window=60, burst=10),

    # Health endpoints - generous
    "/api/health": RateLimitConfig(requests=120, window=60, burst=20),

    # Default for unmatched endpoints
    "default": RateLimitConfig(requests=100, window=60, burst=15),
}


class TokenBucket:
    """In-memory token bucket implementation"""

    def __init__(self):
        self._buckets: Dict[str, Tuple[float, float, float]] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        key: str,
        max_tokens: int,
        refill_rate: float,
        burst: int = 0
    ) -> Tuple[bool, int, float]:
        """
        Check if request is allowed and consume a token.

        Returns:
            Tuple of (allowed, remaining_tokens, reset_time)
        """
        async with self._lock:
            now = time.time()
            max_capacity = max_tokens + burst

            if key not in self._buckets:
                # Initialize new bucket
                self._buckets[key] = (max_capacity - 1, now, now + (1 / refill_rate))
                return True, max_capacity - 1, now + (1 / refill_rate)

            tokens, last_update, reset_time = self._buckets[key]

            # Calculate tokens to add based on time elapsed
            elapsed = now - last_update
            tokens_to_add = elapsed * refill_rate
            tokens = min(max_capacity, tokens + tokens_to_add)

            if tokens >= 1:
                # Allow request, consume token
                tokens -= 1
                next_reset = now + ((max_capacity - tokens) / refill_rate)
                self._buckets[key] = (tokens, now, next_reset)
                return True, int(tokens), next_reset
            else:
                # Rate limited
                retry_after = (1 - tokens) / refill_rate
                return False, 0, now + retry_after

    async def cleanup_old_entries(self, max_age: int = 3600):
        """Remove old entries to prevent memory growth"""
        async with self._lock:
            now = time.time()
            keys_to_remove = [
                key for key, (_, last_update, _) in self._buckets.items()
                if now - last_update > max_age
            ]
            for key in keys_to_remove:
                del self._buckets[key]


class RedisTokenBucket:
    """Redis-backed token bucket for distributed rate limiting"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        """Lazy initialization of Redis connection"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = await redis.from_url(self.redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                return None
        return self._redis

    async def is_allowed(
        self,
        key: str,
        max_tokens: int,
        refill_rate: float,
        burst: int = 0
    ) -> Tuple[bool, int, float]:
        """Check if request is allowed using Redis"""
        redis_client = await self._get_redis()
        if redis_client is None:
            # Fallback: allow all if Redis unavailable
            return True, max_tokens, time.time() + 60

        try:
            now = time.time()
            max_capacity = max_tokens + burst
            bucket_key = f"ratelimit:{key}"

            # Lua script for atomic token bucket operation
            lua_script = """
            local key = KEYS[1]
            local max_capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])

            local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
            local tokens = tonumber(bucket[1]) or max_capacity
            local last_update = tonumber(bucket[2]) or now

            -- Calculate tokens to add
            local elapsed = now - last_update
            local tokens_to_add = elapsed * refill_rate
            tokens = math.min(max_capacity, tokens + tokens_to_add)

            if tokens >= 1 then
                tokens = tokens - 1
                redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                redis.call('EXPIRE', key, 3600)
                return {1, math.floor(tokens), now + ((max_capacity - tokens) / refill_rate)}
            else
                local retry_after = (1 - tokens) / refill_rate
                return {0, 0, now + retry_after}
            end
            """

            result = await redis_client.eval(
                lua_script,
                1,
                bucket_key,
                max_capacity,
                refill_rate,
                now
            )

            allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = float(result[2])

            return allowed, remaining, reset_time

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fallback: allow on error
            return True, max_tokens, time.time() + 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(
        self,
        app,
        limits: Optional[Dict[str, RateLimitConfig]] = None,
        redis_url: Optional[str] = None,
        key_func: Optional[Callable[[Request], str]] = None
    ):
        super().__init__(app)
        self.limits = limits or DEFAULT_LIMITS

        # Use Redis if available, otherwise in-memory
        redis_url = redis_url or os.environ.get("REDIS_URL")
        if redis_url:
            self.bucket = RedisTokenBucket(redis_url)
            logger.info("Rate limiting: Using Redis backend")
        else:
            self.bucket = TokenBucket()
            logger.info("Rate limiting: Using in-memory backend")

        # Function to extract rate limit key from request
        self.key_func = key_func or self._default_key_func

    def _default_key_func(self, request: Request) -> str:
        """Default key function: use IP address"""
        # Try to get real IP from headers (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _get_limit_config(self, path: str) -> RateLimitConfig:
        """Get rate limit config for a path"""
        # Check for exact match first
        if path in self.limits:
            return self.limits[path]

        # Check for prefix match
        for pattern, config in self.limits.items():
            if pattern != "default" and path.startswith(pattern):
                return config

        # Return default
        return self.limits.get("default", RateLimitConfig(requests=100, window=60))

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/docs") or \
           request.url.path.startswith("/openapi") or \
           request.url.path == "/":
            return await call_next(request)

        # Get rate limit key and config
        key = self.key_func(request)
        config = self._get_limit_config(request.url.path)

        # Calculate refill rate (tokens per second)
        refill_rate = config.requests / config.window

        # Create a composite key including the path pattern
        path_key = request.url.path.split("/")[2] if len(request.url.path.split("/")) > 2 else "default"
        rate_key = f"{key}:{path_key}"

        # Check rate limit
        allowed, remaining, reset_time = await self.bucket.is_allowed(
            key=rate_key,
            max_tokens=config.requests,
            refill_rate=refill_rate,
            burst=config.burst
        )

        # Add rate limit headers
        response_headers = {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_time)),
            "X-RateLimit-Window": str(config.window),
        }

        if not allowed:
            retry_after = int(reset_time - time.time())
            response_headers["Retry-After"] = str(max(1, retry_after))

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers=response_headers
            )

        # Process request and add headers to response
        response = await call_next(request)

        # Add rate limit headers to successful response
        for header, value in response_headers.items():
            response.headers[header] = value

        return response


# Convenience function to add rate limiting to an app
def add_rate_limiting(
    app,
    limits: Optional[Dict[str, RateLimitConfig]] = None,
    redis_url: Optional[str] = None
):
    """Add rate limiting middleware to a FastAPI app"""
    app.add_middleware(
        RateLimitMiddleware,
        limits=limits,
        redis_url=redis_url
    )
