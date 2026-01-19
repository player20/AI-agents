"""
Code Weaver Pro API

Enhanced FastAPI backend with WebSocket support for real-time updates.
"""
# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys

from .config import settings
from .routes import (
    projects_router,
    generation_router,
    health_router,
    research_router,
    pipeline_router,
    design_router,
    audit_router,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown"""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # TODO: Initialize database connection
    # TODO: Initialize LLM clients

    yield

    # Shutdown
    logger.info("Shutting down...")
    # TODO: Clean up connections


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    Code Weaver Pro API - AI-powered autonomous application development.

    ## Features

    - **Code Generation**: Generate production-ready apps from natural language
    - **Real-time Updates**: WebSocket support for live progress updates
    - **Multi-platform**: Support for Web, iOS, and Android
    - **52 AI Agents**: Specialized agents for every aspect of development

    ## Getting Started

    1. Create a project with POST /api/projects
    2. Generate code with POST /api/generate or WebSocket /api/generate/ws/{project_id}
    3. Monitor progress through real-time events
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Configure Rate Limiting
from .middleware.rate_limit import add_rate_limiting, RateLimitConfig

add_rate_limiting(app, limits={
    "/api/generate": RateLimitConfig(requests=10, window=60, burst=2),
    "/api/pipeline": RateLimitConfig(requests=5, window=60, burst=1),
    "/api/research": RateLimitConfig(requests=15, window=60, burst=3),
    "/api/design": RateLimitConfig(requests=20, window=60, burst=5),
    "/api/audit": RateLimitConfig(requests=10, window=60, burst=2),
    "/api/projects": RateLimitConfig(requests=60, window=60, burst=10),
    "/api/health": RateLimitConfig(requests=120, window=60, burst=20),
    "default": RateLimitConfig(requests=100, window=60, burst=15),
})

# Register routers
app.include_router(health_router, prefix="/api/health")
app.include_router(projects_router, prefix="/api")
app.include_router(generation_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(design_router, prefix="/api")
app.include_router(audit_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "websocket": "/api/generate/ws/{project_id}",
    }


@app.get("/api")
async def api_root():
    """API root with endpoint listing"""
    return {
        "endpoints": {
            "health": "/api/health",
            "projects": "/api/projects",
            "generate": "/api/generate",
            "generate_ws": "/api/generate/ws/{project_id}",
            "agents": "/api/generate/agents",
            "research": "/api/research",
            "pipeline": "/api/pipeline",
            "design": "/api/design",
            "audit": "/api/audit",
            "audit_code": "/api/audit/code",
        },
        "version": "2.0.0",
        "features": {
            "research": "Market analysis, competitor research, GTM strategy",
            "pipeline": "Full Research → Design → Build workflow",
            "design": "AI-powered design system generation",
            "audit": "Website and GitHub repository code auditing",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
