"""
Report Review & Customization Module

Provides an interactive review step before generating the final report.
Users can:
- Toggle sections on/off
- Edit content
- Remove unwanted recommendations
- Customize before publishing
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json


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
    app_name: str = "JuiceNet"
    tagline: str = "EV Charging Marketplace"
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
    """Create default JuiceNet report configuration."""
    config = ReportConfig()

    # Define sections
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
        "host_analysis": ReportSection(
            id="host_analysis",
            title="Host Analysis",
            enabled=True,
            content="Host signup and charger listing metrics"
        ),
        "revenue": ReportSection(
            id="revenue",
            title="Revenue Analysis",
            enabled=True,
            content="Booking fees and revenue projections"
        ),
        "retention": ReportSection(
            id="retention",
            title="Retention Analysis",
            enabled=True,
            content="Day 1/7/30 retention cohorts"
        ),
        "ux_issues": ReportSection(
            id="ux_issues",
            title="UX Issues",
            enabled=True,
            content="Identified user experience problems"
        ),
        "heuristics": ReportSection(
            id="heuristics",
            title="Nielsen's Heuristics",
            enabled=True,
            content="10-point heuristic evaluation"
        ),
        "prototype": ReportSection(
            id="prototype",
            title="Interactive Prototype",
            enabled=True,
            content="Toggle between current and proposed UX"
        ),
        "recommendations": ReportSection(
            id="recommendations",
            title="Recommendations",
            enabled=True,
            content="Prioritized action items"
        ),
        "roadmap": ReportSection(
            id="roadmap",
            title="Implementation Roadmap",
            enabled=True,
            content="Week-by-week implementation plan"
        ),
        "kpis": ReportSection(
            id="kpis",
            title="KPIs & Targets",
            enabled=True,
            content="Current vs target metrics"
        ),
        "roi": ReportSection(
            id="roi",
            title="ROI Projections",
            enabled=True,
            content="Conservative and optimistic estimates"
        ),
        "marketing": ReportSection(
            id="marketing",
            title="Marketing Analysis",
            enabled=False,  # Off by default
            content="Channel performance and geographic focus"
        ),
        "technical": ReportSection(
            id="technical",
            title="Technical Analysis",
            enabled=False,  # Off by default
            content="Architecture and code quality review"
        ),
        "appendices": ReportSection(
            id="appendices",
            title="Appendices",
            enabled=False,  # Off by default
            content="Email captures, screenshots, data sources"
        ),
    }

    # Define recommendations
    config.recommendations = [
        Recommendation(
            id="rec1",
            priority=1,
            title="Fix Email Verification Flow",
            description="Allow browsing while unverified, add auto-login after confirmation, add 'Open App' button on verification page",
            impact="Recover 50-70% of drop-offs (+490-685 users)",
            effort="Medium (backend + frontend changes)",
            enabled=True
        ),
        Recommendation(
            id="rec2",
            priority=2,
            title="Add Role Selection Before Signup",
            description="Show Host vs Guest choice upfront with personalized messaging",
            impact="Reduce confusion by 30-40%, eliminate 59% role-page drop-off",
            effort="Easy (UI change + API field)",
            enabled=True
        ),
        Recommendation(
            id="rec3",
            priority=3,
            title="Streamline Host Onboarding",
            description="Reduce from 9+ steps to 4 steps, smart defaults, optional amenities",
            impact="Increase host completion from 40% to 70%",
            effort="Medium (restructure flow)",
            enabled=True
        ),
        Recommendation(
            id="rec4",
            priority=4,
            title="Social Login Optimization",
            description="Ensure Apple/Google/Facebook login works properly and is prominent",
            impact="Reduce signup friction",
            effort="Easy (already implemented, verify)",
            enabled=True
        ),
        Recommendation(
            id="rec5",
            priority=5,
            title="Implement QR Code Feature",
            description="Add QR codes to charger listings for scan-to-book flow",
            impact="Easy repeat bookings",
            effort="Medium",
            enabled=True
        ),
        Recommendation(
            id="rec6",
            priority=6,
            title="Add Privacy Explanations",
            description="Add trust text under DOB ('Required by Stripe') and Address ('Never shown publicly')",
            impact="Reduce abandonment at profile step",
            effort="Easy (copy only)",
            enabled=True
        ),
        Recommendation(
            id="rec7",
            priority=7,
            title="Earnings Preview for Hosts",
            description="Show '$180-$320 average monthly earnings' during host signup",
            impact="Increase host motivation",
            effort="Easy (UI addition)",
            enabled=True
        ),
    ]

    # Define UX issues
    config.ux_issues = [
        UXIssue(
            id="ux1",
            title="Email verification forces app exit",
            severity="critical",
            description="Users must leave app to verify, then manually return and re-login",
            impact="23% drop-off",
            enabled=True
        ),
        UXIssue(
            id="ux2",
            title="No auto-login after verification",
            severity="critical",
            description="Verification page shows 'Account Activated' with no app link",
            impact="33% additional drop-off",
            enabled=True
        ),
        UXIssue(
            id="ux3",
            title="Verification page has no app redirect",
            severity="critical",
            description="Link goes to Azure static app domain, dead-end page",
            impact="Users lost after verify",
            enabled=True
        ),
        UXIssue(
            id="ux4",
            title="Role selection after signup",
            severity="high",
            description="Users don't know if signing up as Host or Guest",
            impact="59% confusion drop-off",
            enabled=True
        ),
        UXIssue(
            id="ux5",
            title="Too many host onboarding steps",
            severity="high",
            description="9+ screens required before listing a charger",
            impact="60% host drop-off",
            enabled=True
        ),
        UXIssue(
            id="ux6",
            title="No unverified browsing",
            severity="medium",
            description="Can't explore chargers without completing signup",
            impact="Reduced discovery",
            enabled=True
        ),
        UXIssue(
            id="ux7",
            title="No privacy explanations",
            severity="medium",
            description="DOB and Address requested with no context",
            impact="Profile abandonment",
            enabled=True
        ),
    ]

    # Metrics
    config.metrics = {
        "total_signups": 2012,
        "email_verified": 1543,
        "email_verified_pct": 76.7,
        "profile_complete": 1035,
        "profile_complete_pct": 51.4,
        "reservations": 19,
        "conversion_rate": 0.9,
        "total_hosts": 330,
        "hosts_with_chargers": 131,
        "hosts_with_chargers_pct": 39.7,
        "day30_retention": 0,
    }

    # KPIs with targets
    config.kpis = {
        "signup_to_verified": {"current": 76.7, "target_30d": 85, "target_90d": 90},
        "verified_to_profile": {"current": 67.1, "target_30d": 80, "target_90d": 85},
        "profile_to_booking": {"current": 1.8, "target_30d": 5, "target_90d": 10},
        "overall_conversion": {"current": 0.9, "target_30d": 3.4, "target_90d": 7.5},
        "day30_retention": {"current": 0, "target_30d": 10, "target_90d": 20},
        "monthly_reservations": {"current": 19, "target_30d": 50, "target_90d": 150},
    }

    return config


def render_review_ui(config: ReportConfig) -> ReportConfig:
    """Render the Streamlit review UI and return updated config."""

    st.title("Review & Customize Report")
    st.markdown("Review and customize the report before generating. Toggle sections, edit content, and remove unwanted recommendations.")

    # Tabs for different parts
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Sections",
        "Recommendations",
        "UX Issues",
        "Metrics",
        "Preview"
    ])

    with tab1:
        st.subheader("Report Sections")
        st.markdown("Toggle which sections to include in the final report.")

        col1, col2 = st.columns(2)

        sections_list = list(config.sections.items())
        mid = len(sections_list) // 2

        with col1:
            for section_id, section in sections_list[:mid]:
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"section_{section_id}",
                    help=section.content
                )

        with col2:
            for section_id, section in sections_list[mid:]:
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"section_{section_id}",
                    help=section.content
                )

    with tab2:
        st.subheader("Recommendations")
        st.markdown("Select which recommendations to include. You can also edit them.")

        for i, rec in enumerate(config.recommendations):
            with st.expander(f"Priority {rec.priority}: {rec.title}", expanded=rec.enabled):
                col1, col2 = st.columns([3, 1])

                with col1:
                    rec.enabled = st.checkbox(
                        "Include in report",
                        value=rec.enabled,
                        key=f"rec_enabled_{rec.id}"
                    )

                with col2:
                    severity_color = {
                        1: "🔴",
                        2: "🟠",
                        3: "🟡",
                        4: "🟢",
                        5: "🔵",
                        6: "🟣",
                        7: "⚪"
                    }
                    st.markdown(f"**{severity_color.get(rec.priority, '⚪')} Priority {rec.priority}**")

                if rec.enabled:
                    rec.title = st.text_input(
                        "Title",
                        value=rec.title,
                        key=f"rec_title_{rec.id}"
                    )
                    rec.description = st.text_area(
                        "Description",
                        value=rec.description,
                        key=f"rec_desc_{rec.id}",
                        height=80
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        rec.impact = st.text_input(
                            "Expected Impact",
                            value=rec.impact,
                            key=f"rec_impact_{rec.id}"
                        )
                    with col2:
                        rec.effort = st.text_input(
                            "Effort Level",
                            value=rec.effort,
                            key=f"rec_effort_{rec.id}"
                        )

    with tab3:
        st.subheader("UX Issues")
        st.markdown("Select which issues to highlight in the report.")

        for issue in config.ux_issues:
            severity_badge = {
                "critical": "🔴 CRITICAL",
                "high": "🟠 HIGH",
                "medium": "🟡 MEDIUM",
                "low": "🟢 LOW"
            }

            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                issue.enabled = st.checkbox(
                    "",
                    value=issue.enabled,
                    key=f"issue_{issue.id}",
                    label_visibility="collapsed"
                )

            with col2:
                if issue.enabled:
                    st.markdown(f"**{issue.title}**")
                    st.caption(issue.description)
                else:
                    st.markdown(f"~~{issue.title}~~")

            with col3:
                st.markdown(severity_badge.get(issue.severity, ""))

    with tab4:
        st.subheader("Edit Metrics")
        st.markdown("Adjust the metrics if needed.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**User Metrics**")
            config.metrics["total_signups"] = st.number_input(
                "Total Signups",
                value=config.metrics["total_signups"],
                key="m_signups"
            )
            config.metrics["email_verified"] = st.number_input(
                "Email Verified",
                value=config.metrics["email_verified"],
                key="m_verified"
            )
            config.metrics["profile_complete"] = st.number_input(
                "Profile Complete",
                value=config.metrics["profile_complete"],
                key="m_profile"
            )
            config.metrics["reservations"] = st.number_input(
                "Reservations",
                value=config.metrics["reservations"],
                key="m_reservations"
            )

        with col2:
            st.markdown("**Host Metrics**")
            config.metrics["total_hosts"] = st.number_input(
                "Total Hosts",
                value=config.metrics["total_hosts"],
                key="m_hosts"
            )
            config.metrics["hosts_with_chargers"] = st.number_input(
                "Hosts with Chargers",
                value=config.metrics["hosts_with_chargers"],
                key="m_chargers"
            )

        st.markdown("---")
        st.markdown("**KPI Targets**")

        for kpi_id, kpi_data in config.kpis.items():
            st.markdown(f"**{kpi_id.replace('_', ' ').title()}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                kpi_data["current"] = st.number_input(
                    "Current",
                    value=float(kpi_data["current"]),
                    key=f"kpi_current_{kpi_id}"
                )
            with col2:
                kpi_data["target_30d"] = st.number_input(
                    "30-Day Target",
                    value=float(kpi_data["target_30d"]),
                    key=f"kpi_30d_{kpi_id}"
                )
            with col3:
                kpi_data["target_90d"] = st.number_input(
                    "90-Day Target",
                    value=float(kpi_data["target_90d"]),
                    key=f"kpi_90d_{kpi_id}"
                )

    with tab5:
        st.subheader("Report Preview")

        # Summary of what will be included
        enabled_sections = [s.title for s in config.sections.values() if s.enabled]
        enabled_recs = [r for r in config.recommendations if r.enabled]
        enabled_issues = [i for i in config.ux_issues if i.enabled]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sections", len(enabled_sections))
        with col2:
            st.metric("Recommendations", len(enabled_recs))
        with col3:
            st.metric("UX Issues", len(enabled_issues))

        st.markdown("---")

        st.markdown("**Sections to Include:**")
        for section in enabled_sections:
            st.markdown(f"- {section}")

        st.markdown("**Recommendations to Include:**")
        for rec in enabled_recs:
            st.markdown(f"- **P{rec.priority}**: {rec.title}")

        st.markdown("**UX Issues to Include:**")
        for issue in enabled_issues:
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            st.markdown(f"- {severity_emoji.get(issue.severity, '')} {issue.title}")

    return config


def save_config(config: ReportConfig, path: str):
    """Save config to JSON for later use."""
    data = {
        "app_name": config.app_name,
        "tagline": config.tagline,
        "audit_date": config.audit_date,
        "sections": {
            k: {"enabled": v.enabled, "title": v.title, "content": v.content}
            for k, v in config.sections.items()
        },
        "recommendations": [
            {
                "id": r.id,
                "priority": r.priority,
                "title": r.title,
                "description": r.description,
                "impact": r.impact,
                "effort": r.effort,
                "enabled": r.enabled
            }
            for r in config.recommendations
        ],
        "ux_issues": [
            {
                "id": i.id,
                "title": i.title,
                "severity": i.severity,
                "description": i.description,
                "impact": i.impact,
                "enabled": i.enabled
            }
            for i in config.ux_issues
        ],
        "metrics": config.metrics,
        "kpis": config.kpis
    }

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def load_config(path: str) -> ReportConfig:
    """Load config from JSON."""
    with open(path, 'r') as f:
        data = json.load(f)

    config = ReportConfig()
    config.app_name = data.get("app_name", "JuiceNet")
    config.tagline = data.get("tagline", "")
    config.audit_date = data.get("audit_date", "")

    # Load sections
    for k, v in data.get("sections", {}).items():
        config.sections[k] = ReportSection(
            id=k,
            title=v["title"],
            enabled=v["enabled"],
            content=v.get("content", "")
        )

    # Load recommendations
    config.recommendations = [
        Recommendation(**r) for r in data.get("recommendations", [])
    ]

    # Load issues
    config.ux_issues = [
        UXIssue(**i) for i in data.get("ux_issues", [])
    ]

    config.metrics = data.get("metrics", {})
    config.kpis = data.get("kpis", {})

    return config


# Streamlit page for standalone use
def main():
    st.set_page_config(
        page_title="Report Review",
        page_icon="📝",
        layout="wide"
    )

    # Initialize or load config
    if "report_config" not in st.session_state:
        st.session_state.report_config = create_default_config()

    # Render review UI
    config = render_review_ui(st.session_state.report_config)
    st.session_state.report_config = config

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Save Configuration", type="secondary"):
            save_config(config, "report_config.json")
            st.success("Configuration saved!")

    with col2:
        if st.button("📄 Generate Report", type="primary"):
            # Count enabled items
            enabled_sections = sum(1 for s in config.sections.values() if s.enabled)
            enabled_recs = sum(1 for r in config.recommendations if r.enabled)
            enabled_issues = sum(1 for i in config.ux_issues if i.enabled)

            st.success(f"""
            Report will be generated with:
            - {enabled_sections} sections
            - {enabled_recs} recommendations
            - {enabled_issues} UX issues

            Generating...
            """)

            # Here you would call the actual report generator
            # from comprehensive_shareable_report import ComprehensiveShareableReport
            # report = ComprehensiveShareableReport(config=config)
            # report.save()


if __name__ == "__main__":
    main()
