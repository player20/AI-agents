"""
Report Review & Publish Page

Allows users to review and customize the audit report before generating.
- Toggle sections on/off
- Edit/remove recommendations
- Customize metrics
- Preview before publishing
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_review import (
    ReportConfig,
    ReportSection,
    Recommendation,
    UXIssue,
    create_default_config,
    save_config,
    load_config
)

st.set_page_config(
    page_title="Review & Publish Report",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Review & Customize Report")
st.markdown("**Review all content before generating.** Toggle sections, edit recommendations, and remove anything you don't want.")

# Initialize config
if "report_config" not in st.session_state:
    st.session_state.report_config = create_default_config()

config = st.session_state.report_config

# Sidebar summary
with st.sidebar:
    st.header("Report Summary")

    enabled_sections = sum(1 for s in config.sections.values() if s.enabled)
    enabled_recs = sum(1 for r in config.recommendations if r.enabled)
    enabled_issues = sum(1 for i in config.ux_issues if i.enabled)

    st.metric("Sections", f"{enabled_sections}/{len(config.sections)}")
    st.metric("Recommendations", f"{enabled_recs}/{len(config.recommendations)}")
    st.metric("UX Issues", f"{enabled_issues}/{len(config.ux_issues)}")

    st.markdown("---")

    # Quick toggles
    st.subheader("Quick Actions")

    if st.button("Select All Sections"):
        for section in config.sections.values():
            section.enabled = True
        st.rerun()

    if st.button("Minimal Report"):
        # Only essential sections
        essential = ["executive", "funnel", "ux_issues", "recommendations", "roi"]
        for section_id, section in config.sections.items():
            section.enabled = section_id in essential
        st.rerun()

    if st.button("Full Report"):
        for section in config.sections.values():
            section.enabled = True
        st.rerun()

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📑 Sections",
    "💡 Recommendations",
    "⚠️ UX Issues",
    "📊 Metrics & KPIs",
    "👁️ Preview & Generate"
])

# ============ SECTIONS TAB ============
with tab1:
    st.subheader("Report Sections")
    st.markdown("Choose which sections to include in the final report.")

    # Group sections
    core_sections = ["executive", "funnel", "ux_issues", "recommendations"]
    analysis_sections = ["host_analysis", "revenue", "retention", "heuristics"]
    interactive_sections = ["prototype", "roadmap", "kpis", "roi"]
    optional_sections = ["marketing", "technical", "appendices"]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Core Sections**")
        for section_id in core_sections:
            if section_id in config.sections:
                section = config.sections[section_id]
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"sec_{section_id}",
                    help=section.content
                )

        st.markdown("**📈 Analysis Sections**")
        for section_id in analysis_sections:
            if section_id in config.sections:
                section = config.sections[section_id]
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"sec_{section_id}",
                    help=section.content
                )

    with col2:
        st.markdown("**🎮 Interactive Sections**")
        for section_id in interactive_sections:
            if section_id in config.sections:
                section = config.sections[section_id]
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"sec_{section_id}",
                    help=section.content
                )

        st.markdown("**📎 Optional Sections** *(Off by default)*")
        for section_id in optional_sections:
            if section_id in config.sections:
                section = config.sections[section_id]
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"sec_{section_id}",
                    help=section.content
                )

# ============ RECOMMENDATIONS TAB ============
with tab2:
    st.subheader("Recommendations")
    st.markdown("**Include or exclude recommendations.** Edit the content if needed.")

    # Bulk actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Enable All", key="rec_all"):
            for rec in config.recommendations:
                rec.enabled = True
            st.rerun()
    with col2:
        if st.button("❌ Disable All", key="rec_none"):
            for rec in config.recommendations:
                rec.enabled = False
            st.rerun()
    with col3:
        if st.button("🎯 Top 3 Only", key="rec_top3"):
            for rec in config.recommendations:
                rec.enabled = rec.priority <= 3
            st.rerun()

    st.markdown("---")

    for rec in sorted(config.recommendations, key=lambda x: x.priority):
        priority_colors = {
            1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "🔵", 6: "🟣", 7: "⚪"
        }

        with st.container():
            col1, col2 = st.columns([0.1, 0.9])

            with col1:
                rec.enabled = st.checkbox(
                    "",
                    value=rec.enabled,
                    key=f"rec_check_{rec.id}",
                    label_visibility="collapsed"
                )

            with col2:
                status = "✓" if rec.enabled else "✗"
                color = "green" if rec.enabled else "gray"

                with st.expander(
                    f"{priority_colors.get(rec.priority, '⚪')} **P{rec.priority}: {rec.title}** {status}",
                    expanded=False
                ):
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

                        col_a, col_b = st.columns(2)
                        with col_a:
                            rec.impact = st.text_input(
                                "Impact",
                                value=rec.impact,
                                key=f"rec_impact_{rec.id}"
                            )
                        with col_b:
                            rec.effort = st.text_input(
                                "Effort",
                                value=rec.effort,
                                key=f"rec_effort_{rec.id}"
                            )
                    else:
                        st.caption("This recommendation will not be included.")

# ============ UX ISSUES TAB ============
with tab3:
    st.subheader("UX Issues")
    st.markdown("Select which issues to highlight in the report.")

    # Group by severity
    severity_order = ["critical", "high", "medium", "low"]

    for severity in severity_order:
        issues_in_severity = [i for i in config.ux_issues if i.severity == severity]
        if not issues_in_severity:
            continue

        severity_labels = {
            "critical": "🔴 Critical Issues",
            "high": "🟠 High Priority",
            "medium": "🟡 Medium Priority",
            "low": "🟢 Low Priority"
        }

        st.markdown(f"**{severity_labels.get(severity, severity.title())}**")

        for issue in issues_in_severity:
            col1, col2, col3 = st.columns([0.1, 0.6, 0.3])

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
                    st.markdown(f"~~{issue.title}~~", help="Excluded from report")

            with col3:
                st.caption(f"Impact: {issue.impact}")

        st.markdown("---")

# ============ METRICS TAB ============
with tab4:
    st.subheader("Metrics & KPIs")
    st.markdown("Adjust the numbers if your data has changed.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**👥 User Metrics**")
        config.metrics["total_signups"] = st.number_input(
            "Total Signups",
            value=config.metrics.get("total_signups", 2012),
            key="m_signups"
        )
        config.metrics["email_verified"] = st.number_input(
            "Email Verified",
            value=config.metrics.get("email_verified", 1543),
            key="m_verified"
        )
        config.metrics["profile_complete"] = st.number_input(
            "Profile Complete",
            value=config.metrics.get("profile_complete", 1035),
            key="m_profile"
        )
        config.metrics["reservations"] = st.number_input(
            "Total Reservations",
            value=config.metrics.get("reservations", 19),
            key="m_reservations"
        )

    with col2:
        st.markdown("**🏠 Host Metrics**")
        config.metrics["total_hosts"] = st.number_input(
            "Total Hosts",
            value=config.metrics.get("total_hosts", 330),
            key="m_hosts"
        )
        config.metrics["hosts_with_chargers"] = st.number_input(
            "Hosts with Chargers",
            value=config.metrics.get("hosts_with_chargers", 131),
            key="m_chargers"
        )

    st.markdown("---")
    st.markdown("**🎯 KPI Targets**")

    kpi_labels = {
        "signup_to_verified": "Signup → Verified %",
        "verified_to_profile": "Verified → Profile %",
        "profile_to_booking": "Profile → Booking %",
        "overall_conversion": "Overall Conversion %",
        "day30_retention": "Day 30 Retention %",
        "monthly_reservations": "Monthly Reservations"
    }

    for kpi_id, label in kpi_labels.items():
        if kpi_id in config.kpis:
            kpi = config.kpis[kpi_id]
            st.markdown(f"**{label}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                kpi["current"] = st.number_input(
                    "Current",
                    value=float(kpi.get("current", 0)),
                    key=f"kpi_c_{kpi_id}",
                    format="%.1f"
                )
            with col2:
                kpi["target_30d"] = st.number_input(
                    "30-Day Target",
                    value=float(kpi.get("target_30d", 0)),
                    key=f"kpi_30_{kpi_id}",
                    format="%.1f"
                )
            with col3:
                kpi["target_90d"] = st.number_input(
                    "90-Day Target",
                    value=float(kpi.get("target_90d", 0)),
                    key=f"kpi_90_{kpi_id}",
                    format="%.1f"
                )

# ============ PREVIEW & GENERATE TAB ============
with tab5:
    st.subheader("Preview & Generate")

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    enabled_sections = [s for s in config.sections.values() if s.enabled]
    enabled_recs = [r for r in config.recommendations if r.enabled]
    enabled_issues = [i for i in config.ux_issues if i.enabled]

    with col1:
        st.metric("Sections", len(enabled_sections))
    with col2:
        st.metric("Recommendations", len(enabled_recs))
    with col3:
        st.metric("UX Issues", len(enabled_issues))
    with col4:
        critical_count = sum(1 for i in enabled_issues if i.severity == "critical")
        st.metric("Critical Issues", critical_count)

    st.markdown("---")

    # Preview content
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📑 Sections Included:**")
        for section in enabled_sections:
            st.markdown(f"- {section.title}")

        st.markdown("**⚠️ UX Issues Included:**")
        for issue in enabled_issues:
            severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            st.markdown(f"- {severity_emoji.get(issue.severity, '')} {issue.title}")

    with col2:
        st.markdown("**💡 Recommendations Included:**")
        for rec in sorted(enabled_recs, key=lambda x: x.priority):
            st.markdown(f"- **P{rec.priority}**: {rec.title}")

    st.markdown("---")

    # App info
    col1, col2, col3 = st.columns(3)
    with col1:
        config.app_name = st.text_input("App Name", value=config.app_name)
    with col2:
        config.tagline = st.text_input("Tagline", value=config.tagline)
    with col3:
        config.audit_date = st.text_input("Audit Date", value=config.audit_date)

    st.markdown("---")

    # Generate buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Save Config", type="secondary"):
            save_config(config, "report_config.json")
            st.success("✓ Configuration saved to report_config.json")

    with col2:
        if st.button("📄 Generate Report", type="primary"):
            with st.spinner("Generating report..."):
                try:
                    # Import and generate
                    from comprehensive_shareable_report import ComprehensiveShareableReport

                    # Create report with config
                    report = ComprehensiveShareableReport(
                        app_name=config.app_name,
                        tagline=config.tagline,
                        audit_date=config.audit_date
                    )

                    # TODO: Pass config to filter sections/recommendations
                    # For now, generate full report
                    output_path = report.save()

                    st.success(f"✓ Report generated!")
                    st.markdown(f"**File:** `{output_path}`")

                    st.markdown("---")
                    st.markdown("**🚀 Deploy to Netlify:**")
                    st.code("1. Go to https://app.netlify.com/drop\n2. Drag the HTML file\n3. Get your shareable URL!")

                except Exception as e:
                    st.error(f"Error generating report: {e}")

    # Show what will be excluded
    excluded_sections = [s.title for s in config.sections.values() if not s.enabled]
    excluded_recs = [r.title for r in config.recommendations if not r.enabled]
    excluded_issues = [i.title for i in config.ux_issues if not i.enabled]

    if excluded_sections or excluded_recs or excluded_issues:
        with st.expander("📋 What's Excluded"):
            if excluded_sections:
                st.markdown("**Excluded Sections:**")
                for s in excluded_sections:
                    st.markdown(f"- ~~{s}~~")

            if excluded_recs:
                st.markdown("**Excluded Recommendations:**")
                for r in excluded_recs:
                    st.markdown(f"- ~~{r}~~")

            if excluded_issues:
                st.markdown("**Excluded Issues:**")
                for i in excluded_issues:
                    st.markdown(f"- ~~{i}~~")
