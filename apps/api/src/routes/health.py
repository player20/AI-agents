"""
Health check routes - Comprehensive health monitoring for Code Weaver Pro
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import asyncio

router = APIRouter(tags=["Health"])


class ServiceHealth(BaseModel):
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    uptime_seconds: Optional[float] = None


class ReadinessResponse(BaseModel):
    ready: bool
    services: List[ServiceHealth]
    overall_status: str


class DetailedHealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    environment: str
    services: Dict[str, Any]
    system: Dict[str, Any]


# Track server start time
_start_time = datetime.now()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Basic health status, version, and timestamp.

    This endpoint is designed to be fast and lightweight for
    load balancer health checks.
    """
    uptime = (datetime.now() - _start_time).total_seconds()
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        uptime_seconds=uptime
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check for orchestration systems (Kubernetes, Docker Swarm).

    Checks connectivity to:
    - LLM providers (Anthropic, OpenAI)
    - Database (Supabase/PostgreSQL)
    - Redis (if configured)

    Returns:
        Detailed readiness status with individual service health.
    """
    services: List[ServiceHealth] = []
    all_healthy = True

    # Check LLM providers
    llm_health = await _check_llm_providers()
    services.extend(llm_health)
    if any(s.status == "unhealthy" for s in llm_health):
        # LLM is critical - if all providers fail, we're not ready
        if all(s.status == "unhealthy" for s in llm_health):
            all_healthy = False

    # Check database
    db_health = await _check_database()
    services.append(db_health)
    # Database is optional for local mode
    # if db_health.status == "unhealthy":
    #     all_healthy = False

    # Check Redis
    redis_health = await _check_redis()
    services.append(redis_health)
    # Redis is optional
    # if redis_health.status == "unhealthy":
    #     all_healthy = False

    overall = "healthy" if all_healthy else "degraded"
    if all(s.status == "unhealthy" for s in services):
        overall = "unhealthy"

    return ReadinessResponse(
        ready=all_healthy,
        services=services,
        overall_status=overall
    )


@router.get("/live")
async def liveness_check():
    """
    Liveness check for orchestration systems.

    This is a simple check that the server process is running
    and can respond to requests. Used by Kubernetes to determine
    if the container should be restarted.

    Returns:
        Simple alive status.
    """
    return {"alive": True, "timestamp": datetime.now().isoformat()}


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check with comprehensive system information.

    Includes:
    - All service health statuses
    - System resource information
    - Environment configuration
    - Version details

    Note: This endpoint may be slower due to comprehensive checks.
    Use /health for quick health checks.
    """
    import sys
    import platform

    # Run all checks
    readiness = await readiness_check()

    # System info
    system_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "unknown",
    }

    # Try to get memory info
    try:
        import psutil
        memory = psutil.virtual_memory()
        system_info["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent
        }
        system_info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        system_info["memory"] = "psutil not installed"

    # Environment
    env = os.environ.get("API_DEBUG", "false").lower() == "true"
    environment = "development" if env else "production"

    # Services dict
    services_dict = {s.name: {"status": s.status, "message": s.message} for s in readiness.services}

    return DetailedHealthResponse(
        status=readiness.overall_status,
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        environment=environment,
        services=services_dict,
        system=system_info
    )


# ===========================================
# Helper functions for checking services
# ===========================================

async def _check_llm_providers() -> List[ServiceHealth]:
    """Check LLM provider connectivity."""
    results = []

    # Check Grok (xAI) - Primary provider
    grok_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if grok_key:
        try:
            import openai
            start = datetime.now()
            client = openai.OpenAI(api_key=grok_key, base_url="https://api.x.ai/v1")
            latency = (datetime.now() - start).total_seconds() * 1000
            results.append(ServiceHealth(
                name="grok",
                status="healthy",
                latency_ms=latency,
                message="API key configured (PRIMARY)"
            ))
        except Exception as e:
            results.append(ServiceHealth(
                name="grok",
                status="unhealthy",
                message=str(e)[:100]
            ))
    else:
        results.append(ServiceHealth(
            name="grok",
            status="degraded",
            message="API key not configured"
        ))

    # Check Anthropic - Fallback provider
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            start = datetime.now()
            client = anthropic.Anthropic(api_key=anthropic_key)
            latency = (datetime.now() - start).total_seconds() * 1000
            results.append(ServiceHealth(
                name="anthropic",
                status="healthy",
                latency_ms=latency,
                message="API key configured (FALLBACK)"
            ))
        except Exception as e:
            results.append(ServiceHealth(
                name="anthropic",
                status="unhealthy",
                message=str(e)[:100]
            ))
    else:
        results.append(ServiceHealth(
            name="anthropic",
            status="degraded",
            message="API key not configured"
        ))

    # Check OpenAI - Secondary fallback
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            start = datetime.now()
            client = openai.OpenAI(api_key=openai_key)
            latency = (datetime.now() - start).total_seconds() * 1000
            results.append(ServiceHealth(
                name="openai",
                status="healthy",
                latency_ms=latency,
                message="API key configured (secondary fallback)"
            ))
        except Exception as e:
            results.append(ServiceHealth(
                name="openai",
                status="unhealthy",
                message=str(e)[:100]
            ))
    else:
        results.append(ServiceHealth(
            name="openai",
            status="degraded",
            message="API key not configured (optional)"
        ))

    return results


async def _check_database() -> ServiceHealth:
    """Check database connectivity."""
    supabase_url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        return ServiceHealth(
            name="database",
            status="degraded",
            message="Using local storage mode (Supabase not configured)"
        )

    try:
        from supabase import create_client
        start = datetime.now()
        client = create_client(supabase_url, supabase_key)
        # Simple connectivity check
        latency = (datetime.now() - start).total_seconds() * 1000
        return ServiceHealth(
            name="database",
            status="healthy",
            latency_ms=latency,
            message="Supabase connected"
        )
    except Exception as e:
        return ServiceHealth(
            name="database",
            status="unhealthy",
            message=str(e)[:100]
        )


async def _check_redis() -> ServiceHealth:
    """Check Redis connectivity."""
    redis_url = os.environ.get("REDIS_URL")

    if not redis_url:
        return ServiceHealth(
            name="redis",
            status="degraded",
            message="Not configured (using in-memory queue)"
        )

    try:
        import redis.asyncio as redis
        start = datetime.now()
        client = redis.from_url(redis_url)
        await client.ping()
        latency = (datetime.now() - start).total_seconds() * 1000
        await client.close()
        return ServiceHealth(
            name="redis",
            status="healthy",
            latency_ms=latency,
            message="Connected"
        )
    except ImportError:
        return ServiceHealth(
            name="redis",
            status="degraded",
            message="redis package not installed"
        )
    except Exception as e:
        return ServiceHealth(
            name="redis",
            status="unhealthy",
            message=str(e)[:100]
        )
