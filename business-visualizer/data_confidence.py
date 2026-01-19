"""
Data Confidence System
Calculates confidence scores based on available data and suggests improvements

The more data provided, the higher the confidence in recommendations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class DataCategory(Enum):
    """Categories of data that affect report quality"""
    FUNNEL = "funnel"
    RETENTION = "retention"
    REVENUE = "revenue"
    UX_TESTING = "ux_testing"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    COMPETITIVE = "competitive"


@dataclass
class DataField:
    """A single data field that can be provided"""
    id: str
    name: str
    description: str
    category: DataCategory
    weight: int  # 1-10, how much this affects confidence
    required: bool = False
    example: str = ""
    how_to_get: str = ""


# =============================================================================
# ALL POSSIBLE DATA FIELDS
# =============================================================================

DATA_FIELDS = [
    # FUNNEL METRICS (Critical - 40% of total score)
    DataField(
        id="total_signups",
        name="Total Signups",
        description="Total number of user accounts created",
        category=DataCategory.FUNNEL,
        weight=10,
        required=True,
        example="2,012 users",
        how_to_get="SELECT COUNT(*) FROM users"
    ),
    DataField(
        id="email_verified",
        name="Email Verified Count",
        description="Users who completed email verification",
        category=DataCategory.FUNNEL,
        weight=9,
        required=True,
        example="1,543 users (76.7%)",
        how_to_get="SELECT COUNT(*) FROM users WHERE email_verified = true"
    ),
    DataField(
        id="profile_complete",
        name="Profile Completed",
        description="Users who finished profile setup",
        category=DataCategory.FUNNEL,
        weight=9,
        required=True,
        example="1,035 users (51.4%)",
        how_to_get="SELECT COUNT(*) FROM users WHERE profile_complete = true"
    ),
    DataField(
        id="first_action",
        name="First Key Action",
        description="Users who completed core action (booking, purchase, etc.)",
        category=DataCategory.FUNNEL,
        weight=10,
        required=True,
        example="19 users (0.9%)",
        how_to_get="SELECT COUNT(DISTINCT user_id) FROM transactions"
    ),
    DataField(
        id="page_views",
        name="Page View Data",
        description="Views per page/screen with unique users",
        category=DataCategory.FUNNEL,
        weight=7,
        example="Landing: 5,000 views, Signup: 2,500 views",
        how_to_get="Google Analytics > Behavior > Site Content"
    ),
    DataField(
        id="signup_sources",
        name="Signup Sources",
        description="Where users came from (organic, paid, referral)",
        category=DataCategory.FUNNEL,
        weight=6,
        example="Organic: 60%, Paid: 25%, Referral: 15%",
        how_to_get="Google Analytics > Acquisition > Source/Medium"
    ),

    # RETENTION METRICS (Important - 15% of total score)
    DataField(
        id="day1_retention",
        name="Day 1 Retention",
        description="% of users who return after 1 day",
        category=DataCategory.RETENTION,
        weight=8,
        example="25%",
        how_to_get="Analytics cohort report or custom query"
    ),
    DataField(
        id="day7_retention",
        name="Day 7 Retention",
        description="% of users who return after 7 days",
        category=DataCategory.RETENTION,
        weight=8,
        example="12%",
        how_to_get="Analytics cohort report"
    ),
    DataField(
        id="day30_retention",
        name="Day 30 Retention",
        description="% of users who return after 30 days",
        category=DataCategory.RETENTION,
        weight=9,
        example="5%",
        how_to_get="Analytics cohort report"
    ),
    DataField(
        id="churn_rate",
        name="Monthly Churn Rate",
        description="% of users who stop using the product",
        category=DataCategory.RETENTION,
        weight=7,
        example="8%",
        how_to_get="(Users at start - Users at end) / Users at start"
    ),

    # REVENUE METRICS (Important - 15% of total score)
    DataField(
        id="total_transactions",
        name="Total Transactions",
        description="Number of completed transactions/bookings",
        category=DataCategory.REVENUE,
        weight=8,
        example="19 transactions",
        how_to_get="SELECT COUNT(*) FROM transactions WHERE status = 'completed'"
    ),
    DataField(
        id="avg_transaction_value",
        name="Average Transaction Value",
        description="Average revenue per transaction",
        category=DataCategory.REVENUE,
        weight=7,
        example="$8.49",
        how_to_get="SELECT AVG(amount) FROM transactions"
    ),
    DataField(
        id="monthly_revenue",
        name="Monthly Revenue",
        description="Total revenue in the last 30 days",
        category=DataCategory.REVENUE,
        weight=8,
        example="$1,250",
        how_to_get="Payment processor dashboard or database query"
    ),
    DataField(
        id="ltv",
        name="Customer Lifetime Value",
        description="Average total revenue per customer",
        category=DataCategory.REVENUE,
        weight=6,
        example="$45",
        how_to_get="Total revenue / Total customers"
    ),
    DataField(
        id="cac",
        name="Customer Acquisition Cost",
        description="Cost to acquire one customer",
        category=DataCategory.REVENUE,
        weight=6,
        example="$12",
        how_to_get="Total marketing spend / New customers acquired"
    ),

    # UX TESTING (Critical - 20% of total score)
    DataField(
        id="screenshots",
        name="App Screenshots",
        description="Screenshots of all key screens/flows",
        category=DataCategory.UX_TESTING,
        weight=9,
        required=True,
        example="50-100 screenshots covering main flows",
        how_to_get="Manual capture using DevTools device mode"
    ),
    DataField(
        id="user_flows_documented",
        name="User Flows Documented",
        description="Step-by-step documentation of key user journeys",
        category=DataCategory.UX_TESTING,
        weight=8,
        example="Signup flow, Booking flow, Payment flow",
        how_to_get="Manual walkthrough and documentation"
    ),
    DataField(
        id="error_logs",
        name="Error/Crash Logs",
        description="Recent errors and their frequency",
        category=DataCategory.UX_TESTING,
        weight=6,
        example="Top 10 errors from last 30 days",
        how_to_get="Error tracking tool (Sentry, LogRocket, etc.)"
    ),
    DataField(
        id="session_recordings",
        name="Session Recordings",
        description="Video recordings of real user sessions",
        category=DataCategory.UX_TESTING,
        weight=7,
        example="100+ sessions from Hotjar/FullStory",
        how_to_get="Session recording tool"
    ),
    DataField(
        id="heatmaps",
        name="Click Heatmaps",
        description="Visual data showing where users click",
        category=DataCategory.UX_TESTING,
        weight=5,
        example="Heatmaps for top 10 pages",
        how_to_get="Hotjar, Crazy Egg, or similar"
    ),

    # TECHNICAL (Moderate - 5% of total score)
    DataField(
        id="tech_stack",
        name="Technology Stack",
        description="List of technologies used",
        category=DataCategory.TECHNICAL,
        weight=4,
        example="Angular, Node.js, PostgreSQL, AWS",
        how_to_get="Development team documentation"
    ),
    DataField(
        id="lighthouse_scores",
        name="Lighthouse Scores",
        description="Performance, accessibility, SEO scores",
        category=DataCategory.TECHNICAL,
        weight=6,
        example="Performance: 72, Accessibility: 85",
        how_to_get="Chrome DevTools > Lighthouse"
    ),
    DataField(
        id="api_response_times",
        name="API Response Times",
        description="Average response times for key endpoints",
        category=DataCategory.TECHNICAL,
        weight=5,
        example="Login: 200ms, Search: 450ms",
        how_to_get="APM tool or server logs"
    ),

    # MARKETING (Moderate - 5% of total score)
    DataField(
        id="marketing_channels",
        name="Marketing Channels",
        description="Active marketing channels and spend",
        category=DataCategory.MARKETING,
        weight=5,
        example="Google Ads: $500/mo, Facebook: $300/mo",
        how_to_get="Marketing team/ads dashboard"
    ),
    DataField(
        id="conversion_by_channel",
        name="Conversion by Channel",
        description="Conversion rates per acquisition channel",
        category=DataCategory.MARKETING,
        weight=6,
        example="Organic: 2.1%, Paid: 1.5%",
        how_to_get="Google Analytics > Conversions"
    ),
    DataField(
        id="nps_score",
        name="NPS Score",
        description="Net Promoter Score from user surveys",
        category=DataCategory.MARKETING,
        weight=5,
        example="NPS: 42",
        how_to_get="User surveys or feedback tool"
    ),

    # COMPETITIVE (Nice to have - 0% required but adds context)
    DataField(
        id="competitors",
        name="Competitor List",
        description="Main competitors and their strengths",
        category=DataCategory.COMPETITIVE,
        weight=3,
        example="Competitor A (larger), Competitor B (cheaper)",
        how_to_get="Market research"
    ),
    DataField(
        id="market_position",
        name="Market Position",
        description="Your positioning vs competitors",
        category=DataCategory.COMPETITIVE,
        weight=3,
        example="Premium tier, local focus",
        how_to_get="Internal strategy documents"
    ),
]


# =============================================================================
# CONFIDENCE CALCULATOR
# =============================================================================

@dataclass
class ConfidenceResult:
    """Result of confidence calculation"""
    overall_score: int  # 0-100
    category_scores: Dict[str, int]  # Score per category
    provided_fields: List[str]  # Fields that have data
    missing_fields: List[DataField]  # Fields without data
    critical_missing: List[DataField]  # Required fields without data
    improvement_suggestions: List[Dict[str, Any]]  # How to improve
    confidence_level: str  # "High", "Medium", "Low", "Very Low"
    report_reliability: str  # Description of what this means


class DataConfidenceCalculator:
    """Calculate confidence scores based on provided data"""

    # Category weights (must sum to 100)
    CATEGORY_WEIGHTS = {
        DataCategory.FUNNEL: 40,
        DataCategory.RETENTION: 15,
        DataCategory.REVENUE: 15,
        DataCategory.UX_TESTING: 20,
        DataCategory.TECHNICAL: 5,
        DataCategory.MARKETING: 5,
        DataCategory.COMPETITIVE: 0,  # Nice to have, doesn't affect score
    }

    def __init__(self, fields: List[DataField] = None):
        self.fields = fields or DATA_FIELDS
        self.fields_by_id = {f.id: f for f in self.fields}
        self.fields_by_category = {}
        for f in self.fields:
            if f.category not in self.fields_by_category:
                self.fields_by_category[f.category] = []
            self.fields_by_category[f.category].append(f)

    def calculate(self, provided_data: Dict[str, Any]) -> ConfidenceResult:
        """
        Calculate confidence score based on provided data

        Args:
            provided_data: Dict with field IDs as keys, data as values
                          Use None or empty value to indicate missing data

        Returns:
            ConfidenceResult with scores and suggestions
        """
        provided_fields = []
        missing_fields = []
        critical_missing = []
        category_scores = {}

        # Calculate score for each category
        for category, weight in self.CATEGORY_WEIGHTS.items():
            category_fields = self.fields_by_category.get(category, [])
            if not category_fields:
                category_scores[category.value] = 100
                continue

            total_weight = sum(f.weight for f in category_fields)
            achieved_weight = 0

            for field in category_fields:
                has_data = self._has_data(provided_data.get(field.id))
                if has_data:
                    provided_fields.append(field.id)
                    achieved_weight += field.weight
                else:
                    missing_fields.append(field)
                    if field.required:
                        critical_missing.append(field)

            category_score = int((achieved_weight / total_weight) * 100) if total_weight > 0 else 0
            category_scores[category.value] = category_score

        # Calculate overall score (weighted average)
        overall_score = 0
        for category, weight in self.CATEGORY_WEIGHTS.items():
            category_score = category_scores.get(category.value, 0)
            overall_score += (category_score * weight / 100)

        overall_score = int(overall_score)

        # Determine confidence level
        if overall_score >= 80:
            confidence_level = "High"
            report_reliability = "Recommendations are data-backed with high confidence. ROI projections are reliable."
        elif overall_score >= 60:
            confidence_level = "Medium"
            report_reliability = "Recommendations are reasonably confident but some assumptions are made. ROI projections are estimates."
        elif overall_score >= 40:
            confidence_level = "Low"
            report_reliability = "Recommendations are based on limited data. Consider them directional guidance rather than definitive."
        else:
            confidence_level = "Very Low"
            report_reliability = "Insufficient data for reliable analysis. Recommendations are speculative and require validation."

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(missing_fields, category_scores)

        return ConfidenceResult(
            overall_score=overall_score,
            category_scores=category_scores,
            provided_fields=provided_fields,
            missing_fields=missing_fields,
            critical_missing=critical_missing,
            improvement_suggestions=suggestions,
            confidence_level=confidence_level,
            report_reliability=report_reliability
        )

    def _has_data(self, value: Any) -> bool:
        """Check if a value represents actual data"""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False  # 0 might be valid, but usually indicates missing
        return True

    def _generate_suggestions(
        self,
        missing_fields: List[DataField],
        category_scores: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized suggestions for improving confidence"""
        suggestions = []

        # Sort missing fields by weight (highest impact first)
        sorted_missing = sorted(missing_fields, key=lambda f: f.weight, reverse=True)

        # Find lowest scoring categories
        lowest_categories = sorted(category_scores.items(), key=lambda x: x[1])[:3]

        for field in sorted_missing[:10]:  # Top 10 suggestions
            impact = "HIGH" if field.weight >= 8 else "MEDIUM" if field.weight >= 5 else "LOW"
            score_boost = field.weight * 2  # Rough estimate of score improvement

            suggestions.append({
                'field': field.name,
                'description': field.description,
                'impact': impact,
                'score_boost': f"+{score_boost}%",
                'how_to_get': field.how_to_get,
                'example': field.example,
                'category': field.category.value,
                'required': field.required
            })

        return suggestions

    def get_intake_form(self) -> Dict[str, Any]:
        """Generate a client intake form structure"""
        form = {
            'title': 'Audit Data Intake Form',
            'description': 'The more data you provide, the more accurate and actionable our recommendations will be.',
            'sections': []
        }

        for category in DataCategory:
            fields = self.fields_by_category.get(category, [])
            if not fields:
                continue

            section = {
                'category': category.value,
                'title': category.value.replace('_', ' ').title(),
                'weight': f"{self.CATEGORY_WEIGHTS[category]}% of confidence score",
                'fields': []
            }

            for field in fields:
                section['fields'].append({
                    'id': field.id,
                    'name': field.name,
                    'description': field.description,
                    'required': field.required,
                    'example': field.example,
                    'how_to_get': field.how_to_get,
                    'impact': 'High' if field.weight >= 8 else 'Medium' if field.weight >= 5 else 'Low'
                })

            form['sections'].append(section)

        return form


# =============================================================================
# CONFIDENCE DISPLAY GENERATORS
# =============================================================================

def generate_confidence_html(result: ConfidenceResult) -> str:
    """Generate HTML section showing confidence score and suggestions"""

    # Color based on score
    if result.overall_score >= 80:
        color = "#10B981"
        bg = "#D1FAE5"
    elif result.overall_score >= 60:
        color = "#F59E0B"
        bg = "#FEF3C7"
    elif result.overall_score >= 40:
        color = "#F97316"
        bg = "#FFEDD5"
    else:
        color = "#EF4444"
        bg = "#FEE2E2"

    # Category bars
    category_bars = ""
    for category, score in result.category_scores.items():
        cat_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"
        category_bars += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                <span>{category.replace('_', ' ').title()}</span>
                <span style="font-weight: 600; color: {cat_color};">{score}%</span>
            </div>
            <div style="height: 8px; background: #E2E8F0; border-radius: 4px; overflow: hidden;">
                <div style="width: {score}%; height: 100%; background: {cat_color}; border-radius: 4px;"></div>
            </div>
        </div>
        """

    # Suggestions list
    suggestions_html = ""
    for i, sug in enumerate(result.improvement_suggestions[:5], 1):
        impact_color = "#DC2626" if sug['impact'] == 'HIGH' else "#D97706" if sug['impact'] == 'MEDIUM' else "#2563EB"
        required_badge = '<span style="background: #FEE2E2; color: #DC2626; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; margin-left: 8px;">REQUIRED</span>' if sug['required'] else ''

        suggestions_html += f"""
        <div style="background: #F8FAFC; border-radius: 12px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <div style="font-weight: 600; color: #0F172A; margin-bottom: 4px;">
                        {i}. {sug['field']}{required_badge}
                    </div>
                    <div style="font-size: 13px; color: #64748B; margin-bottom: 8px;">{sug['description']}</div>
                    <div style="font-size: 12px; color: #94A3B8;">
                        <strong>How to get:</strong> {sug['how_to_get']}
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="background: {impact_color}20; color: {impact_color}; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{sug['impact']} IMPACT</span>
                    <div style="font-size: 12px; color: #10B981; margin-top: 4px; font-weight: 600;">{sug['score_boost']}</div>
                </div>
            </div>
        </div>
        """

    # Critical missing warning
    critical_warning = ""
    if result.critical_missing:
        critical_list = ", ".join([f.name for f in result.critical_missing[:3]])
        critical_warning = f"""
        <div style="background: #FEE2E2; border: 1px solid #FECACA; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
            <div style="font-weight: 700; color: #991B1B; margin-bottom: 8px;">&#9888; Missing Required Data</div>
            <div style="font-size: 14px; color: #7F1D1D;">
                The following required fields are missing: <strong>{critical_list}</strong>
                <br>Without this data, recommendations may not be reliable.
            </div>
        </div>
        """

    return f"""
    <div style="background: white; border-radius: 24px; padding: 48px; margin-bottom: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.04);">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
            <div style="width: 52px; height: 52px; background: linear-gradient(135deg, {color}, {color}CC); border-radius: 16px; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px;">
                &#128202;
            </div>
            <h2 style="font-size: 28px; font-weight: 700; color: #0F172A;">Data Confidence Score</h2>
        </div>

        <p style="font-size: 17px; color: #64748B; margin-bottom: 32px; line-height: 1.7;">
            This score reflects the completeness and quality of the data used in this audit.
            Higher scores mean more reliable recommendations.
        </p>

        {critical_warning}

        <!-- Score Display -->
        <div style="display: grid; grid-template-columns: 200px 1fr; gap: 40px; margin-bottom: 32px;">
            <div style="text-align: center; background: {bg}; border-radius: 20px; padding: 32px;">
                <div style="font-size: 64px; font-weight: 800; color: {color};">{result.overall_score}</div>
                <div style="font-size: 14px; color: {color}; font-weight: 600;">OUT OF 100</div>
                <div style="margin-top: 12px; padding: 8px 16px; background: {color}; color: white; border-radius: 20px; font-size: 13px; font-weight: 600;">
                    {result.confidence_level} Confidence
                </div>
            </div>
            <div>
                <div style="font-size: 15px; color: #64748B; margin-bottom: 20px;">
                    {result.report_reliability}
                </div>
                {category_bars}
            </div>
        </div>

        <!-- How to Improve -->
        <div style="border-top: 1px solid #E2E8F0; padding-top: 32px;">
            <h3 style="font-size: 20px; font-weight: 700; color: #0F172A; margin-bottom: 16px;">
                &#128200; How to Improve Confidence
            </h3>
            <p style="font-size: 14px; color: #64748B; margin-bottom: 20px;">
                Provide these data points to increase the accuracy of our recommendations:
            </p>
            {suggestions_html}
        </div>
    </div>
    """


def generate_confidence_markdown(result: ConfidenceResult) -> str:
    """Generate markdown section showing confidence score"""

    lines = [
        "## Data Confidence Score",
        "",
        f"**Overall Score: {result.overall_score}/100** ({result.confidence_level} Confidence)",
        "",
        f"> {result.report_reliability}",
        "",
        "### Category Breakdown",
        "",
        "| Category | Score | Status |",
        "|----------|-------|--------|"
    ]

    for category, score in result.category_scores.items():
        status = "Good" if score >= 70 else "Needs Data" if score >= 50 else "Missing Data"
        lines.append(f"| {category.replace('_', ' ').title()} | {score}% | {status} |")

    if result.critical_missing:
        lines.append("")
        lines.append("### Missing Required Data")
        lines.append("")
        for field in result.critical_missing:
            lines.append(f"- **{field.name}**: {field.description}")
            lines.append(f"  - How to get: {field.how_to_get}")

    if result.improvement_suggestions:
        lines.append("")
        lines.append("### How to Improve Confidence")
        lines.append("")
        for i, sug in enumerate(result.improvement_suggestions[:5], 1):
            required = " (REQUIRED)" if sug['required'] else ""
            lines.append(f"{i}. **{sug['field']}**{required} - {sug['impact']} impact ({sug['score_boost']})")
            lines.append(f"   - {sug['description']}")
            lines.append(f"   - How to get: {sug['how_to_get']}")
            lines.append("")

    return "\n".join(lines)


def generate_intake_form_markdown() -> str:
    """Generate a client intake form in markdown"""
    calc = DataConfidenceCalculator()
    form = calc.get_intake_form()

    lines = [
        f"# {form['title']}",
        "",
        form['description'],
        "",
        "---",
        ""
    ]

    for section in form['sections']:
        lines.append(f"## {section['title']}")
        lines.append(f"*{section['weight']}*")
        lines.append("")

        for field in section['fields']:
            required = " **(REQUIRED)**" if field['required'] else ""
            impact = f"[{field['impact']} Impact]"

            lines.append(f"### {field['name']}{required} {impact}")
            lines.append(f"{field['description']}")
            lines.append("")
            lines.append(f"- **Example**: {field['example']}")
            lines.append(f"- **How to get**: {field['how_to_get']}")
            lines.append("")
            lines.append("**Your data**: _________________")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    """Demo the confidence calculator"""
    import json

    # Example: JuiceNet with partial data
    juicenet_data = {
        'total_signups': 2012,
        'email_verified': 1543,
        'profile_complete': 1035,
        'first_action': 19,
        'screenshots': True,  # They have screenshots
        'user_flows_documented': True,
        'total_transactions': 19,
        'avg_transaction_value': 8.49,
        # Missing: retention data, marketing data, session recordings, etc.
    }

    calc = DataConfidenceCalculator()
    result = calc.calculate(juicenet_data)

    print("=" * 60)
    print("DATA CONFIDENCE ANALYSIS")
    print("=" * 60)
    print(f"\nOverall Score: {result.overall_score}/100 ({result.confidence_level})")
    print(f"\n{result.report_reliability}")
    print("\nCategory Scores:")
    for cat, score in result.category_scores.items():
        print(f"  {cat}: {score}%")

    if result.critical_missing:
        print("\nMISSING REQUIRED DATA:")
        for field in result.critical_missing:
            print(f"  - {field.name}")

    print("\nTOP SUGGESTIONS TO IMPROVE CONFIDENCE:")
    for i, sug in enumerate(result.improvement_suggestions[:5], 1):
        print(f"  {i}. {sug['field']} ({sug['impact']}) - {sug['score_boost']}")

    # Generate intake form
    print("\n" + "=" * 60)
    print("Generating intake form...")
    intake_md = generate_intake_form_markdown()
    with open("CLIENT_DATA_INTAKE.md", 'w', encoding='utf-8') as f:
        f.write(intake_md)
    print("Saved to: CLIENT_DATA_INTAKE.md")


if __name__ == "__main__":
    main()
