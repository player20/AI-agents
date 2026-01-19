"""
API Routes for Code Weaver Pro
"""
from .projects import router as projects_router
from .generation import router as generation_router
from .health import router as health_router
from .research import router as research_router
from .pipeline import router as pipeline_router
from .design import router as design_router
from .audit import router as audit_router

__all__ = [
    "projects_router",
    "generation_router",
    "health_router",
    "research_router",
    "pipeline_router",
    "design_router",
    "audit_router",
]
