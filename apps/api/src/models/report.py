"""
Business Report models for Code Weaver Pro

These models define the structure for professional HTML business reports
that accompany generated prototypes.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    """Types of business reports that can be generated"""
    TRANSFORMATION_PROPOSAL = "transformation_proposal"  # For new builds
    UX_AUDIT = "ux_audit"  # For existing site audits
    COMPREHENSIVE = "comprehensive"  # Combines both


class Severity(str, Enum):
    """Severity levels for issues and recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BadgeType(str, Enum):
    """Badge types for metrics and status indicators"""
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"


# ============================================================================
# Report Section Models
# ============================================================================

class MetricItem(BaseModel):
    """A single metric with label, value, and optional badge"""
    label: str
    value: str
    badge: Optional[BadgeType] = None
    badge_text: Optional[str] = None  # Custom badge text


class ExecutiveSummary(BaseModel):
    """Executive summary section of the report"""
    headline: str = Field(..., description="Key insight headline, e.g., 'You have a signup problem, not a supply problem'")
    metrics: List[MetricItem] = Field(default_factory=list, description="Key metrics table")
    bottom_line: str = Field(..., description="The most important takeaway")
    bottom_line_type: Literal["warning", "success", "info"] = "warning"


class IndustryInsight(BaseModel):
    """Industry insights from web research"""
    title: str
    value: str
    source: Optional[str] = None
    trend: Optional[Literal["up", "down", "stable"]] = None


class IndustrySection(BaseModel):
    """Complete industry insights section"""
    market_size: Optional[str] = None
    digital_adoption_rate: Optional[str] = None
    key_trends: List[str] = Field(default_factory=list)
    insights: List[IndustryInsight] = Field(default_factory=list)


class CompetitorFeature(BaseModel):
    """A feature found in competitor analysis"""
    feature: str
    competitors_with_feature: List[str] = Field(default_factory=list)
    importance: Literal["must_have", "nice_to_have", "differentiator"] = "nice_to_have"


class CompetitorAnalysis(BaseModel):
    """Competitor analysis section"""
    competitors: List[Dict[str, Any]] = Field(default_factory=list)  # Name, URL, strengths, weaknesses
    common_features: List[CompetitorFeature] = Field(default_factory=list)
    pricing_benchmarks: Dict[str, str] = Field(default_factory=dict)
    market_gaps: List[str] = Field(default_factory=list)


class DesignSystem(BaseModel):
    """Design system recommendations"""
    primary_color: str = "#3B82F6"
    secondary_color: str = "#10B981"
    accent_color: str = "#F59E0B"
    background_color: str = "#F8FAFC"
    text_color: str = "#1E293B"
    font_family: str = "Inter, system-ui, sans-serif"
    mood_tags: List[str] = Field(default_factory=list)  # e.g., ["Modern", "Clean", "Professional"]


# ============================================================================
# Issue and Recommendation Models
# ============================================================================

class IssueCard(BaseModel):
    """An issue found during audit"""
    id: str
    title: str
    description: str
    severity: Severity
    business_impact: str
    how_to_fix: str
    drop_off_percentage: Optional[float] = None  # e.g., 23.3 for "23.3% drop-off"
    confirmed: bool = False  # Was this confirmed through testing?
    category: Optional[str] = None  # e.g., "Email Verification", "Onboarding"
    affected_page: Optional[str] = None


class Recommendation(BaseModel):
    """A prioritized recommendation"""
    priority: int = Field(..., ge=1, le=10)
    title: str
    subtitle: str = Field(..., description="e.g., 'HIGH - 80% confidence'")
    current_state: Optional[str] = None
    recommended_state: Optional[str] = None
    expected_lift: Optional[str] = None  # e.g., "+60-100 more listings"
    confidence: float = Field(default=0.8, ge=0, le=1)
    changes: List[str] = Field(default_factory=list)  # Bullet points of changes
    stats: Optional[Dict[str, Any]] = None  # e.g., {"current_steps": 9, "recommended_steps": 4}


class RoadmapItem(BaseModel):
    """A single roadmap checklist item"""
    task: str
    completed: bool = False


class RoadmapPhase(BaseModel):
    """A phase in the implementation roadmap"""
    title: str
    color: str = "#3B82F6"  # Border color for the phase
    items: List[RoadmapItem] = Field(default_factory=list)


# ============================================================================
# KPI and ROI Models
# ============================================================================

class KPIRow(BaseModel):
    """A single KPI tracking row"""
    metric: str
    current: str
    target_30_days: str
    target_90_days: str
    current_is_bad: bool = True  # Used for styling


class ROIMetric(BaseModel):
    """A single ROI metric"""
    label: str
    value: str


class ROIProjection(BaseModel):
    """ROI projection scenario"""
    scenario: Literal["conservative", "optimistic"]
    title: str
    metrics: List[ROIMetric] = Field(default_factory=list)


# ============================================================================
# Funnel Analysis Models
# ============================================================================

class FunnelStep(BaseModel):
    """A step in the user funnel"""
    name: str
    count: int
    percentage: float  # Percentage of total or previous step
    drop_off: Optional[float] = None  # Drop-off percentage to next step


class FunnelAnalysis(BaseModel):
    """Complete funnel analysis"""
    title: str = "User Acquisition Funnel"
    steps: List[FunnelStep] = Field(default_factory=list)
    overall_conversion: float = 0.0  # Final conversion rate
    biggest_drop_off: Optional[str] = None  # Which step has the biggest drop


# ============================================================================
# Score Models (for UX Audits)
# ============================================================================

class ScoreBreakdown(BaseModel):
    """Score breakdown for audit reports"""
    ux_score: float = Field(..., ge=0, le=10)
    performance_score: float = Field(..., ge=0, le=100)
    accessibility_score: float = Field(..., ge=0, le=100)
    seo_score: float = Field(..., ge=0, le=100)


class HeuristicScore(BaseModel):
    """Individual heuristic evaluation score"""
    name: str
    score: float = Field(..., ge=0, le=10)
    status: Literal["good", "ok", "bad"] = "ok"


# ============================================================================
# Feature Table Models
# ============================================================================

class FeatureRow(BaseModel):
    """A feature in the recommended features table"""
    feature: str
    priority: Literal["Must Have", "Should Have", "Nice to Have"]
    investment: str  # e.g., "$500-1,000"
    timeline: str  # e.g., "Week 1-2"
    description: Optional[str] = None


class AppScreen(BaseModel):
    """An app screen in the proposal"""
    name: str
    description: str
    key_features: List[str] = Field(default_factory=list)


# ============================================================================
# AI Analysis Log
# ============================================================================

class AILogEntry(BaseModel):
    """An entry in the AI analysis log"""
    agent: str
    action: str
    result: str
    timestamp: Optional[datetime] = None


# ============================================================================
# Complete Report Model
# ============================================================================

class BusinessReport(BaseModel):
    """Complete business insights report"""
    # Metadata
    report_type: ReportType
    company_name: str
    industry: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    report_id: Optional[str] = None

    # Cover page stats (for audit reports)
    cover_stats: List[MetricItem] = Field(default_factory=list)

    # Main sections
    executive_summary: ExecutiveSummary
    industry_section: Optional[IndustrySection] = None
    competitor_analysis: Optional[CompetitorAnalysis] = None
    design_system: Optional[DesignSystem] = None

    # Issues and recommendations
    issues_found: List[IssueCard] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)

    # Funnel analysis (for audits)
    funnel_analysis: Optional[FunnelAnalysis] = None

    # Scores (for audits)
    score_breakdown: Optional[ScoreBreakdown] = None
    heuristic_scores: List[HeuristicScore] = Field(default_factory=list)

    # Features and screens (for proposals)
    recommended_features: List[FeatureRow] = Field(default_factory=list)
    app_screens: List[AppScreen] = Field(default_factory=list)

    # Roadmap
    roadmap: List[RoadmapPhase] = Field(default_factory=list)

    # KPIs and ROI
    kpis: List[KPIRow] = Field(default_factory=list)
    roi_projections: List[ROIProjection] = Field(default_factory=list)

    # For comprehensive reports
    prototype_embed_url: Optional[str] = None
    ai_analysis_log: List[AILogEntry] = Field(default_factory=list)

    # Footer
    data_sources: List[str] = Field(default_factory=list)
    confidence_level: str = "95% on primary recommendations"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
