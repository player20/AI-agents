"""
Pydantic models for Code Weaver Pro API
"""
from .project import (
    Platform,
    ProjectStatus,
    AgentStatus,
    ProjectCreate,
    ProjectResponse,
    AgentExecutionCreate,
    AgentExecutionResponse,
    GenerationRequest,
    GenerationEvent,
)

# Re-export research models for convenience
from ..ai.research_models import (
    MarketResearch,
    MarketSize,
    MarketSegment,
    CompetitorAnalysis,
    Competitor,
    CompetitorTier,
    FeatureRecommendations,
    Feature,
    FeaturePriority,
    GTMStrategy,
    TargetPersona,
    Milestone,
    SWOTAnalysis,
    SWOTItem,
    ResearchReport,
    ResearchRequest,
    ResearchStatus,
    ResearchResponse,
    PricingModel,
    Channel,
)

__all__ = [
    # Project models
    "Platform",
    "ProjectStatus",
    "AgentStatus",
    "ProjectCreate",
    "ProjectResponse",
    "AgentExecutionCreate",
    "AgentExecutionResponse",
    "GenerationRequest",
    "GenerationEvent",

    # Research models
    "MarketResearch",
    "MarketSize",
    "MarketSegment",
    "CompetitorAnalysis",
    "Competitor",
    "CompetitorTier",
    "FeatureRecommendations",
    "Feature",
    "FeaturePriority",
    "GTMStrategy",
    "TargetPersona",
    "Milestone",
    "SWOTAnalysis",
    "SWOTItem",
    "ResearchReport",
    "ResearchRequest",
    "ResearchStatus",
    "ResearchResponse",
    "PricingModel",
    "Channel",
]
