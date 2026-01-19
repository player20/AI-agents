"""
Report Review & Customize Page for Weaver Pro

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

st.set_page_config(
    page_title="Report Review - Weaver Pro",
    page_icon="📝",
    layout="wide"
)

st.title("📝 Review & Customize Report")
st.markdown("**Review all content before generating.** Toggle sections, edit recommendations, and remove anything you don't want.")

try:
    from report_review import (
        ReportConfig,
        ReportSection,
        Recommendation,
        UXIssue,
        create_default_config,
        save_config,
    )

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

        st.subheader("Quick Actions")

        if st.button("✅ Select All"):
            for section in config.sections.values():
                section.enabled = True
            for rec in config.recommendations:
                rec.enabled = True
            for issue in config.ux_issues:
                issue.enabled = True
            st.rerun()

        if st.button("🎯 Minimal Report"):
            essential = ["executive", "funnel", "ux_issues", "recommendations", "roi"]
            for section_id, section in config.sections.items():
                section.enabled = section_id in essential
            for rec in config.recommendations:
                rec.enabled = rec.priority <= 3
            st.rerun()

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📑 Sections",
        "💡 Recommendations",
        "⚠️ UX Issues",
        "📊 Metrics",
        "👁️ Preview"
    ])

    # ============ SECTIONS TAB ============
    with tab1:
        st.subheader("Report Sections")
        st.markdown("Toggle which sections to include.")

        col1, col2 = st.columns(2)

        sections_list = list(config.sections.items())
        mid = len(sections_list) // 2

        with col1:
            for section_id, section in sections_list[:mid]:
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"sec_{section_id}",
                    help=section.content
                )

        with col2:
            for section_id, section in sections_list[mid:]:
                section.enabled = st.checkbox(
                    section.title,
                    value=section.enabled,
                    key=f"sec_{section_id}",
                    help=section.content
                )

    # ============ RECOMMENDATIONS TAB ============
    with tab2:
        st.subheader("Recommendations")
        st.markdown("Select which recommendations to include. Click to edit.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ All On"):
                for rec in config.recommendations:
                    rec.enabled = True
                st.rerun()
        with col2:
            if st.button("❌ All Off"):
                for rec in config.recommendations:
                    rec.enabled = False
                st.rerun()
        with col3:
            if st.button("🔝 Top 3"):
                for rec in config.recommendations:
                    rec.enabled = rec.priority <= 3
                st.rerun()

        st.markdown("---")

        for rec in sorted(config.recommendations, key=lambda x: x.priority):
            priority_colors = {1: "🔴", 2: "🟠", 3: "🟡", 4: "🟢", 5: "🔵", 6: "🟣", 7: "⚪"}

            col1, col2 = st.columns([0.08, 0.92])

            with col1:
                rec.enabled = st.checkbox(
                    "",
                    value=rec.enabled,
                    key=f"rec_{rec.id}",
                    label_visibility="collapsed"
                )

            with col2:
                with st.expander(f"{priority_colors.get(rec.priority, '⚪')} P{rec.priority}: {rec.title}"):
                    if rec.enabled:
                        rec.title = st.text_input("Title", value=rec.title, key=f"rt_{rec.id}")
                        rec.description = st.text_area("Description", value=rec.description, key=f"rd_{rec.id}", height=80)
                        c1, c2 = st.columns(2)
                        with c1:
                            rec.impact = st.text_input("Impact", value=rec.impact, key=f"ri_{rec.id}")
                        with c2:
                            rec.effort = st.text_input("Effort", value=rec.effort, key=f"re_{rec.id}")
                    else:
                        st.caption("Excluded from report")

    # ============ UX ISSUES TAB ============
    with tab3:
        st.subheader("UX Issues")

        for issue in config.ux_issues:
            severity_badge = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

            col1, col2, col3 = st.columns([0.08, 0.62, 0.3])

            with col1:
                issue.enabled = st.checkbox("", value=issue.enabled, key=f"ux_{issue.id}", label_visibility="collapsed")

            with col2:
                if issue.enabled:
                    st.markdown(f"**{issue.title}**")
                    st.caption(issue.description)
                else:
                    st.markdown(f"~~{issue.title}~~")

            with col3:
                st.markdown(f"{severity_badge.get(issue.severity, '')} {issue.severity.upper()}")
                st.caption(issue.impact)

    # ============ METRICS TAB ============
    with tab4:
        st.subheader("Metrics")

        col1, col2 = st.columns(2)

        with col1:
            config.metrics["total_signups"] = st.number_input("Total Signups", value=config.metrics.get("total_signups", 2012))
            config.metrics["email_verified"] = st.number_input("Email Verified", value=config.metrics.get("email_verified", 1543))
            config.metrics["reservations"] = st.number_input("Reservations", value=config.metrics.get("reservations", 19))

        with col2:
            config.metrics["total_hosts"] = st.number_input("Total Hosts", value=config.metrics.get("total_hosts", 330))
            config.metrics["hosts_with_chargers"] = st.number_input("Hosts with Chargers", value=config.metrics.get("hosts_with_chargers", 131))

    # ============ PREVIEW TAB ============
    with tab5:
        st.subheader("Preview")

        enabled_sections = [s for s in config.sections.values() if s.enabled]
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

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Sections:**")
            for s in enabled_sections:
                st.markdown(f"- {s.title}")

        with col2:
            st.markdown("**Recommendations:**")
            for r in sorted(enabled_recs, key=lambda x: x.priority):
                st.markdown(f"- P{r.priority}: {r.title}")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        with col1:
            config.app_name = st.text_input("App Name", value=config.app_name)
        with col2:
            config.tagline = st.text_input("Tagline", value=config.tagline)
        with col3:
            config.audit_date = st.text_input("Date", value=config.audit_date)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Config", type="secondary", use_container_width=True):
                save_config(config, "report_config.json")
                st.success("Saved!")

        with col2:
            if st.button("📄 Generate Report", type="primary", use_container_width=True):
                with st.spinner("Generating..."):
                    try:
                        # Add business-visualizer to path for imports
                        sys.path.insert(0, str(Path(__file__).parent.parent / "business-visualizer"))
                        from comprehensive_shareable_report import ComprehensiveShareableReport

                        report = ComprehensiveShareableReport(
                            app_name=config.app_name,
                            tagline=config.tagline,
                            audit_date=config.audit_date
                        )

                        output_path = report.save()
                        st.success(f"Generated: {output_path}")

                        st.markdown("**Deploy:** Drag to https://app.netlify.com/drop")

                    except Exception as e:
                        st.error(f"Error: {e}")

except ImportError as e:
    st.error(f"Missing dependency: {e}")
    st.info("Make sure report_review.py is in the MultiAgentTeam folder.")
