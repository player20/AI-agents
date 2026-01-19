"""
Report Review & Customization Module

Provides an interactive review step before generating the final report.
Works with ANY audit type - fully modular.

Users can:
- Choose audit type (UX, Marketing, Business, Technical, Custom)
- Toggle sections on/off
- Edit metrics, issues, recommendations
- Customize before publishing
"""

import streamlit as st
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import json


# ============================================
# Legacy ReportConfig classes for 4_Report_Review.py compatibility
# ============================================

@dataclass
class ReportSection:
    """A section that can be toggled on/off."""
    id: str
    title: str
    enabled: bool = True
    content: str = ""
    editable: bool = True


@dataclass
class Recommendation:
    """A recommendation that can be included/excluded."""
    id: str
    priority: int
    title: str
    description: str
    impact: str
    effort: str
    enabled: bool = True
    editable: bool = True


@dataclass
class UXIssue:
    """A UX issue that can be included/excluded."""
    id: str
    title: str
    severity: str  # critical, high, medium, low
    description: str
    impact: str
    enabled: bool = True


@dataclass
class ReportConfig:
    """Complete report configuration for review."""
    app_name: str = "Business App"
    tagline: str = "Your Business Tagline"
    audit_date: str = "January 2026"

    # Sections
    sections: Dict[str, ReportSection] = field(default_factory=dict)

    # Content
    recommendations: List[Recommendation] = field(default_factory=list)
    ux_issues: List[UXIssue] = field(default_factory=list)

    # Metrics (editable)
    metrics: Dict[str, Any] = field(default_factory=dict)

    # KPIs (editable targets)
    kpis: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def create_default_config() -> ReportConfig:
    """Create default report configuration."""
    config = ReportConfig()

    # Define default sections
    config.sections = {
        "executive": ReportSection(
            id="executive",
            title="Executive Summary",
            enabled=True,
            content="Critical metrics and bottom line analysis"
        ),
        "funnel": ReportSection(
            id="funnel",
            title="Funnel Analysis",
            enabled=True,
            content="User acquisition funnel with drop-off points"
        ),
        "ux_issues": ReportSection(
            id="ux_issues",
            title="UX Issues",
            enabled=True,
            content="Identified user experience problems"
        ),
        "recommendations": ReportSection(
            id="recommendations",
            title="Recommendations",
            enabled=True,
            content="Prioritized action items"
        ),
        "roi": ReportSection(
            id="roi",
            title="ROI Projections",
            enabled=True,
            content="Conservative and optimistic estimates"
        ),
    }

    # Default recommendations
    config.recommendations = [
        Recommendation(
            id="r1",
            priority=1,
            title="Improve Onboarding Flow",
            description="Streamline the user onboarding experience",
            impact="High",
            effort="Medium"
        ),
        Recommendation(
            id="r2",
            priority=2,
            title="Enhance Mobile Experience",
            description="Optimize for mobile users",
            impact="High",
            effort="Medium"
        ),
        Recommendation(
            id="r3",
            priority=3,
            title="Add Progress Indicators",
            description="Show users their progress through key flows",
            impact="Medium",
            effort="Low"
        ),
    ]

    # Default metrics
    config.metrics = {
        "total_signups": 1000,
        "email_verified": 750,
        "profile_complete": 500,
        "reservations": 100,
        "total_hosts": 50,
        "hosts_with_chargers": 30,
    }

    # Default KPIs
    config.kpis = {
        "signup_to_verified": {"current": 75.0, "target_30d": 80.0, "target_90d": 85.0},
        "verified_to_profile": {"current": 66.7, "target_30d": 75.0, "target_90d": 80.0},
        "overall_conversion": {"current": 10.0, "target_30d": 15.0, "target_90d": 20.0},
    }

    return config


def save_config(config: ReportConfig, path: str):
    """Save config to JSON file."""
    data = {
        "app_name": config.app_name,
        "tagline": config.tagline,
        "audit_date": config.audit_date,
        "sections": {k: {"id": v.id, "title": v.title, "enabled": v.enabled, "content": v.content}
                     for k, v in config.sections.items()},
        "recommendations": [{"id": r.id, "priority": r.priority, "title": r.title,
                            "description": r.description, "impact": r.impact,
                            "effort": r.effort, "enabled": r.enabled}
                           for r in config.recommendations],
        "ux_issues": [{"id": i.id, "title": i.title, "severity": i.severity,
                       "description": i.description, "impact": i.impact, "enabled": i.enabled}
                      for i in config.ux_issues],
        "metrics": config.metrics,
        "kpis": config.kpis,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_config(path: str) -> ReportConfig:
    """Load config from JSON file."""
    with open(path, "r") as f:
        data = json.load(f)

    config = ReportConfig(
        app_name=data.get("app_name", "Business App"),
        tagline=data.get("tagline", ""),
        audit_date=data.get("audit_date", "")
    )

    # Load sections
    for k, v in data.get("sections", {}).items():
        config.sections[k] = ReportSection(**v)

    # Load recommendations
    for r in data.get("recommendations", []):
        config.recommendations.append(Recommendation(**r))

    # Load issues
    for i in data.get("ux_issues", []):
        config.ux_issues.append(UXIssue(**i))

    config.metrics = data.get("metrics", {})
    config.kpis = data.get("kpis", {})

    return config


# ============================================
# Modern AuditData-based functionality
# ============================================

from audit_data import (
    AuditData,
    AuditType,
    Metric,
    Issue,
    Recommendation,
    ReportSection,
    DataConfidence,
    get_sections_for_type,
    NIELSENS_HEURISTICS,
    MARKETING_SCORE_CATEGORIES,
    TECHNICAL_SCORE_CATEGORIES
)
from data_loader import (
    create_audit,
    save_to_json,
    load_from_json,
    create_ux_audit,
    create_marketing_audit,
    create_business_audit,
    create_technical_audit
)


def render_audit_type_selector() -> AuditType:
    """Render audit type selection."""
    st.subheader("Select Audit Type")

    audit_types = {
        "UX / App Audit": AuditType.UX_APP,
        "Marketing Audit": AuditType.MARKETING,
        "Business Model Audit": AuditType.BUSINESS,
        "Technical Audit": AuditType.TECHNICAL,
        "Custom Audit": AuditType.CUSTOM,
    }

    selected = st.selectbox(
        "What type of audit are you creating?",
        options=list(audit_types.keys()),
        key="audit_type_selector"
    )

    return audit_types[selected]


def render_basic_info(data: AuditData) -> AuditData:
    """Render basic information fields."""
    st.subheader("Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        data.name = st.text_input("Business/App Name", value=data.name, key="basic_name")
        data.tagline = st.text_input("Tagline", value=data.tagline, key="basic_tagline")
        data.audit_date = st.text_input("Audit Date", value=data.audit_date, key="basic_date")

    with col2:
        data.company_name = st.text_input("Company Name", value=data.company_name, key="basic_company")
        data.business_model = st.text_input("Business Model", value=data.business_model, key="basic_model")
        data.auditor = st.text_input("Auditor", value=data.auditor, key="basic_auditor")

    data.executive_summary = st.text_area(
        "Executive Summary",
        value=data.executive_summary,
        key="basic_summary",
        height=100,
        help="Brief overview of the audit findings"
    )

    return data


def render_sections_tab(data: AuditData) -> AuditData:
    """Render sections toggle tab."""
    st.subheader("Report Sections")
    st.markdown("Toggle which sections to include in the final report.")

    if not data.sections:
        st.info("No sections defined. Add sections below or select an audit type with default sections.")

        # Add new section
        with st.expander("+ Add New Section"):
            new_id = st.text_input("Section ID", key="new_section_id")
            new_title = st.text_input("Section Title", key="new_section_title")
            new_desc = st.text_area("Description", key="new_section_desc")

            if st.button("Add Section") and new_id and new_title:
                data.add_section(ReportSection(
                    id=new_id,
                    title=new_title,
                    description=new_desc,
                    order=len(data.sections) + 1
                ))
                st.rerun()
    else:
        # Display existing sections
        col1, col2 = st.columns(2)
        sections = sorted(data.sections, key=lambda x: x.order)
        mid = len(sections) // 2

        with col1:
            for section in sections[:mid]:
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"section_{section.id}",
                    help=section.description
                )

        with col2:
            for section in sections[mid:]:
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"section_{section.id}",
                    help=section.description
                )

    return data


def render_metrics_tab(data: AuditData) -> AuditData:
    """Render metrics editing tab."""
    st.subheader("Metrics")

    # Group metrics by category
    categories = list(set(m.category for m in data.metrics))

    if not categories:
        st.info("No metrics defined yet. Add metrics below.")
    else:
        for category in sorted(categories):
            with st.expander(f"📊 {category.replace('_', ' ').title()}", expanded=True):
                metrics = data.get_metrics_by_category(category)

                for metric in metrics:
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                    with col1:
                        metric.name = st.text_input(
                            "Name",
                            value=metric.name,
                            key=f"metric_name_{metric.id}",
                            label_visibility="collapsed"
                        )

                    with col2:
                        metric.value = st.number_input(
                            "Value",
                            value=float(metric.value),
                            key=f"metric_value_{metric.id}",
                            label_visibility="collapsed"
                        )

                    with col3:
                        metric.unit = st.text_input(
                            "Unit",
                            value=metric.unit,
                            key=f"metric_unit_{metric.id}",
                            label_visibility="collapsed"
                        )

                    with col4:
                        confidence_display = {
                            DataConfidence.VERIFIED: "✅",
                            DataConfidence.ESTIMATED: "🔶",
                            DataConfidence.PLACEHOLDER: "⚪"
                        }
                        st.markdown(f"**{confidence_display.get(metric.confidence, '⚪')}**")

    # Add new metric
    with st.expander("+ Add New Metric"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Metric Name", key="new_metric_name")
            new_value = st.number_input("Value", key="new_metric_value")
        with col2:
            new_category = st.text_input("Category", value="general", key="new_metric_category")
            new_unit = st.text_input("Unit", key="new_metric_unit")

        if st.button("Add Metric") and new_name:
            data.add_metric(Metric(
                id=f"m_{len(data.metrics) + 1}",
                name=new_name,
                value=new_value,
                category=new_category,
                unit=new_unit,
                confidence=DataConfidence.PLACEHOLDER,
                order=len(data.metrics) + 1
            ))
            st.rerun()

    return data


def render_issues_tab(data: AuditData) -> AuditData:
    """Render issues editing tab."""
    st.subheader("Issues Found")

    if not data.issues:
        st.info("No issues defined yet. Add issues below.")
    else:
        for issue in data.issues:
            severity_badge = {
                "critical": "🔴 CRITICAL",
                "high": "🟠 HIGH",
                "medium": "🟡 MEDIUM",
                "low": "🟢 LOW"
            }

            col1, col2, col3 = st.columns([0.5, 4, 1.5])

            with col1:
                issue.enabled = st.checkbox(
                    "",
                    value=issue.enabled,
                    key=f"issue_{issue.id}",
                    label_visibility="collapsed"
                )

            with col2:
                if issue.enabled:
                    with st.expander(f"**{issue.title}**", expanded=False):
                        issue.title = st.text_input("Title", value=issue.title, key=f"issue_title_{issue.id}")
                        issue.description = st.text_area("Description", value=issue.description, key=f"issue_desc_{issue.id}")
                        issue.impact = st.text_input("Impact", value=issue.impact, key=f"issue_impact_{issue.id}")
                        issue.severity = st.selectbox(
                            "Severity",
                            options=["critical", "high", "medium", "low"],
                            index=["critical", "high", "medium", "low"].index(issue.severity),
                            key=f"issue_severity_{issue.id}"
                        )
                else:
                    st.markdown(f"~~{issue.title}~~")

            with col3:
                st.markdown(severity_badge.get(issue.severity, ""))

    # Add new issue
    with st.expander("+ Add New Issue"):
        new_title = st.text_input("Issue Title", key="new_issue_title")
        new_desc = st.text_area("Description", key="new_issue_desc")
        col1, col2 = st.columns(2)
        with col1:
            new_severity = st.selectbox("Severity", ["critical", "high", "medium", "low"], key="new_issue_severity")
        with col2:
            new_impact = st.text_input("Impact", key="new_issue_impact")

        if st.button("Add Issue") and new_title:
            data.add_issue(Issue(
                id=f"i_{len(data.issues) + 1}",
                title=new_title,
                description=new_desc,
                severity=new_severity,
                impact=new_impact
            ))
            st.rerun()

    return data


def render_recommendations_tab(data: AuditData) -> AuditData:
    """Render recommendations editing tab."""
    st.subheader("Recommendations")
    st.markdown("Select and edit recommendations to include in the report.")

    # Quick actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Enable All"):
            for rec in data.recommendations:
                rec.enabled = True
            st.rerun()
    with col2:
        if st.button("❌ Disable All"):
            for rec in data.recommendations:
                rec.enabled = False
            st.rerun()
    with col3:
        if st.button("🔝 Top 3 Only"):
            for rec in data.recommendations:
                rec.enabled = rec.priority <= 3
            st.rerun()

    st.markdown("---")

    if not data.recommendations:
        st.info("No recommendations defined yet. Add recommendations below.")
    else:
        for rec in sorted(data.recommendations, key=lambda x: x.priority):
            priority_color = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "🔵", 6: "🟣", 7: "⚪"}

            col1, col2 = st.columns([0.5, 9.5])

            with col1:
                rec.enabled = st.checkbox(
                    "",
                    value=rec.enabled,
                    key=f"rec_{rec.id}",
                    label_visibility="collapsed"
                )

            with col2:
                with st.expander(f"{priority_color.get(rec.priority, '⚪')} P{rec.priority}: {rec.title}"):
                    if rec.enabled:
                        rec.title = st.text_input("Title", value=rec.title, key=f"rec_title_{rec.id}")
                        rec.description = st.text_area("Description", value=rec.description, key=f"rec_desc_{rec.id}", height=80)

                        col1, col2 = st.columns(2)
                        with col1:
                            rec.impact = st.text_input("Impact", value=rec.impact, key=f"rec_impact_{rec.id}")
                            rec.priority = st.number_input("Priority", value=rec.priority, min_value=1, key=f"rec_priority_{rec.id}")
                        with col2:
                            rec.effort = st.text_input("Effort", value=rec.effort, key=f"rec_effort_{rec.id}")
                            rec.roi_estimate = st.text_input("ROI Estimate", value=rec.roi_estimate or "", key=f"rec_roi_{rec.id}")
                    else:
                        st.caption("Excluded from report")

    # Add new recommendation
    with st.expander("+ Add New Recommendation"):
        new_title = st.text_input("Title", key="new_rec_title")
        new_desc = st.text_area("Description", key="new_rec_desc")
        col1, col2 = st.columns(2)
        with col1:
            new_priority = st.number_input("Priority", value=len(data.recommendations) + 1, min_value=1, key="new_rec_priority")
            new_impact = st.text_input("Impact", key="new_rec_impact")
        with col2:
            new_effort = st.text_input("Effort", key="new_rec_effort")
            new_category = st.text_input("Category", key="new_rec_category")

        if st.button("Add Recommendation") and new_title:
            data.add_recommendation(Recommendation(
                id=f"r_{len(data.recommendations) + 1}",
                title=new_title,
                description=new_desc,
                priority=new_priority,
                impact=new_impact,
                effort=new_effort,
                category=new_category
            ))
            st.rerun()

    return data


def render_scores_tab(data: AuditData) -> AuditData:
    """Render scores/heuristics tab."""
    st.subheader("Scoring")

    if not data.scores:
        # Offer to add default scores based on audit type
        st.info("No scores defined. Add scoring criteria below or use defaults.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Add Nielsen's Heuristics"):
                data.scores = {h: 5 for h in NIELSENS_HEURISTICS}
                st.rerun()
        with col2:
            if st.button("Add Marketing Scores"):
                data.scores = {c: 5 for c in MARKETING_SCORE_CATEGORIES}
                st.rerun()
        with col3:
            if st.button("Add Technical Scores"):
                data.scores = {c: 5 for c in TECHNICAL_SCORE_CATEGORIES}
                st.rerun()
    else:
        st.markdown("Rate each criterion from 1-10:")

        for criterion, score in data.scores.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{criterion}**")
            with col2:
                data.scores[criterion] = st.slider(
                    criterion,
                    min_value=1,
                    max_value=10,
                    value=score,
                    key=f"score_{criterion}",
                    label_visibility="collapsed"
                )

        # Calculate average
        avg_score = sum(data.scores.values()) / len(data.scores)
        st.metric("Average Score", f"{avg_score:.1f}/10")

    return data


def render_preview_tab(data: AuditData):
    """Render preview of what will be generated."""
    st.subheader("Report Preview")

    # Summary metrics
    enabled_sections = data.get_enabled_sections()
    enabled_recs = data.get_enabled_recommendations()
    enabled_issues = data.get_enabled_issues()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sections", len(enabled_sections))
    with col2:
        st.metric("Metrics", len(data.metrics))
    with col3:
        st.metric("Issues", len(enabled_issues))
    with col4:
        st.metric("Recommendations", len(enabled_recs))

    # Confidence indicator
    confidence_display = {
        DataConfidence.VERIFIED: ("✅ Verified", "All data from real sources"),
        DataConfidence.ESTIMATED: ("🔶 Estimated", "Some data calculated or inferred"),
        DataConfidence.PLACEHOLDER: ("⚪ Placeholder", "Sample data - replace with real values")
    }
    conf_label, conf_desc = confidence_display.get(data.overall_confidence, ("❓", "Unknown"))
    st.info(f"**Data Confidence:** {conf_label} - {conf_desc}")

    st.markdown("---")

    # Preview content
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Sections:**")
        for section in enabled_sections:
            st.markdown(f"- {section.title}")

        st.markdown("**Metrics:**")
        for metric in data.metrics[:5]:  # Show first 5
            st.markdown(f"- {metric.name}: {metric.value} {metric.unit}")
        if len(data.metrics) > 5:
            st.caption(f"...and {len(data.metrics) - 5} more")

    with col2:
        st.markdown("**Issues:**")
        for issue in enabled_issues[:5]:
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            st.markdown(f"- {severity_emoji.get(issue.severity, '')} {issue.title}")
        if len(enabled_issues) > 5:
            st.caption(f"...and {len(enabled_issues) - 5} more")

        st.markdown("**Recommendations:**")
        for rec in enabled_recs[:5]:
            st.markdown(f"- **P{rec.priority}**: {rec.title}")
        if len(enabled_recs) > 5:
            st.caption(f"...and {len(enabled_recs) - 5} more")


def render_review_ui(data: AuditData) -> AuditData:
    """
    Main review UI renderer.

    Args:
        data: AuditData to review and edit

    Returns:
        Updated AuditData
    """
    st.title("📝 Review & Customize Report")
    st.markdown("Review and customize the audit data before generating the final report.")

    # Show audit type
    audit_type_display = {
        AuditType.UX_APP: "🎨 UX / App Audit",
        AuditType.MARKETING: "📢 Marketing Audit",
        AuditType.BUSINESS: "💼 Business Model Audit",
        AuditType.TECHNICAL: "⚙️ Technical Audit",
        AuditType.CUSTOM: "🔧 Custom Audit"
    }
    st.caption(f"Audit Type: {audit_type_display.get(data.audit_type, 'Custom')}")

    # Tabs
    tabs = st.tabs([
        "📋 Basic Info",
        "📑 Sections",
        "📊 Metrics",
        "⚠️ Issues",
        "💡 Recommendations",
        "📈 Scores",
        "👁️ Preview"
    ])

    with tabs[0]:
        data = render_basic_info(data)

    with tabs[1]:
        data = render_sections_tab(data)

    with tabs[2]:
        data = render_metrics_tab(data)

    with tabs[3]:
        data = render_issues_tab(data)

    with tabs[4]:
        data = render_recommendations_tab(data)

    with tabs[5]:
        data = render_scores_tab(data)

    with tabs[6]:
        render_preview_tab(data)

    # Update confidence
    data.overall_confidence = data.calculate_confidence()

    return data


def main():
    """Standalone page for report review."""
    st.set_page_config(
        page_title="Report Review - Weaver Pro",
        page_icon="📝",
        layout="wide"
    )

    # Sidebar - audit type selection and actions
    with st.sidebar:
        st.header("Audit Setup")

        # Create new or load existing
        action = st.radio(
            "Action",
            ["Create New Audit", "Load Existing"],
            key="action_selector"
        )

        if action == "Create New Audit":
            audit_type = render_audit_type_selector()
            name = st.text_input("Business/App Name", value="My Business", key="new_audit_name")
            include_samples = st.checkbox("Include sample data", value=False, key="include_samples")

            if st.button("Create Audit", type="primary"):
                st.session_state.audit_data = create_audit(name, audit_type, include_samples)
                st.rerun()

        else:
            uploaded = st.file_uploader("Upload JSON config", type=["json"], key="upload_config")
            if uploaded:
                try:
                    content = json.load(uploaded)
                    st.session_state.audit_data = AuditData.from_dict(content)
                    st.success("Config loaded!")
                except Exception as e:
                    st.error(f"Error loading config: {e}")

        st.markdown("---")
        st.subheader("Quick Actions")

        if st.button("💾 Save Config"):
            if "audit_data" in st.session_state:
                save_to_json(st.session_state.audit_data, "audit_config.json")
                st.success("Saved to audit_config.json")

        if st.button("🔄 Reset to Defaults"):
            if "audit_data" in st.session_state:
                audit_type = st.session_state.audit_data.audit_type
                st.session_state.audit_data = create_audit(
                    st.session_state.audit_data.name,
                    audit_type,
                    include_samples=True
                )
                st.rerun()

    # Main content
    if "audit_data" not in st.session_state:
        st.info("👈 Create a new audit or load an existing configuration from the sidebar.")
        return

    # Render review UI
    data = render_review_ui(st.session_state.audit_data)
    st.session_state.audit_data = data

    # Generate button
    st.markdown("---")
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("📄 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Generating report..."):
                try:
                    # Import the report generator
                    from comprehensive_shareable_report import ComprehensiveShareableReport

                    report = ComprehensiveShareableReport(data)
                    output_path = report.save()

                    st.success(f"Report generated: {output_path}")
                    st.markdown("**Deploy:** Drag to https://app.netlify.com/drop")
                except Exception as e:
                    st.error(f"Error generating report: {e}")


if __name__ == "__main__":
    main()
