"""
Comprehensive Audit Report Generator
Generates powerful, decision-driving audit reports in the style of JUICENET_COMPREHENSIVE_AUDIT_2026.md

Features:
- ASCII funnel diagrams with drop-off percentages
- Nielsen's 10 Heuristics evaluation
- ROI projections (conservative vs optimistic)
- Data-backed recommendations with confidence levels
- Multiple output formats (Markdown, HTML, PDF-ready)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import json


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class FunnelStage:
    """Represents a single stage in a conversion funnel"""
    name: str
    label: str  # Short label like "SIGNUP" or "EMAIL VERIFIED"
    count: int
    description: str = ""
    route: str = ""  # e.g., "/auth/signin"

    @property
    def rate(self) -> float:
        """Will be calculated when building funnel"""
        return 0.0

    @property
    def dropoff(self) -> float:
        """Will be calculated when building funnel"""
        return 0.0


@dataclass
class RetentionCohort:
    """Weekly retention cohort data"""
    week: str
    new_users: int
    day_1: float
    day_7: float
    day_30: float


@dataclass
class RevenueData:
    """Revenue metrics"""
    total_transactions: int = 0
    avg_transaction_value: float = 0.0
    booking_fee: float = 0.0
    monthly_revenue: float = 0.0
    notes: str = ""


@dataclass
class FlowAnalysis:
    """Analysis of a specific user flow"""
    flow_id: str
    flow_name: str
    screenshots: List[str] = field(default_factory=list)
    elements_checked: Dict[str, Any] = field(default_factory=dict)
    score: int = 0  # out of 10
    notes: str = ""


@dataclass
class UXIssue:
    """A UX issue found during audit"""
    id: str
    title: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    impact: str
    status: str = "observed"  # 'confirmed', 'observed'
    fix_difficulty: str = "medium"  # 'easy', 'medium', 'hard'
    screenshot: str = ""


@dataclass
class Recommendation:
    """A prioritized recommendation"""
    priority: int
    title: str
    problem: str
    data_support: str
    confidence: int  # percentage 0-100
    implementation: str
    expected_impact: str
    files_to_modify: List[str] = field(default_factory=list)
    code_snippets: Dict[str, str] = field(default_factory=dict)


@dataclass
class RoadmapPhase:
    """A phase in the implementation roadmap"""
    phase: str  # "Week 1-2", "Month 2", etc.
    title: str
    tasks: List[Dict[str, Any]] = field(default_factory=list)  # {'task': str, 'done': bool}


@dataclass
class DataSource:
    """A data source used in the audit"""
    name: str
    file: str
    records: int
    notes: str = ""


@dataclass
class TechStackItem:
    """Technology in the stack"""
    component: str
    technology: str
    assessment: str


@dataclass
class CompetitorAnalysis:
    """Competitor comparison"""
    competitor: str
    advantage: str
    opportunity: str


@dataclass
class ComprehensiveAuditData:
    """Complete data structure for a comprehensive audit report"""
    # Company Info
    app_name: str
    company_name: str = ""
    business_model: str = ""
    target_market: str = ""
    app_url: str = ""

    # Funnel Metrics
    funnel_stages: List[FunnelStage] = field(default_factory=list)
    funnel_title: str = "SIGNUP FUNNEL"

    # Additional Business Metrics
    host_metrics: Dict[str, Any] = field(default_factory=dict)
    retention_cohorts: List[RetentionCohort] = field(default_factory=list)
    revenue_data: RevenueData = field(default_factory=RevenueData)

    # UX Analysis
    testing_date: str = ""
    testing_url: str = ""
    device_viewport: str = "iPhone 14 Pro (390x844)"
    screenshots_count: int = 0
    flows_analyzed: List[FlowAnalysis] = field(default_factory=list)
    ux_issues: List[UXIssue] = field(default_factory=list)
    heuristics_scores: Dict[str, int] = field(default_factory=dict)

    # Marketing
    channel_metrics: Dict[str, Any] = field(default_factory=dict)
    page_view_data: List[Dict[str, Any]] = field(default_factory=list)
    competitors: List[CompetitorAnalysis] = field(default_factory=list)

    # Technical
    tech_stack: List[TechStackItem] = field(default_factory=list)
    code_quality_notes: Dict[str, List[str]] = field(default_factory=dict)
    api_issues: List[Dict[str, str]] = field(default_factory=list)

    # Recommendations
    recommendations: List[Recommendation] = field(default_factory=list)
    roadmap: List[RoadmapPhase] = field(default_factory=list)

    # Before/After Mockups (optional - will be auto-generated if not provided)
    # Each mockup: {'title': str, 'impact': str, 'before_html': str, 'after_html': str, 'changes': List[str]}
    mockups: List[Dict[str, Any]] = field(default_factory=list)

    # Success Metrics
    kpis: List[Dict[str, Any]] = field(default_factory=list)
    roi_projection: Dict[str, Any] = field(default_factory=dict)

    # Evidence
    screenshots_dir: str = ""
    data_sources: List[DataSource] = field(default_factory=list)
    appendix_content: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# NIELSEN'S HEURISTICS
# =============================================================================

NIELSENS_HEURISTICS = [
    {
        'id': 'visibility',
        'name': 'Visibility of System Status',
        'description': 'Users should always know what is happening through appropriate feedback'
    },
    {
        'id': 'match',
        'name': 'Match with Real World',
        'description': 'Use language and concepts familiar to users'
    },
    {
        'id': 'control',
        'name': 'User Control & Freedom',
        'description': 'Users can easily undo, redo, and escape'
    },
    {
        'id': 'consistency',
        'name': 'Consistency & Standards',
        'description': 'Follow platform and industry conventions'
    },
    {
        'id': 'prevention',
        'name': 'Error Prevention',
        'description': 'Prevent problems before they occur'
    },
    {
        'id': 'recognition',
        'name': 'Recognition over Recall',
        'description': 'Minimize memory load with visible options'
    },
    {
        'id': 'flexibility',
        'name': 'Flexibility & Efficiency',
        'description': 'Cater to both novice and expert users'
    },
    {
        'id': 'aesthetic',
        'name': 'Aesthetic & Minimal Design',
        'description': 'Keep interfaces clean and focused'
    },
    {
        'id': 'errors',
        'name': 'Help Users with Errors',
        'description': 'Clear error messages with solutions'
    },
    {
        'id': 'help',
        'name': 'Help & Documentation',
        'description': 'Provide help when needed'
    }
]


# =============================================================================
# FUNNEL GENERATOR
# =============================================================================

class FunnelGenerator:
    """Generates ASCII funnel diagrams"""

    @staticmethod
    def calculate_funnel_metrics(stages: List[FunnelStage]) -> List[Dict]:
        """Calculate rates and dropoffs for funnel stages"""
        if not stages:
            return []

        results = []
        base_count = stages[0].count

        for i, stage in enumerate(stages):
            rate = (stage.count / base_count * 100) if base_count > 0 else 0
            prev_count = stages[i - 1].count if i > 0 else stage.count
            dropoff = ((prev_count - stage.count) / prev_count * 100) if prev_count > 0 else 0
            lost = prev_count - stage.count if i > 0 else 0

            results.append({
                'name': stage.name,
                'label': stage.label,
                'count': stage.count,
                'rate': round(rate, 1),
                'dropoff': round(dropoff, 1),
                'lost': lost,
                'description': stage.description,
                'route': stage.route
            })

        return results

    @staticmethod
    def generate_ascii(stages: List[FunnelStage], title: str = "SIGNUP FUNNEL") -> str:
        """Generate ASCII funnel diagram matching JuiceNet format"""
        metrics = FunnelGenerator.calculate_funnel_metrics(stages)
        if not metrics:
            return "No funnel data available"

        lines = []
        lines.append(f"{title} - FROM YOUR DATA")
        lines.append("=" * 62)
        lines.append("")

        for i, stage in enumerate(metrics):
            # Stage header
            route_text = f" {stage['route']}" if stage['route'] else ""
            lines.append(f"[{stage['label']}]{route_text}")

            # Stage description and count
            desc = stage['description'] or f"{stage['count']:,} users"
            lines.append(f"         {desc}")
            lines.append(f"         {stage['count']:,} total ({stage['rate']}%)")

            # Show drop-off if not first stage and there's drop
            if i > 0 and stage['lost'] > 0:
                lines.append(f"         X {stage['lost']:,} LOST ({stage['dropoff']}% drop-off)")

            # Arrow to next stage (if not last)
            if i < len(metrics) - 1:
                lines.append("              |")
                if metrics[i + 1]['dropoff'] > 0:
                    lines.append(f"              | {metrics[i + 1]['dropoff']}% DROP-OFF")
                lines.append("              v")
                lines.append("")

        lines.append("")
        lines.append("=" * 62)

        # Overall conversion
        if len(metrics) >= 2:
            overall = (metrics[-1]['count'] / metrics[0]['count'] * 100) if metrics[0]['count'] > 0 else 0
            lines.append(f"OVERALL CONVERSION: {overall:.1f}% ({metrics[-1]['count']:,} / {metrics[0]['count']:,})")

        lines.append("=" * 62)

        return "\n".join(lines)

    @staticmethod
    def generate_markdown(stages: List[FunnelStage], title: str = "User Acquisition Funnel") -> str:
        """Generate markdown funnel with code block"""
        ascii_funnel = FunnelGenerator.generate_ascii(stages, title.upper().replace(" ", "_"))
        return f"### {title} (Real Data)\n\n```\n{ascii_funnel}\n```"


# =============================================================================
# HEURISTICS SCORER
# =============================================================================

class HeuristicsScorer:
    """Nielsen's Heuristics evaluation"""

    @staticmethod
    def generate_table(scores: Dict[str, int], notes: Dict[str, str] = None) -> str:
        """Generate markdown table of heuristics scores"""
        notes = notes or {}

        lines = [
            "| Heuristic | Score | Notes |",
            "|-----------|-------|-------|"
        ]

        total = 0
        for h in NIELSENS_HEURISTICS:
            score = scores.get(h['id'], 5)
            total += score
            note = notes.get(h['id'], '-')
            lines.append(f"| {h['name']} | {score}/10 | {note} |")

        avg = total / len(NIELSENS_HEURISTICS)
        lines.append("")
        lines.append(f"**Overall UX Score: {avg:.1f}/10**")

        return "\n".join(lines)

    @staticmethod
    def get_heuristic_name(heuristic_id: str) -> str:
        """Get full name from ID"""
        for h in NIELSENS_HEURISTICS:
            if h['id'] == heuristic_id:
                return h['name']
        return heuristic_id


# =============================================================================
# ROI CALCULATOR
# =============================================================================

class ROICalculator:
    """Calculate ROI projections"""

    @staticmethod
    def calculate(
        current_signups: int,
        current_conversion_pct: float,
        dropoff_recoverable_pct: float,
        avg_transaction_value: float,
        booking_fee: float = 0.0
    ) -> Dict[str, Dict]:
        """
        Calculate conservative and optimistic ROI projections

        Args:
            current_signups: Total signups
            current_conversion_pct: Current conversion rate (e.g., 0.9 for 0.9%)
            dropoff_recoverable_pct: Estimated % of dropoffs that can be recovered
            avg_transaction_value: Average value per transaction
            booking_fee: Platform fee per booking
        """
        # Calculate current lost users
        current_conversions = int(current_signups * (current_conversion_pct / 100))
        lost_users = current_signups - current_conversions

        # Conservative: 50% of estimated recovery
        conservative_recovery = dropoff_recoverable_pct * 0.5
        cons_recovered = int(lost_users * (conservative_recovery / 100))
        cons_booking_rate = 0.05  # 5% of recovered users book
        cons_bookings = int(cons_recovered * cons_booking_rate)
        cons_revenue = cons_bookings * (booking_fee if booking_fee else avg_transaction_value * 0.1)

        # Optimistic: 70% of estimated recovery
        optimistic_recovery = dropoff_recoverable_pct * 0.7
        opt_recovered = int(lost_users * (optimistic_recovery / 100))
        opt_booking_rate = 0.10  # 10% of recovered users book
        opt_bookings = int(opt_recovered * opt_booking_rate)
        opt_revenue = opt_bookings * (booking_fee if booking_fee else avg_transaction_value * 0.1)

        return {
            'conservative': {
                'label': 'Conservative Estimate (50% recovery)',
                'recovered_users': cons_recovered,
                'bookings_per_month': cons_bookings,
                'monthly_revenue': round(cons_revenue, 2),
                'assumptions': f"If {cons_booking_rate * 100:.0f}% book"
            },
            'optimistic': {
                'label': 'Optimistic Estimate (70% recovery)',
                'recovered_users': opt_recovered,
                'bookings_per_month': opt_bookings,
                'monthly_revenue': round(opt_revenue, 2),
                'assumptions': f"If {opt_booking_rate * 100:.0f}% book"
            }
        }

    @staticmethod
    def generate_markdown(roi_data: Dict) -> str:
        """Generate markdown ROI projection section"""
        lines = ["### ROI Projection", ""]

        for key in ['conservative', 'optimistic']:
            data = roi_data.get(key, {})
            lines.append(f"**{data.get('label', key.title())}**:")
            lines.append(f"- Additional completed signups: ~{data.get('recovered_users', 0):,}")
            lines.append(f"- {data.get('assumptions', '')}: +{data.get('bookings_per_month', 0)} reservations/month")
            lines.append(f"- Monthly platform revenue: +${data.get('monthly_revenue', 0):,.2f}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# COMPREHENSIVE REPORT GENERATOR
# =============================================================================

class ComprehensiveAuditReport:
    """Generates comprehensive audit reports"""

    def __init__(self, config: Dict = None):
        self.config = config or {
            'company_name': 'Weaver Pro',
            'company_tagline': 'AI-Powered UX Analysis',
            'contact_email': 'hello@weaver.pro',
            'contact_phone': '(555) 123-4567'
        }

    def generate_markdown(self, data: ComprehensiveAuditData) -> str:
        """Generate full markdown report matching JuiceNet format"""
        sections = []

        # Title
        sections.append(f"# {data.app_name} Comprehensive Business, App & Marketing Audit")
        sections.append(f"## {datetime.now().strftime('%B %Y')} | Data-Driven Analysis with Production Testing")
        sections.append("")
        sections.append("---")
        sections.append("")

        # Part 1: Executive Summary
        sections.append(self._generate_executive_summary(data))

        # Part 2: Business Analysis
        sections.append(self._generate_business_analysis(data))

        # Part 3: App UX Audit
        sections.append(self._generate_ux_audit(data))

        # Part 4: Marketing Analysis
        sections.append(self._generate_marketing_analysis(data))

        # Part 5: Technical Analysis
        sections.append(self._generate_technical_analysis(data))

        # Part 6: Data-Backed Recommendations
        sections.append(self._generate_recommendations(data))

        # Part 7: Implementation Roadmap
        sections.append(self._generate_roadmap(data))

        # Part 8: Success Metrics
        sections.append(self._generate_success_metrics(data))

        # Appendices
        sections.append(self._generate_appendices(data))

        # Conclusion
        sections.append(self._generate_conclusion(data))

        return "\n".join(sections)

    def _generate_executive_summary(self, data: ComprehensiveAuditData) -> str:
        """Generate Executive Summary section"""
        lines = [
            "## Executive Summary",
            "",
            "### Company Overview"
        ]

        # Company overview table
        if data.business_model or data.target_market:
            lines.append(f"- **Product**: {data.app_name}")
            if data.business_model:
                lines.append(f"- **Business Model**: {data.business_model}")
            if data.target_market:
                lines.append(f"- **Target Market**: {data.target_market}")
            lines.append("")

        # Critical Metrics table
        lines.append("### Critical Metrics (Real Data)")
        lines.append("")
        lines.append("| Metric | Value | Assessment |")
        lines.append("|--------|-------|------------|")

        # Build metrics from funnel stages
        funnel_metrics = FunnelGenerator.calculate_funnel_metrics(data.funnel_stages)
        for i, stage in enumerate(funnel_metrics):
            assessment = ""
            if stage['dropoff'] > 50:
                assessment = f"**CRITICAL: {stage['dropoff']}% drop-off**"
            elif stage['dropoff'] > 20:
                assessment = f"**{stage['dropoff']}% lost**"
            elif stage['dropoff'] > 0:
                assessment = f"{stage['dropoff']}% drop-off"
            else:
                assessment = "Baseline" if i == 0 else "Good"

            lines.append(f"| {stage['name']} | {stage['count']:,} ({stage['rate']:.1f}%) | {assessment} |")

        lines.append("")

        # Bottom Line
        if funnel_metrics:
            overall = funnel_metrics[-1]['rate']
            lines.append("### Bottom Line")
            if overall < 5:
                lines.append(f"**Your funnel is leaking at multiple points.** Only {overall:.1f}% of users complete the journey. The issues are fixable.")
            elif overall < 20:
                lines.append(f"**Room for improvement.** {overall:.1f}% conversion is below industry average. See recommendations below.")
            else:
                lines.append(f"**Solid foundation.** {overall:.1f}% conversion with opportunities for optimization.")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_business_analysis(self, data: ComprehensiveAuditData) -> str:
        """Generate Business Analysis section"""
        lines = [
            "## Part 1: Business Analysis",
            ""
        ]

        # Funnel
        lines.append("### 1.1 User Acquisition Funnel (Real Data)")
        lines.append("")
        ascii_funnel = FunnelGenerator.generate_ascii(data.funnel_stages, data.funnel_title)
        lines.append("```")
        lines.append(ascii_funnel)
        lines.append("```")
        lines.append("")

        # Host/Supplier metrics if present
        if data.host_metrics:
            lines.append("### 1.2 Host/Supplier Analysis")
            lines.append("")
            lines.append("| Metric | Count | Percentage |")
            lines.append("|--------|-------|------------|")
            for key, value in data.host_metrics.items():
                if isinstance(value, dict):
                    lines.append(f"| {value.get('name', key)} | {value.get('count', 0):,} | {value.get('pct', '-')} |")
                else:
                    lines.append(f"| {key} | {value} | - |")
            lines.append("")

        # Revenue
        if data.revenue_data.total_transactions > 0:
            lines.append("### 1.3 Revenue Analysis")
            lines.append("")
            lines.append(f"- **Total Transactions**: {data.revenue_data.total_transactions}")
            lines.append(f"- **Average Transaction**: ${data.revenue_data.avg_transaction_value:.2f}")
            if data.revenue_data.booking_fee > 0:
                lines.append(f"- **Booking Fee**: ${data.revenue_data.booking_fee:.2f}")
            if data.revenue_data.monthly_revenue > 0:
                lines.append(f"- **Monthly Revenue**: ${data.revenue_data.monthly_revenue:.2f}")
            if data.revenue_data.notes:
                lines.append(f"- **Note**: {data.revenue_data.notes}")
            lines.append("")

        # Retention
        if data.retention_cohorts:
            lines.append("### 1.4 Retention Analysis")
            lines.append("")
            lines.append("| Cohort Week | New Users | Day 1 Return | Day 7 Return | Day 30 Return |")
            lines.append("|-------------|-----------|--------------|--------------|---------------|")
            for cohort in data.retention_cohorts:
                lines.append(f"| {cohort.week} | {cohort.new_users} | {cohort.day_1}% | {cohort.day_7}% | {cohort.day_30}% |")
            lines.append("")

            # Critical finding about retention
            worst_d30 = min([c.day_30 for c in data.retention_cohorts]) if data.retention_cohorts else 0
            if worst_d30 < 5:
                lines.append(f"**Critical Finding**: Day 30 retention is essentially {worst_d30}%. Users sign up and never come back.")
                lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_ux_audit(self, data: ComprehensiveAuditData) -> str:
        """Generate UX Audit section"""
        lines = [
            "## Part 2: App UX Audit (Production Testing)",
            ""
        ]

        # Methodology
        lines.append("### 2.1 Testing Methodology")
        lines.append(f"- **URL Tested**: {data.testing_url or data.app_url}")
        lines.append(f"- **Device Viewport**: {data.device_viewport}")
        lines.append(f"- **Screenshots Captured**: {data.screenshots_count} screens")
        if data.testing_date:
            lines.append(f"- **Date**: {data.testing_date}")
        lines.append("")

        # Flow Analysis
        if data.flows_analyzed:
            lines.append("### 2.2 User Flow Analysis")
            lines.append("")
            for flow in data.flows_analyzed:
                lines.append(f"#### Flow: {flow.flow_name}")
                if flow.screenshots:
                    lines.append(f"**Screenshots**: `{', '.join(flow.screenshots)}`")
                lines.append("")
                if flow.elements_checked:
                    lines.append("| Element | Present | Quality |")
                    lines.append("|---------|---------|---------|")
                    for elem, check in flow.elements_checked.items():
                        present = "Yes" if check.get('present', True) else "No"
                        quality = check.get('quality', '-')
                        lines.append(f"| {elem} | {present} | {quality} |")
                    lines.append("")
                lines.append(f"**Score: {flow.score}/10** - {flow.notes}")
                lines.append("")

        # UX Issues Summary
        if data.ux_issues:
            lines.append("### 2.3 UX Issues Summary")
            lines.append("")
            lines.append("| Issue | Severity | Impact | Fix Difficulty | Status |")
            lines.append("|-------|----------|--------|----------------|--------|")
            for issue in data.ux_issues:
                status_text = f"**{issue.status.upper()}**" if issue.status == 'confirmed' else issue.status.capitalize()
                lines.append(f"| {issue.title} | {issue.severity.capitalize()} | {issue.impact} | {issue.fix_difficulty.capitalize()} | {status_text} |")
            lines.append("")

        # Nielsen's Heuristics
        if data.heuristics_scores:
            lines.append("### 2.4 Nielsen's Heuristics Evaluation")
            lines.append("")
            lines.append(HeuristicsScorer.generate_table(data.heuristics_scores))
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_marketing_analysis(self, data: ComprehensiveAuditData) -> str:
        """Generate Marketing Analysis section"""
        lines = [
            "## Part 3: Marketing Analysis",
            ""
        ]

        # Channel Performance
        if data.channel_metrics:
            lines.append("### 3.1 Channel Performance")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for metric, value in data.channel_metrics.items():
                lines.append(f"| {metric} | {value} |")
            lines.append("")

        # Page View Funnel
        if data.page_view_data:
            lines.append("### 3.2 Funnel Analysis by Page")
            lines.append("")
            lines.append("| Page | Views | Unique Users | Drop-off |")
            lines.append("|------|-------|--------------|----------|")
            for page in data.page_view_data:
                lines.append(f"| {page.get('page', '')} | {page.get('views', 0):,} | {page.get('unique', 0):,} | {page.get('dropoff', '-')} |")
            lines.append("")

        # Competitors
        if data.competitors:
            lines.append("### 3.3 Competitive Analysis")
            lines.append("")
            lines.append("| Competitor | Advantage | Your Opportunity |")
            lines.append("|------------|-----------|------------------|")
            for comp in data.competitors:
                lines.append(f"| {comp.competitor} | {comp.advantage} | {comp.opportunity} |")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_technical_analysis(self, data: ComprehensiveAuditData) -> str:
        """Generate Technical Analysis section"""
        lines = [
            "## Part 4: Technical Analysis",
            ""
        ]

        # Tech Stack
        if data.tech_stack:
            lines.append("### 4.1 Architecture Overview")
            lines.append("")
            lines.append("| Component | Technology | Assessment |")
            lines.append("|-----------|------------|------------|")
            for item in data.tech_stack:
                lines.append(f"| {item.component} | {item.technology} | {item.assessment} |")
            lines.append("")

        # Code Quality
        if data.code_quality_notes:
            lines.append("### 4.2 Code Quality Observations")
            lines.append("")
            if 'positive' in data.code_quality_notes:
                lines.append("**Positive**:")
                for note in data.code_quality_notes['positive']:
                    lines.append(f"- {note}")
                lines.append("")
            if 'improvements' in data.code_quality_notes:
                lines.append("**Areas for Improvement**:")
                for note in data.code_quality_notes['improvements']:
                    lines.append(f"- {note}")
                lines.append("")

        # API Issues
        if data.api_issues:
            lines.append("### 4.3 API Endpoints Review")
            lines.append("")
            lines.append("| Endpoint | Function | Issue |")
            lines.append("|----------|----------|-------|")
            for api in data.api_issues:
                lines.append(f"| {api.get('endpoint', '')} | {api.get('function', '')} | {api.get('issue', '')} |")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_recommendations(self, data: ComprehensiveAuditData) -> str:
        """Generate Data-Backed Recommendations section"""
        lines = [
            "## Part 5: Data-Backed Recommendations",
            ""
        ]

        for rec in data.recommendations:
            severity = "CRITICAL" if rec.priority == 1 else "HIGH" if rec.priority <= 3 else "MEDIUM"
            lines.append(f"### Priority {rec.priority}: {rec.title} ({severity})")
            lines.append("")
            lines.append(f"**Problem**: {rec.problem}")
            lines.append(f"**Data Support**: {rec.data_support}")
            lines.append(f"**Confidence**: {rec.confidence}%")
            lines.append("")

            if rec.implementation:
                lines.append("#### Implementation Details")
                lines.append("")
                lines.append(rec.implementation)
                lines.append("")

            if rec.files_to_modify:
                lines.append("**Files to Modify**:")
                for f in rec.files_to_modify:
                    lines.append(f"- `{f}`")
                lines.append("")

            if rec.code_snippets:
                for filename, code in rec.code_snippets.items():
                    lines.append(f"**{filename}**:")
                    lines.append("```")
                    lines.append(code)
                    lines.append("```")
                    lines.append("")

            lines.append(f"**Expected Impact**: {rec.expected_impact}")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_roadmap(self, data: ComprehensiveAuditData) -> str:
        """Generate Implementation Roadmap section"""
        lines = [
            "## Part 6: Implementation Roadmap",
            ""
        ]

        for phase in data.roadmap:
            lines.append(f"### {phase.phase}: {phase.title}")
            for task in phase.tasks:
                checkbox = "[x]" if task.get('done', False) else "[ ]"
                lines.append(f"- {checkbox} {task.get('task', '')}")
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_success_metrics(self, data: ComprehensiveAuditData) -> str:
        """Generate Success Metrics section"""
        lines = [
            "## Part 7: Success Metrics",
            ""
        ]

        # KPIs table
        if data.kpis:
            lines.append("### KPIs to Track")
            lines.append("")
            lines.append("| Metric | Current | Target (30 days) | Target (90 days) |")
            lines.append("|--------|---------|------------------|------------------|")
            for kpi in data.kpis:
                lines.append(f"| {kpi.get('metric', '')} | {kpi.get('current', '')} | {kpi.get('target_30', '')} | {kpi.get('target_90', '')} |")
            lines.append("")

        # ROI Projection
        if data.roi_projection:
            lines.append(ROICalculator.generate_markdown(data.roi_projection))
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _generate_appendices(self, data: ComprehensiveAuditData) -> str:
        """Generate Appendices section"""
        lines = []

        # Data Sources
        if data.data_sources:
            lines.append("## Appendix A: Data Sources")
            lines.append("")
            lines.append("| Source | File | Records |")
            lines.append("|--------|------|---------|")
            for source in data.data_sources:
                lines.append(f"| {source.name} | {source.file} | {source.records:,} |")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Screenshots
        if data.screenshots_dir:
            lines.append("## Appendix B: Screenshot Evidence")
            lines.append("")
            lines.append(f"**Location**: `{data.screenshots_dir}`")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Additional appendix content
        for title, content in data.appendix_content.items():
            lines.append(f"## Appendix: {title}")
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _generate_conclusion(self, data: ComprehensiveAuditData) -> str:
        """Generate Conclusion section"""
        lines = [
            "## Conclusion",
            ""
        ]

        # Count critical issues
        critical_count = len([i for i in data.ux_issues if i.severity == 'critical'])
        high_count = len([i for i in data.ux_issues if i.severity == 'high'])

        if critical_count > 0:
            lines.append(f"{data.app_name} has solid product fundamentals but is losing users due to UX friction. ")
            lines.append(f"We identified **{critical_count} critical issues** that require immediate attention.")
            lines.append("")
            lines.append("The fixes are straightforward and well-documented. Implementation of Priority 1 alone could recover 50%+ of lost users.")
            lines.append("")
        elif high_count > 0:
            lines.append(f"Overall, {data.app_name} provides a good user experience with some areas for improvement. ")
            lines.append(f"We identified **{high_count} high-priority issues** that would improve conversion rates.")
            lines.append("")
        else:
            lines.append(f"{data.app_name} has a strong UX foundation. The recommendations focus on optimization and growth.")
            lines.append("")

        lines.append("**Recommended Next Step**: Implement the highest priority fix and measure impact over 30 days before proceeding.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated: {datetime.now().strftime('%B %d, %Y')}*")
        lines.append(f"*Analysis by: {self.config.get('company_name', 'Weaver Pro')}*")
        lines.append("")

        return "\n".join(lines)

    def generate(
        self,
        data: ComprehensiveAuditData,
        output_format: str = 'markdown',
        output_path: str = None
    ) -> str:
        """
        Generate comprehensive audit report

        Args:
            data: ComprehensiveAuditData with all audit information
            output_format: 'markdown', 'html', or 'json'
            output_path: Optional path to save the report
        """
        if output_format == 'markdown':
            content = self.generate_markdown(data)
        elif output_format == 'html':
            md_content = self.generate_markdown(data)
            content = self._convert_to_html(md_content, data)
        elif output_format == 'json':
            content = self._to_json(data)
        else:
            content = self.generate_markdown(data)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[REPORT] Saved to: {output_path}")

        return content

    def _convert_to_html(self, markdown_content: str, data: ComprehensiveAuditData) -> str:
        """Convert markdown to styled HTML"""
        # Basic HTML wrapper with styling
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.app_name} - Comprehensive Audit Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #F8FAFC;
            color: #1E293B;
            line-height: 1.7;
            padding: 40px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            padding: 60px;
        }}

        h1 {{
            font-size: 32px;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 8px;
            border-bottom: 4px solid #3B82F6;
            padding-bottom: 16px;
        }}

        h2 {{
            font-size: 24px;
            font-weight: 700;
            color: #0F172A;
            margin-top: 48px;
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 2px solid #E2E8F0;
        }}

        h3 {{
            font-size: 18px;
            font-weight: 600;
            color: #334155;
            margin-top: 32px;
            margin-bottom: 16px;
        }}

        h4 {{
            font-size: 16px;
            font-weight: 600;
            color: #475569;
            margin-top: 24px;
            margin-bottom: 12px;
        }}

        p {{
            margin-bottom: 16px;
        }}

        ul, ol {{
            margin-bottom: 16px;
            padding-left: 24px;
        }}

        li {{
            margin-bottom: 8px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}

        th {{
            background: #F1F5F9;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #E2E8F0;
        }}

        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #E2E8F0;
        }}

        tr:hover {{
            background: #F8FAFC;
        }}

        code {{
            font-family: 'JetBrains Mono', monospace;
            background: #F1F5F9;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 13px;
        }}

        pre {{
            background: #0F172A;
            color: #E2E8F0;
            padding: 20px;
            border-radius: 12px;
            overflow-x: auto;
            margin: 20px 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
        }}

        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}

        strong {{
            font-weight: 600;
            color: #0F172A;
        }}

        hr {{
            border: none;
            border-top: 1px solid #E2E8F0;
            margin: 40px 0;
        }}

        .critical {{ color: #DC2626; font-weight: 700; }}
        .high {{ color: #D97706; font-weight: 600; }}
        .medium {{ color: #2563EB; }}
        .good {{ color: #059669; }}

        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; padding: 20px; }}
            pre {{ white-space: pre-wrap; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
{self._markdown_to_html(markdown_content)}
        </div>
    </div>
</body>
</html>"""
        return html

    def _markdown_to_html(self, md: str) -> str:
        """Basic markdown to HTML conversion"""
        import re

        html = md

        # Headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        # Code blocks
        html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)

        # Tables (basic)
        lines = html.split('\n')
        in_table = False
        new_lines = []
        for line in lines:
            if '|' in line and not line.strip().startswith('```'):
                if not in_table:
                    new_lines.append('<table>')
                    in_table = True

                cells = [c.strip() for c in line.split('|') if c.strip()]
                if '---' in line:
                    continue  # Skip separator row

                row_tag = 'th' if not any('<tr>' in l for l in new_lines[-5:]) else 'td'
                if in_table and '</tr>' not in ''.join(new_lines[-3:]):
                    row_tag = 'th'
                else:
                    row_tag = 'td'

                new_lines.append('<tr>')
                for cell in cells:
                    new_lines.append(f'<{row_tag}>{cell}</{row_tag}>')
                new_lines.append('</tr>')
            else:
                if in_table:
                    new_lines.append('</table>')
                    in_table = False
                new_lines.append(line)

        if in_table:
            new_lines.append('</table>')

        html = '\n'.join(new_lines)

        # Lists
        html = re.sub(r'^- \[x\] (.+)$', r'<li style="list-style:none;">&#9745; \1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^- \[ \] (.+)$', r'<li style="list-style:none;">&#9744; \1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

        # Paragraphs (basic)
        html = re.sub(r'^(?!<[hultop]|$)(.+)$', r'<p>\1</p>', html, flags=re.MULTILINE)

        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)

        return html

    def _to_json(self, data: ComprehensiveAuditData) -> str:
        """Convert audit data to JSON"""
        # Convert dataclass to dict
        from dataclasses import asdict
        return json.dumps(asdict(data), indent=2, default=str)


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate comprehensive audit reports in JuiceNet format'
    )
    parser.add_argument('--config', type=str, help='Path to audit config JSON')
    parser.add_argument('--output', type=str, default='audit_report.md', help='Output file path')
    parser.add_argument('--format', type=str, default='markdown', choices=['markdown', 'html', 'json'])
    parser.add_argument('--demo', action='store_true', help='Generate demo report')

    args = parser.parse_args()

    if args.demo:
        # Generate demo report
        data = create_demo_audit_data()
        report = ComprehensiveAuditReport()
        output = report.generate(data, output_format=args.format, output_path=args.output)
        print(f"Demo report generated: {args.output}")
    elif args.config:
        # Load from config
        with open(args.config, 'r') as f:
            config = json.load(f)
        # TODO: Parse config into ComprehensiveAuditData
        print("Config loading not yet implemented")
    else:
        parser.print_help()


def create_demo_audit_data() -> ComprehensiveAuditData:
    """Create demo audit data for testing"""
    return ComprehensiveAuditData(
        app_name="DemoApp",
        company_name="Demo Company",
        business_model="SaaS subscription model",
        target_market="Small businesses",
        app_url="https://demoapp.example.com",

        funnel_stages=[
            FunnelStage(name="Page Views", label="PAGE VIEW", count=5000, route="/landing"),
            FunnelStage(name="Signups", label="SIGNUP", count=2000, description="Account created"),
            FunnelStage(name="Email Verified", label="VERIFIED", count=1500),
            FunnelStage(name="Profile Complete", label="PROFILE", count=800),
            FunnelStage(name="First Action", label="ACTIVE", count=200),
        ],
        funnel_title="USER ACQUISITION FUNNEL",

        testing_date=datetime.now().strftime("%B %d, %Y"),
        testing_url="https://demoapp.example.com",
        screenshots_count=50,

        ux_issues=[
            UXIssue(
                id="1",
                title="Email verification breaks flow",
                description="Users leave app to verify email and never return",
                severity="critical",
                impact="25% drop-off",
                status="confirmed",
                fix_difficulty="medium"
            ),
            UXIssue(
                id="2",
                title="Too many onboarding steps",
                description="5+ steps before first value",
                severity="high",
                impact="40% abandonment",
                status="observed",
                fix_difficulty="medium"
            )
        ],

        heuristics_scores={
            'visibility': 7,
            'match': 8,
            'control': 5,
            'consistency': 8,
            'prevention': 6,
            'recognition': 7,
            'flexibility': 5,
            'aesthetic': 8,
            'errors': 6,
            'help': 4
        },

        recommendations=[
            Recommendation(
                priority=1,
                title="Fix Email Verification Flow",
                problem="Users must leave app to verify email, breaking momentum",
                data_support="25% drop-off at verification step (500 users lost)",
                confidence=95,
                implementation="Allow browsing while unverified + add verification polling",
                expected_impact="Recover 50-70% of dropped users (+250-350)",
                files_to_modify=["auth/verification.ts", "services/auth.service.ts"]
            )
        ],

        roadmap=[
            RoadmapPhase(
                phase="Week 1-2",
                title="Critical Fixes",
                tasks=[
                    {"task": "Implement unverified browsing", "done": False},
                    {"task": "Add verification polling", "done": False}
                ]
            )
        ],

        kpis=[
            {"metric": "Signup -> Verified", "current": "75%", "target_30": "85%", "target_90": "90%"},
            {"metric": "Verified -> Active", "current": "13%", "target_30": "25%", "target_90": "40%"}
        ],

        roi_projection=ROICalculator.calculate(
            current_signups=2000,
            current_conversion_pct=10,
            dropoff_recoverable_pct=50,
            avg_transaction_value=50,
            booking_fee=5
        ),

        data_sources=[
            DataSource(name="User Database", file="users.csv", records=2000),
            DataSource(name="Analytics", file="analytics_export.csv", records=50000)
        ]
    )


if __name__ == "__main__":
    main()
