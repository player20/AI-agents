"""
Research & Market Analysis Models

Pydantic models for structured research outputs including:
- Market Research (TAM/SAM/SOM)
- Competitor Analysis
- Feature Recommendations
- Go-To-Market Strategy
- SWOT Analysis
- Complete Research Report
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime


# ===========================================
# Enums
# ===========================================

class MarketSegment(str, Enum):
    """Target market segments"""
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    ENTERPRISE = "enterprise"
    SMB = "smb"
    CONSUMER = "consumer"


class CompetitorTier(str, Enum):
    """Competitor positioning tiers"""
    DIRECT = "direct"
    INDIRECT = "indirect"
    EMERGING = "emerging"
    MARKET_LEADER = "market_leader"


class FeaturePriority(str, Enum):
    """Feature priority levels"""
    MVP = "mvp"
    NICE_TO_HAVE = "nice_to_have"
    FUTURE = "future"


class PricingModel(str, Enum):
    """Common pricing models"""
    FREEMIUM = "freemium"
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    USAGE_BASED = "usage_based"
    TIERED = "tiered"
    FREE = "free"


class Channel(str, Enum):
    """Marketing/distribution channels"""
    SOCIAL_MEDIA = "social_media"
    CONTENT_MARKETING = "content_marketing"
    PAID_ADS = "paid_ads"
    SEO = "seo"
    EMAIL = "email"
    PARTNERSHIPS = "partnerships"
    EVENTS = "events"
    REFERRAL = "referral"
    DIRECT_SALES = "direct_sales"
    APP_STORES = "app_stores"


# ===========================================
# Market Research Models
# ===========================================

class MarketSize(BaseModel):
    """Market size with methodology"""
    value: float = Field(description="Market size in USD (billions)")
    year: int = Field(description="Year of estimate")
    growth_rate: float = Field(description="Annual growth rate percentage")
    source: Optional[str] = Field(default=None, description="Data source or methodology")


class MarketResearch(BaseModel):
    """Comprehensive market research data"""
    tam: MarketSize = Field(description="Total Addressable Market")
    sam: MarketSize = Field(description="Serviceable Addressable Market")
    som: MarketSize = Field(description="Serviceable Obtainable Market")

    methodology: str = Field(description="How market sizes were calculated")
    key_trends: List[str] = Field(description="Major trends affecting the market")
    market_drivers: List[str] = Field(description="Factors driving market growth")
    market_barriers: List[str] = Field(description="Challenges and barriers to entry")

    target_demographics: List[str] = Field(description="Primary target demographics")
    geographic_focus: List[str] = Field(description="Target geographic regions")

    industry_vertical: str = Field(description="Primary industry vertical")
    market_maturity: str = Field(description="'emerging', 'growing', 'mature', 'declining'")


# ===========================================
# Competitor Analysis Models
# ===========================================

class CompetitorFeature(BaseModel):
    """A feature offered by a competitor"""
    name: str
    has_feature: bool
    quality: Optional[str] = Field(default=None, description="'basic', 'good', 'excellent'")
    notes: Optional[str] = None


class Competitor(BaseModel):
    """Detailed competitor profile"""
    name: str
    website: Optional[str] = None
    description: str
    tier: CompetitorTier

    # Market position
    market_share: Optional[float] = Field(default=None, description="Estimated market share %")
    founded_year: Optional[int] = None
    funding: Optional[str] = Field(default=None, description="Total funding raised")
    employee_count: Optional[str] = Field(default=None, description="Approximate employee count range")

    # Positioning
    price_position: float = Field(ge=0, le=10, description="Price positioning 0(cheap)-10(premium)")
    feature_position: float = Field(ge=0, le=10, description="Feature richness 0(basic)-10(full)")

    # Strengths and weaknesses
    strengths: List[str]
    weaknesses: List[str]

    # Features
    key_features: List[CompetitorFeature] = Field(default_factory=list)

    # Pricing
    pricing_model: PricingModel
    price_range: Optional[str] = Field(default=None, description="e.g., '$10-50/month'")


class CompetitorAnalysis(BaseModel):
    """Complete competitor analysis"""
    competitors: List[Competitor] = Field(description="List of analyzed competitors")

    # Positioning matrix data (for visualization)
    positioning: Dict[str, Tuple[float, float]] = Field(
        default_factory=dict,
        description="Competitor name -> (price_position, feature_position)"
    )

    # Insights
    market_gaps: List[str] = Field(description="Unserved needs in the market")
    differentiation_opportunities: List[str] = Field(description="Ways to stand out")
    competitive_threats: List[str] = Field(description="Key competitive risks")

    # Feature comparison
    feature_comparison_matrix: Dict[str, Dict[str, bool]] = Field(
        default_factory=dict,
        description="Feature name -> {competitor: has_feature}"
    )


# ===========================================
# Feature Recommendations Models
# ===========================================

class Feature(BaseModel):
    """A recommended product feature"""
    name: str
    description: str
    priority: FeaturePriority

    # Effort and impact
    effort: str = Field(description="'low', 'medium', 'high'")
    impact: str = Field(description="'low', 'medium', 'high'")

    # Details
    user_story: Optional[str] = Field(default=None, description="As a... I want... So that...")
    acceptance_criteria: List[str] = Field(default_factory=list)

    # Justification
    rationale: str = Field(description="Why this feature is recommended")
    competitor_parity: bool = Field(default=False, description="Is this table stakes?")


class FeatureRecommendations(BaseModel):
    """Prioritized feature recommendations"""
    mvp_features: List[Feature] = Field(description="Must-have features for launch")
    nice_to_have: List[Feature] = Field(description="Important but not critical")
    future_roadmap: List[Feature] = Field(description="Future phase features")

    # Summary
    mvp_summary: str = Field(description="Overview of MVP scope")
    total_features: int = Field(description="Total number of features recommended")

    # Prioritization methodology
    prioritization_criteria: List[str] = Field(description="How features were prioritized")


# ===========================================
# Go-To-Market Strategy Models
# ===========================================

class Milestone(BaseModel):
    """A GTM milestone"""
    name: str
    description: str
    phase: str = Field(description="'pre-launch', 'launch', 'growth', 'scale'")
    success_metrics: List[str] = Field(description="How to measure success")
    dependencies: List[str] = Field(default_factory=list)


class TargetPersona(BaseModel):
    """A target customer persona"""
    name: str = Field(description="Persona name (e.g., 'Tech-Savvy Sarah')")
    role: str = Field(description="Job title or role")
    demographics: str = Field(description="Age, location, etc.")

    pain_points: List[str]
    goals: List[str]
    objections: List[str] = Field(description="Common objections to purchase")

    channels: List[Channel] = Field(description="Where to reach this persona")
    messaging: str = Field(description="Key value proposition for this persona")


class GTMStrategy(BaseModel):
    """Go-to-market strategy"""
    # Target audience
    target_segments: List[MarketSegment]
    target_personas: List[TargetPersona]

    # Value proposition
    value_proposition: str = Field(description="Core value proposition statement")
    positioning_statement: str = Field(description="Market positioning statement")
    key_messages: List[str] = Field(description="Top 3-5 marketing messages")

    # Channels
    primary_channels: List[Channel]
    secondary_channels: List[Channel]
    channel_strategy: Dict[str, str] = Field(
        default_factory=dict,
        description="Channel -> strategy description"
    )

    # Pricing
    pricing_strategy: PricingModel
    pricing_rationale: str
    price_points: Dict[str, str] = Field(
        default_factory=dict,
        description="Tier name -> price"
    )

    # Launch
    launch_timeline: List[Milestone]
    launch_strategy: str = Field(description="Overall launch approach")

    # Metrics
    key_metrics: List[str] = Field(description="KPIs to track")
    success_criteria: Dict[str, str] = Field(
        default_factory=dict,
        description="Metric -> target value"
    )


# ===========================================
# SWOT Analysis Models
# ===========================================

class SWOTItem(BaseModel):
    """A single SWOT item with details"""
    item: str = Field(description="The strength/weakness/opportunity/threat")
    impact: str = Field(description="'high', 'medium', 'low'")
    description: Optional[str] = None
    mitigation: Optional[str] = Field(default=None, description="For weaknesses/threats: how to address")
    leverage: Optional[str] = Field(default=None, description="For strengths/opportunities: how to capitalize")


class SWOTAnalysis(BaseModel):
    """Complete SWOT analysis"""
    strengths: List[SWOTItem]
    weaknesses: List[SWOTItem]
    opportunities: List[SWOTItem]
    threats: List[SWOTItem]

    # Strategic implications
    key_insights: List[str] = Field(description="Top strategic takeaways")
    recommended_actions: List[str] = Field(description="Prioritized action items")


# ===========================================
# Complete Research Report
# ===========================================

class ResearchReport(BaseModel):
    """Complete research report combining all analyses"""
    # Metadata
    id: Optional[str] = None
    project_id: Optional[str] = None
    business_idea: str = Field(description="Original business idea input")
    created_at: datetime = Field(default_factory=datetime.now)

    # Executive summary
    executive_summary: str = Field(description="High-level summary of findings")
    key_findings: List[str] = Field(description="Top 5-7 key findings")
    recommendations: List[str] = Field(description="Top recommendations")

    # Detailed analyses
    market: MarketResearch
    competitors: CompetitorAnalysis
    features: FeatureRecommendations
    gtm: GTMStrategy
    swot: SWOTAnalysis

    # Additional insights
    differentiation_strategy: str = Field(description="How to differentiate in the market")
    risk_factors: List[str] = Field(description="Key risks to consider")
    next_steps: List[str] = Field(description="Recommended immediate actions")

    # Status
    status: str = Field(default="complete", description="'pending', 'in_progress', 'complete', 'error'")


# ===========================================
# Request/Response Models for API
# ===========================================

class ResearchRequest(BaseModel):
    """Request to start research analysis"""
    business_idea: str = Field(..., min_length=10, description="Business idea to research")
    industry: Optional[str] = Field(default=None, description="Optional industry hint")
    target_market: Optional[MarketSegment] = None
    geographic_focus: Optional[List[str]] = None
    include_sections: Optional[List[str]] = Field(
        default=None,
        description="Specific sections to include (default: all)"
    )


class ResearchStatus(BaseModel):
    """Status of a research job"""
    id: str
    status: str = Field(description="'pending', 'researching', 'analyzing', 'complete', 'error'")
    progress: int = Field(ge=0, le=100, description="Completion percentage")
    current_phase: str = Field(description="Current analysis phase")
    estimated_remaining: Optional[str] = None
    error: Optional[str] = None


class ResearchResponse(BaseModel):
    """Response containing research report"""
    id: str
    status: str
    report: Optional[ResearchReport] = None
    html_report: Optional[str] = Field(default=None, description="Rendered HTML report")
    pdf_url: Optional[str] = Field(default=None, description="URL to download PDF")
