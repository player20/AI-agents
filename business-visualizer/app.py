"""
Weaver Pro - Business Audit & UX Analysis Platform

Main Streamlit application with multi-page navigation.
"""

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Weaver Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #EF4444, #F97316);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #F8FAFC;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #E2E8F0;
    }
    .feature-card h3 {
        color: #0F172A;
        margin-bottom: 8px;
    }
    .feature-card p {
        color: #64748B;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔍 Weaver Pro")
    st.markdown("---")
    st.markdown("**Navigation**")

    page = st.radio(
        "Go to",
        ["🏠 Home", "📊 Audit Report", "📝 Review & Customize", "🎨 Prototype Generator"],
        label_visibility="collapsed"
    )

# Main content based on page selection
if page == "🏠 Home":
    st.markdown('<p class="main-header">Weaver Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Business Audit & UX Analysis Platform</p>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Comprehensive Audits</h3>
            <p>Generate data-driven audit reports with funnel analysis, UX issues, and ROI projections.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <h3>🎨 Interactive Prototypes</h3>
            <p>Create shareable prototypes showing before/after UX improvements.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Review & Customize</h3>
            <p>Edit recommendations, toggle sections, and customize before publishing.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            <h3>🚀 One-Click Deploy</h3>
            <p>Generate shareable HTML reports ready for Netlify hosting.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Quick Start")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Generate Audit Report", use_container_width=True):
            st.session_state.page = "audit"
            st.rerun()

    with col2:
        if st.button("📝 Review & Customize", use_container_width=True):
            st.session_state.page = "review"
            st.rerun()

    with col3:
        if st.button("🎨 Create Prototype", use_container_width=True):
            st.session_state.page = "prototype"
            st.rerun()

elif page == "📊 Audit Report":
    st.header("📊 Generate Audit Report")
    st.markdown("Create a comprehensive, shareable audit report.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        app_name = st.text_input("App Name", value="JuiceNet")
        tagline = st.text_input("Tagline", value="EV Charging Marketplace")
        audit_date = st.text_input("Audit Date", value="January 2026")

    with col2:
        prototype_path = st.text_input(
            "Prototype HTML Path (optional)",
            value=r"C:\Users\jacob\Desktop\claude-code-example\JuiceNet code\mockups\juicenet-flow-prototype.html"
        )

    st.markdown("---")

    report_type = st.radio(
        "Report Type",
        ["Comprehensive (Full)", "Executive Summary", "Developer Handover"],
        horizontal=True
    )

    if st.button("🚀 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            try:
                from comprehensive_shareable_report import ComprehensiveShareableReport

                report = ComprehensiveShareableReport(
                    app_name=app_name,
                    tagline=tagline,
                    audit_date=audit_date,
                    prototype_path=prototype_path
                )

                output_path = report.save()

                st.success(f"Report generated successfully!")
                st.markdown(f"**File:** `{output_path}`")

                st.markdown("---")
                st.markdown("### 🚀 Deploy to Netlify")
                st.code("1. Go to https://app.netlify.com/drop\n2. Drag the HTML file\n3. Get your shareable URL!")

                # Show preview link
                st.markdown(f"[📄 Open Report](file:///{output_path.replace(chr(92), '/')})")

            except Exception as e:
                st.error(f"Error generating report: {e}")

elif page == "📝 Review & Customize":
    # Import and run the review UI
    try:
        from report_review import create_default_config, render_review_ui, save_config

        if "report_config" not in st.session_state:
            st.session_state.report_config = create_default_config()

        config = render_review_ui(st.session_state.report_config)
        st.session_state.report_config = config

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Configuration", type="secondary"):
                save_config(config, "report_config.json")
                st.success("Configuration saved!")

        with col2:
            if st.button("📄 Generate Report", type="primary"):
                with st.spinner("Generating customized report..."):
                    try:
                        from comprehensive_shareable_report import ComprehensiveShareableReport

                        report = ComprehensiveShareableReport(
                            app_name=config.app_name,
                            tagline=config.tagline,
                            audit_date=config.audit_date
                        )

                        output_path = report.save()
                        st.success(f"Report generated: {output_path}")

                    except Exception as e:
                        st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"Error loading review module: {e}")

elif page == "🎨 Prototype Generator":
    st.header("🎨 Prototype Generator")
    st.markdown("Generate interactive before/after prototypes.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input")
        source_file = st.text_input(
            "Source Prototype HTML",
            value=r"C:\Users\jacob\Desktop\claude-code-example\JuiceNet code\mockups\juicenet-flow-prototype.html"
        )

    with col2:
        st.subheader("Output")
        output_name = st.text_input("Output Filename", value="JUICENET_SHAREABLE_PROTOTYPE.html")

    if st.button("🎨 Generate Prototype", type="primary"):
        with st.spinner("Generating prototype..."):
            try:
                from shareable_interactive_report import ShareableInteractiveReport

                report = ShareableInteractiveReport(
                    prototype_path=source_file
                )

                output_path = Path(__file__).parent / output_name
                report.save(str(output_path))

                st.success(f"Prototype generated: {output_path}")

            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("Weaver Pro | Business Audit & UX Analysis Platform")
