"""
Unified Data Model for Weaver Pro Audit Reports

This module provides a MODULAR, FLEXIBLE data model that works for any business type:
- SaaS applications
- E-commerce stores
- Marketplaces
- B2B services
- Content platforms
- Any custom business

The key principle: Nothing is hardcoded. Users define their own:
- Sections (what appears in the report)
- Metrics (what numbers to track)
- Issues (problems found)
- Recommendations (actions to take)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class DataConfidence(Enum):
    """Indicates the reliability of a data point."""
    VERIFIED = "verified"      # From real database/CSV import
    ESTIMATED = "estimated"    # Calculated/inferred from other data
    PLACEHOLDER = "placeholder"  # Default values, not real data


class AuditType(Enum):
    """Pre-defined audit templates for common use cases."""
    UX_APP = "ux_app"           # App/website UX audit
    MARKETING = "marketing"     # Marketing performance audit
    BUSINESS = "business"       # Business model audit
    TECHNICAL = "technical"     # Technical/security audit
    CUSTOM = "custom"           # User-defined audit


class ChartType(Enum):
    """Visualization types for metrics."""
    FUNNEL = "funnel"           # Funnel/conversion chart
    BAR = "bar"                 # Bar chart
    LINE = "line"               # Line/trend chart
    PIE = "pie"                 # Pie chart
    TABLE = "table"             # Data table
    METRIC = "metric"           # Single metric card
    NONE = "none"               # No visualization


@dataclass
class Metric:
    """
    A flexible metric that can represent any measurable value.

    Examples:
    - Funnel stage: name="Email Verified", value=1543, category="funnel"
    - Revenue: name="Monthly Revenue", value=45000, category="financial"
    - Engagement: name="DAU", value=5200, category="engagement"
    """
    id: str
    name: str
    value: float
    category: str = "general"  # funnel, financial, engagement, hosts, custom
    unit: str = ""             # "$", "%", "users", etc.
    previous_value: Optional[float] = None  # For trend/comparison
    target_value: Optional[float] = None    # Goal to hit
    rate: Optional[float] = None            # Percentage (for funnels)
    dropoff: Optional[float] = None         # Drop from previous (for funnels)
    confidence: DataConfidence = DataConfidence.PLACEHOLDER
    source: str = ""
    chart_type: ChartType = ChartType.METRIC
    order: int = 0             # Display order within category

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'category': self.category,
            'unit': self.unit,
            'previous_value': self.previous_value,
            'target_value': self.target_value,
            'rate': self.rate,
            'dropoff': self.dropoff,
            'confidence': self.confidence.value,
            'source': self.source,
            'chart_type': self.chart_type.value,
            'order': self.order
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Metric':
        return cls(
            id=data['id'],
            name=data['name'],
            value=data['value'],
            category=data.get('category', 'general'),
            unit=data.get('unit', ''),
            previous_value=data.get('previous_value'),
            target_value=data.get('target_value'),
            rate=data.get('rate'),
            dropoff=data.get('dropoff'),
            confidence=DataConfidence(data.get('confidence', 'placeholder')),
            source=data.get('source', ''),
            chart_type=ChartType(data.get('chart_type', 'metric')),
            order=data.get('order', 0)
        )


@dataclass
class Issue:
    """
    A problem or issue found during the audit.

    Works for any audit type:
    - UX issue: "Confusing navigation"
    - Marketing issue: "Low email open rates"
    - Technical issue: "Slow API response times"
    - Business issue: "High customer churn"
    """
    id: str
    title: str
    description: str
    category: str = "general"  # ux, marketing, technical, business, custom
    severity: str = "medium"   # critical, high, medium, low
    impact: str = ""
    evidence: str = ""         # Screenshot path, data reference, etc.
    enabled: bool = True
    confidence: DataConfidence = DataConfidence.ESTIMATED

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'severity': self.severity,
            'impact': self.impact,
            'evidence': self.evidence,
            'enabled': self.enabled,
            'confidence': self.confidence.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Issue':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            category=data.get('category', 'general'),
            severity=data.get('severity', 'medium'),
            impact=data.get('impact', ''),
            evidence=data.get('evidence', ''),
            enabled=data.get('enabled', True),
            confidence=DataConfidence(data.get('confidence', 'estimated'))
        )


@dataclass
class Recommendation:
    """
    An actionable recommendation from the audit.

    Flexible enough for any recommendation type:
    - UX: "Add progress indicators"
    - Marketing: "Implement email drip campaign"
    - Technical: "Add database indexes"
    - Business: "Introduce annual pricing tier"
    """
    id: str
    title: str
    description: str
    category: str = "general"
    priority: int = 1
    impact: str = ""
    effort: str = ""
    roi_estimate: Optional[str] = None
    implementation_notes: Optional[str] = None
    code_snippet: Optional[str] = None
    related_issue_ids: List[str] = field(default_factory=list)
    enabled: bool = True
    confidence: DataConfidence = DataConfidence.ESTIMATED

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'impact': self.impact,
            'effort': self.effort,
            'roi_estimate': self.roi_estimate,
            'implementation_notes': self.implementation_notes,
            'code_snippet': self.code_snippet,
            'related_issue_ids': self.related_issue_ids,
            'enabled': self.enabled,
            'confidence': self.confidence.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Recommendation':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            category=data.get('category', 'general'),
            priority=data.get('priority', 1),
            impact=data.get('impact', ''),
            effort=data.get('effort', ''),
            roi_estimate=data.get('roi_estimate'),
            implementation_notes=data.get('implementation_notes'),
            code_snippet=data.get('code_snippet'),
            related_issue_ids=data.get('related_issue_ids', []),
            enabled=data.get('enabled', True),
            confidence=DataConfidence(data.get('confidence', 'estimated'))
        )


@dataclass
class ReportSection:
    """
    A section in the report that can be toggled on/off.

    Sections are completely customizable - users define what sections
    they want in their report.
    """
    id: str
    title: str
    description: str = ""
    content_type: str = "markdown"  # markdown, metrics, issues, recommendations, custom
    custom_content: str = ""        # For custom sections
    order: int = 0
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content_type': self.content_type,
            'custom_content': self.custom_content,
            'order': self.order,
            'enabled': self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ReportSection':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            content_type=data.get('content_type', 'markdown'),
            custom_content=data.get('custom_content', ''),
            order=data.get('order', 0),
            enabled=data.get('enabled', True)
        )


@dataclass
class AuditData:
    """
    Single source of truth for all audit report data.

    This is a MODULAR data model that works for any business type.
    Instead of hardcoded fields like "funnel_stages" or "hosts",
    everything is stored in flexible collections.

    Usage:
        # For a SaaS UX audit
        data = AuditData(app_name="MyApp", audit_type=AuditType.UX_APP)
        data.add_metric(Metric(id="signup", name="Signups", value=1000, category="funnel"))

        # For a marketing audit
        data = AuditData(app_name="MyBrand", audit_type=AuditType.MARKETING)
        data.add_metric(Metric(id="cac", name="CAC", value=45, unit="$", category="financial"))
    """

    # Basic Info
    name: str                      # Business/app name
    audit_type: AuditType = AuditType.CUSTOM
    tagline: str = ""
    audit_date: str = ""
    auditor: str = ""
    company_name: str = ""
    business_model: str = ""
    target_market: str = ""
    executive_summary: str = ""

    # Flexible Data Collections
    metrics: List[Metric] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    sections: List[ReportSection] = field(default_factory=list)

    # Scoring (optional, customizable)
    scores: Dict[str, int] = field(default_factory=dict)  # e.g., {"usability": 7, "performance": 8}

    # Metadata
    data_sources: List[str] = field(default_factory=list)
    overall_confidence: DataConfidence = DataConfidence.PLACEHOLDER
    prototype_path: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)  # For any additional data

    # --- Helper Methods ---

    def add_metric(self, metric: Metric):
        """Add a metric to the audit."""
        self.metrics.append(metric)

    def add_issue(self, issue: Issue):
        """Add an issue to the audit."""
        self.issues.append(issue)

    def add_recommendation(self, rec: Recommendation):
        """Add a recommendation to the audit."""
        self.recommendations.append(rec)

    def add_section(self, section: ReportSection):
        """Add a section to the report."""
        self.sections.append(section)

    def get_metrics_by_category(self, category: str) -> List[Metric]:
        """Get all metrics in a category."""
        return sorted(
            [m for m in self.metrics if m.category == category],
            key=lambda x: x.order
        )

    def get_funnel_metrics(self) -> List[Metric]:
        """Get metrics marked as funnel type (convenience method)."""
        return self.get_metrics_by_category("funnel")

    def get_issues_by_category(self, category: str) -> List[Issue]:
        """Get issues in a category."""
        return [i for i in self.issues if i.category == category and i.enabled]

    def get_issues_by_severity(self, severity: str) -> List[Issue]:
        """Get issues by severity level."""
        return [i for i in self.issues if i.severity == severity and i.enabled]

    def get_enabled_issues(self) -> List[Issue]:
        """Get all enabled issues."""
        return [i for i in self.issues if i.enabled]

    def get_enabled_recommendations(self) -> List[Recommendation]:
        """Get enabled recommendations sorted by priority."""
        return sorted(
            [r for r in self.recommendations if r.enabled],
            key=lambda x: x.priority
        )

    def get_enabled_sections(self) -> List[ReportSection]:
        """Get enabled sections sorted by order."""
        return sorted(
            [s for s in self.sections if s.enabled],
            key=lambda x: x.order
        )

    def validate(self) -> List[str]:
        """Return list of validation errors. Empty list means valid."""
        errors = []

        if not self.name:
            errors.append("Business/app name is required")

        for metric in self.metrics:
            if metric.value < 0 and metric.unit != "change":
                errors.append(f"Metric '{metric.name}' has invalid negative value")

        for rec in self.recommendations:
            if rec.priority < 1:
                errors.append(f"Recommendation '{rec.title}' has invalid priority")

        return errors

    def calculate_confidence(self) -> DataConfidence:
        """Calculate overall confidence based on data sources."""
        if not self.metrics:
            return DataConfidence.PLACEHOLDER

        verified_count = sum(
            1 for m in self.metrics
            if m.confidence == DataConfidence.VERIFIED
        )

        if verified_count == len(self.metrics):
            return DataConfidence.VERIFIED
        elif verified_count > 0:
            return DataConfidence.ESTIMATED
        return DataConfidence.PLACEHOLDER

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            'name': self.name,
            'audit_type': self.audit_type.value,
            'tagline': self.tagline,
            'audit_date': self.audit_date,
            'auditor': self.auditor,
            'company_name': self.company_name,
            'business_model': self.business_model,
            'target_market': self.target_market,
            'executive_summary': self.executive_summary,
            'metrics': [m.to_dict() for m in self.metrics],
            'issues': [i.to_dict() for i in self.issues],
            'recommendations': [r.to_dict() for r in self.recommendations],
            'sections': [s.to_dict() for s in self.sections],
            'scores': self.scores,
            'data_sources': self.data_sources,
            'overall_confidence': self.overall_confidence.value,
            'prototype_path': self.prototype_path,
            'custom_data': self.custom_data
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AuditData':
        """Deserialize from dictionary."""
        return cls(
            name=data['name'],
            audit_type=AuditType(data.get('audit_type', 'custom')),
            tagline=data.get('tagline', ''),
            audit_date=data.get('audit_date', ''),
            auditor=data.get('auditor', ''),
            company_name=data.get('company_name', ''),
            business_model=data.get('business_model', ''),
            target_market=data.get('target_market', ''),
            executive_summary=data.get('executive_summary', ''),
            metrics=[Metric.from_dict(m) for m in data.get('metrics', [])],
            issues=[Issue.from_dict(i) for i in data.get('issues', [])],
            recommendations=[Recommendation.from_dict(r) for r in data.get('recommendations', [])],
            sections=[ReportSection.from_dict(s) for s in data.get('sections', [])],
            scores=data.get('scores', {}),
            data_sources=data.get('data_sources', []),
            overall_confidence=DataConfidence(data.get('overall_confidence', 'placeholder')),
            prototype_path=data.get('prototype_path'),
            custom_data=data.get('custom_data', {})
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'AuditData':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


# --- AUDIT TEMPLATES ---
# Pre-defined section configurations for common audit types

def get_ux_app_sections() -> List[ReportSection]:
    """Default sections for a UX/App audit."""
    return [
        ReportSection("executive", "Executive Summary", "High-level overview for stakeholders", "markdown", "", 1),
        ReportSection("metrics", "Key Metrics", "User funnel and engagement data", "metrics", "", 2),
        ReportSection("issues", "UX Issues Found", "Problems identified during testing", "issues", "", 3),
        ReportSection("heuristics", "Heuristics Evaluation", "Nielsen's 10 usability principles", "scores", "", 4),
        ReportSection("recommendations", "Recommendations", "Prioritized action items", "recommendations", "", 5),
        ReportSection("roadmap", "Implementation Roadmap", "Suggested implementation order", "markdown", "", 6),
        ReportSection("roi", "ROI Projections", "Expected return on improvements", "metrics", "", 7),
    ]


def get_marketing_sections() -> List[ReportSection]:
    """Default sections for a Marketing audit."""
    return [
        ReportSection("executive", "Executive Summary", "Marketing performance overview", "markdown", "", 1),
        ReportSection("channels", "Channel Performance", "Performance by marketing channel", "metrics", "", 2),
        ReportSection("funnel", "Marketing Funnel", "Awareness to conversion", "metrics", "", 3),
        ReportSection("issues", "Issues & Opportunities", "Problems and growth areas", "issues", "", 4),
        ReportSection("competitors", "Competitive Analysis", "Market positioning", "markdown", "", 5),
        ReportSection("recommendations", "Recommendations", "Marketing improvement actions", "recommendations", "", 6),
        ReportSection("budget", "Budget Recommendations", "Suggested budget allocation", "metrics", "", 7),
    ]


def get_business_sections() -> List[ReportSection]:
    """Default sections for a Business Model audit."""
    return [
        ReportSection("executive", "Executive Summary", "Business health overview", "markdown", "", 1),
        ReportSection("revenue", "Revenue Analysis", "Revenue streams and trends", "metrics", "", 2),
        ReportSection("costs", "Cost Structure", "Operating costs breakdown", "metrics", "", 3),
        ReportSection("customers", "Customer Analysis", "Customer segments and LTV", "metrics", "", 4),
        ReportSection("issues", "Business Challenges", "Risks and problems identified", "issues", "", 5),
        ReportSection("opportunities", "Growth Opportunities", "Potential expansion areas", "issues", "", 6),
        ReportSection("recommendations", "Strategic Recommendations", "Business improvement actions", "recommendations", "", 7),
    ]


def get_technical_sections() -> List[ReportSection]:
    """Default sections for a Technical audit."""
    return [
        ReportSection("executive", "Executive Summary", "Technical health overview", "markdown", "", 1),
        ReportSection("architecture", "Architecture Review", "System design analysis", "markdown", "", 2),
        ReportSection("performance", "Performance Metrics", "Speed and reliability data", "metrics", "", 3),
        ReportSection("security", "Security Assessment", "Vulnerabilities and risks", "issues", "", 4),
        ReportSection("code_quality", "Code Quality", "Code health indicators", "metrics", "", 5),
        ReportSection("recommendations", "Technical Recommendations", "Engineering improvements", "recommendations", "", 6),
        ReportSection("roadmap", "Technical Roadmap", "Implementation priorities", "markdown", "", 7),
    ]


def get_sections_for_type(audit_type: AuditType) -> List[ReportSection]:
    """Get default sections for an audit type."""
    section_map = {
        AuditType.UX_APP: get_ux_app_sections,
        AuditType.MARKETING: get_marketing_sections,
        AuditType.BUSINESS: get_business_sections,
        AuditType.TECHNICAL: get_technical_sections,
        AuditType.CUSTOM: lambda: [],
    }
    return section_map.get(audit_type, lambda: [])()


# --- SCORING TEMPLATES ---

NIELSENS_HEURISTICS = [
    'Visibility of System Status',
    'Match Between System and Real World',
    'User Control and Freedom',
    'Consistency and Standards',
    'Error Prevention',
    'Recognition Rather Than Recall',
    'Flexibility and Efficiency of Use',
    'Aesthetic and Minimalist Design',
    'Help Users Recognize and Recover from Errors',
    'Help and Documentation'
]

MARKETING_SCORE_CATEGORIES = [
    'Brand Awareness',
    'Lead Generation',
    'Conversion Rate',
    'Customer Retention',
    'Channel Effectiveness',
    'Content Quality',
    'SEO Performance',
    'Social Engagement',
    'Email Performance',
    'ROI Tracking'
]

TECHNICAL_SCORE_CATEGORIES = [
    'Performance',
    'Scalability',
    'Security',
    'Code Quality',
    'Documentation',
    'Testing Coverage',
    'Monitoring',
    'DevOps Maturity',
    'API Design',
    'Error Handling'
]
