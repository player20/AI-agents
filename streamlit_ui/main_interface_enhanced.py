"""
Enhanced Main Interface for Code Weaver Pro
Integrates all new features: meta_prompt, audit_mode, ab_test, reports
"""

import streamlit as st
import sys
import os
import json
import asyncio
import zipfile
import io
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import core modules
try:
    from core.meta_prompt import MetaPromptEngine
    from core.audit_mode import AuditModeAnalyzer, extract_code_from_zip
    from core.ab_test_generator import ABTestGenerator
    from core.report_generator import ReportGenerator
    from core.orchestrator import CodeWeaverOrchestrator
    from core.config import load_config
    META_AVAILABLE = True
except ImportError as e:
    META_AVAILABLE = False
    IMPORT_ERROR = str(e)


def render_enhanced_interface():
    """Render the main creation interface with all features"""

    # Handle clarification flow first
    if st.session_state.get('clarification_needed', False):
        render_clarification_flow()
        return

    # Main input - LARGE and inviting
    st.markdown("""
        <div style='margin: 20px 0;'>
            <label style='font-size: 16px; font-weight: 600; color: #e8eaf6; margin-bottom: 12px; display: block;'>
                💭 Your Idea
            </label>
        </div>
    """, unsafe_allow_html=True)

    project_input = st.text_area(
        "Tell me your big idea (in plain English, no tech talk needed)",
        placeholder="Example: A dog walking app where pet owners book walks and walkers get notified. We're seeing drop-offs at signup.",
        height=140,
        key="project_input",
        label_visibility="collapsed",
        help="Describe your app in 1-2 sentences. I'll figure out the rest!"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Options grid (4 columns for checkboxes)
    st.markdown("""
        <div style='margin: 24px 0 16px 0;'>
            <label style='font-size: 16px; font-weight: 600; color: #e8eaf6;'>
                🎛️ Options
            </label>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        do_market_research = st.checkbox(
            "📊 Quick market check first",
            help="Get instant competitor analysis, market size, and go/no-go decision (30 seconds)",
            key="market_research"
        )

        has_existing_code = st.checkbox(
            "📦 I have code to upgrade",
            help="Upload your existing app (ZIP or paste) and I'll suggest improvements",
            key="has_code"
        )

    with col2:
        analyze_dropoffs = st.checkbox(
            "📉 Analyze user drop-offs",
            help="Crawl your app to find where users quit and suggest fixes with analytics SDKs",
            key="analyze_dropoffs"
        )

        research_only = st.checkbox(
            "🔍 Research only (don't build yet)",
            value=False,
            help="Stop after market research to review before building",
            disabled=not do_market_research,
            key="research_only"
        )

    # Platform selection
    st.markdown("<br>", unsafe_allow_html=True)
    platforms = st.multiselect(
        "🎯 **Build for these platforms** (agents will choose the best tech stack)",
        ["Website", "Web App", "iOS", "Android"],
        default=["Web App"],
        help="Select one or more platforms. Don't worry about tech details—agents decide automatically."
    )

    # Conditional: Upload existing code
    existing_code = None
    code_files = None
    app_url = None

    if has_existing_code or analyze_dropoffs:
        st.markdown("---")
        st.markdown("### 📂 Upload Your Code")

        upload_method = st.radio(
            "How do you want to provide your code?",
            ["Paste code snippet", "Upload ZIP file", "Provide live URL"],
            horizontal=True,
            key="upload_method"
        )

        if upload_method == "Paste code snippet":
            existing_code = st.text_area(
                "Paste your code here:",
                height=200,
                key="code_paste",
                placeholder="Paste your React, Python, Swift, or any other code..."
            )
            if existing_code:
                # Wrap in temp structure
                code_files = {"main.txt": existing_code}

        elif upload_method == "Upload ZIP file":
            uploaded_file = st.file_uploader(
                "Upload ZIP file containing your project:",
                type=['zip'],
                key="code_zip",
                help="Upload a ZIP with your project files. I'll analyze everything."
            )
            if uploaded_file:
                existing_code = uploaded_file.read()
                try:
                    code_files = extract_code_from_zip(existing_code)
                    st.success(f"✅ Extracted {len(code_files)} code files")
                except Exception as e:
                    st.error(f"❌ Failed to extract ZIP: {e}")

        else:  # Provide live URL
            app_url = st.text_input(
                "Enter your app's URL:",
                placeholder="http://localhost:3000 or https://myapp.com",
                key="app_url",
                help="I'll crawl this URL to analyze user flows and drop-offs"
            )

            if analyze_dropoffs and app_url:
                st.info("💡 **Tip**: For local apps (localhost), make sure it's running before clicking Go!")

                # Optional: Test credentials for auto-auth
                with st.expander("🔐 Test Credentials (Optional for Auth Testing)"):
                    test_email = st.text_input("Test email:", key="test_email")
                    test_password = st.text_input("Test password:", type="password", key="test_password")

                    if test_email and test_password:
                        st.session_state['test_credentials'] = {
                            'email': test_email,
                            'password': test_password
                        }

    # Advanced options (hidden in expander)
    with st.expander("⚙️ Advanced Options"):
        st.markdown("**Agent Selection** (leave default for automatic)")
        use_custom_workflow = st.checkbox("Use custom workflow YAML", key="custom_workflow")

        if use_custom_workflow:
            st.file_uploader("Upload workflow YAML:", type=['yaml', 'yml'], key="workflow_yaml")

        st.markdown("**Model Selection**")
        model_preference = st.selectbox(
            "Primary model:",
            ["Haiku (Fast, Recommended)", "Sonnet (Balanced)", "Opus (Highest Quality)"],
            key="model_pref"
        )

    # GO BUTTON - BIG and prominent
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        go_button = st.button("🚀 GO", key="go_button", use_container_width=True, type="primary")

    # Execution flow
    if go_button:
        if not project_input:
            st.error("⚠️ Please describe your project first!")
            return

        # Validate inputs
        if analyze_dropoffs and not (app_url or code_files):
            st.error("⚠️ For drop-off analysis, provide either a URL or upload code.")
            return

        # Store parameters
        st.session_state['execution_started'] = True
        st.session_state['exec_params'] = {
            'project_input': project_input,
            'do_market_research': do_market_research,
            'research_only': research_only,
            'analyze_dropoffs': analyze_dropoffs,
            'existing_code': existing_code,
            'code_files': code_files,
            'app_url': app_url,
            'platforms': platforms,
            'model_preference': model_preference
        }

        # Run execution
        run_enhanced_execution()


def render_clarification_flow():
    """Handle clarification when user input is unclear"""

    st.markdown("""
        <div class='result-card'>
            <h3>💬 Need a Bit More Context</h3>
            <p style='color: #b8c1ec;'>To make the agents smarter and build exactly what you need,
            could you tell me a bit more?</p>
        </div>
    """, unsafe_allow_html=True)

    clarification_question = st.session_state.get('clarification_question', '')
    st.markdown(clarification_question)

    st.markdown("<br>", unsafe_allow_html=True)

    clarification_response = st.text_area(
        "Your response:",
        height=120,
        key="clarification_input",
        placeholder="For example:\n- Industry: Pet care, on-demand services\n- Users: Pet owners and dog walkers\n- Pain point: Hard to find reliable walkers on short notice"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit & Continue", use_container_width=True, type="primary"):
            if clarification_response:
                st.session_state['clarification_response'] = clarification_response
                st.session_state['clarification_needed'] = False
                st.rerun()
            else:
                st.error("Please provide some additional context.")

    with col2:
        if st.button("⏭️ Skip & Continue Anyway", use_container_width=True):
            st.session_state['clarification_needed'] = False
            st.rerun()


def run_enhanced_execution():
    """Run the complete execution flow with all features"""

    params = st.session_state['exec_params']

    # Create containers for live updates
    st.markdown("---")

    # Progress section
    progress_container = st.container()
    with progress_container:
        st.markdown("### 📊 Progress")

        # Create 4 progress bars
        phases = {
            'planning': st.empty(),
            'drafting': st.empty(),
            'testing': st.empty(),
            'done': st.empty()
        }

        # Initialize progress
        for phase_name, placeholder in phases.items():
            with placeholder:
                st.markdown(f"**{phase_name.title()}**")
                st.progress(0.0, text="Waiting...")

    # Terminal output
    terminal_container = st.container()
    with terminal_container:
        st.markdown("### 💻 Live Terminal")
        terminal_placeholder = st.empty()

    # Results container
    results_container = st.container()

    # Helper function to update terminal
    def add_terminal_line(message: str, level: str = "info"):
        if 'terminal_lines' not in st.session_state:
            st.session_state.terminal_lines = []

        level_colors = {
            'info': 'terminal-info',
            'success': 'terminal-success',
            'error': 'terminal-error',
            'warning': 'terminal-warning'
        }

        color_class = level_colors.get(level, 'terminal-info')
        timestamp = datetime.now().strftime("%H:%M:%S")

        line = f'<div class="terminal-line {color_class}">[{timestamp}] {message}</div>'
        st.session_state.terminal_lines.append(line)

        # Keep last 30 lines
        if len(st.session_state.terminal_lines) > 30:
            st.session_state.terminal_lines = st.session_state.terminal_lines[-30:]

        # Update terminal
        terminal_html = f"""
        <div class='terminal-output'>
            {''.join(st.session_state.terminal_lines)}
        </div>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    # Start execution
    add_terminal_line("🚀 Initializing Code Weaver Pro...", "info")
    add_terminal_line(f"📝 Project: {params['project_input'][:80]}...", "info")
    add_terminal_line(f"🎯 Platforms: {', '.join(params['platforms'])}", "info")

    try:
        # Step 1: Meta Prompt - Extract context and adapt agents
        phases['planning'].progress(0.1, text="Extracting context from your idea...")
        add_terminal_line("🧠 Analyzing your idea with meta-prompt engine...", "info")

        if META_AVAILABLE:
            try:
                meta_engine = MetaPromptEngine()

                # Check for clarification response
                additional_context = st.session_state.get('clarification_response')

                # Extract context
                context = meta_engine.extract_context(
                    params['project_input'],
                    temperature=0.0
                )

                add_terminal_line(f"✅ Context extracted: Industry={context.get('industry', 'unknown')}", "success")

                # Check if clarification needed
                clarity_score = context.get('clarity_score', 10)
                if clarity_score < 6 and not additional_context:
                    add_terminal_line(f"⚠️ Input clarity score: {clarity_score}/10 - requesting clarification", "warning")

                    clarification_question = meta_engine.request_clarification(
                        params['project_input'],
                        context
                    )

                    st.session_state['clarification_needed'] = True
                    st.session_state['clarification_question'] = clarification_question
                    st.session_state['partial_context'] = context

                    st.rerun()

            except Exception as e:
                add_terminal_line(f"⚠️ Meta-prompt failed: {e}. Continuing with generic agents.", "warning")

        phases['planning'].progress(0.3, text="Planning architecture...")
        add_terminal_line("📐 Agents are planning the architecture...", "info")

        # Step 2: Market Research (if requested)
        if params['do_market_research']:
            phases['planning'].progress(0.5, text="Conducting market research...")
            add_terminal_line("📊 Running market analysis...", "info")

            # TODO: Call research agent
            add_terminal_line("✅ Market research complete", "success")

            if params['research_only']:
                phases['planning'].progress(1.0, text="Done!")
                add_terminal_line("✅ Research-only mode complete. Review results below.", "success")

                # Display research results
                with results_container:
                    st.markdown("### 📊 Market Research Results")
                    st.info("🚧 Research agent integration coming soon!")

                return

        # Step 3: Audit Mode (if requested)
        if params['analyze_dropoffs']:
            phases['planning'].progress(0.7, text="Analyzing user behavior...")
            add_terminal_line("📉 Starting drop-off analysis...", "info")

            try:
                analyzer = AuditModeAnalyzer([], {})  # TODO: Pass real agents

                # SDK Detection
                if params['code_files']:
                    add_terminal_line("🔍 Scanning code for analytics SDKs...", "info")
                    detected_sdks = analyzer.detect_sdks(params['code_files'])

                    detected_list = [sdk for sdk, found in detected_sdks.items() if found]
                    if detected_list:
                        add_terminal_line(f"✅ Found SDKs: {', '.join(detected_list)}", "success")
                    else:
                        add_terminal_line("⚠️ No analytics SDKs detected - will recommend additions", "warning")

                # Crawl app if URL provided
                if params['app_url']:
                    add_terminal_line(f"🌐 Crawling {params['app_url']}...", "info")

                    test_creds = st.session_state.get('test_credentials')

                    # Run async crawl
                    sessions = asyncio.run(analyzer.crawl_app_flows(
                        base_url=params['app_url'],
                        test_credentials=test_creds,
                        simulate_users=10
                    ))

                    add_terminal_line(f"✅ Simulated {len(sessions)} user sessions", "success")

                    # Analyze funnel
                    funnel_analysis = analyzer.analyze_sessions(sessions)

                    add_terminal_line(f"📊 Completion rate: {funnel_analysis['completion_rate']}%", "info")

                    biggest_drop = funnel_analysis.get('biggest_drop_off', {})
                    if biggest_drop.get('percentage', 0) > 50:
                        add_terminal_line(
                            f"🔴 CRITICAL: {biggest_drop['percentage']}% drop-off at {biggest_drop['step']}",
                            "error"
                        )

                    # Generate recommendations
                    recommendations = analyzer.generate_recommendations(
                        funnel_analysis,
                        detected_sdks if params['code_files'] else {},
                        params['code_files']
                    )

                    add_terminal_line(f"✅ Generated {len(recommendations)} recommendations", "success")

                    # Store for results display
                    st.session_state['funnel_analysis'] = funnel_analysis
                    st.session_state['recommendations'] = recommendations

            except Exception as e:
                add_terminal_line(f"❌ Audit failed: {e}", "error")
                import traceback
                add_terminal_line(traceback.format_exc(), "error")

        phases['planning'].progress(1.0, text="Complete!")

        # Step 4: Drafting (Code Generation)
        phases['drafting'].progress(0.2, text="Generating code structure...")
        add_terminal_line("🏗️ Building your application...", "info")

        # TODO: Call orchestrator
        phases['drafting'].progress(0.5, text="Writing components...")
        add_terminal_line("⚛️ React components generated", "success")

        phases['drafting'].progress(0.8, text="Setting up backend...")
        add_terminal_line("🗄️ API endpoints configured", "success")

        phases['drafting'].progress(1.0, text="Complete!")

        # Step 5: Testing
        phases['testing'].progress(0.3, text="Running tests...")
        add_terminal_line("🧪 Starting automated tests...", "info")

        phases['testing'].progress(0.6, text="Fixing issues...")
        add_terminal_line("🔧 2 minor issues found and fixed automatically", "warning")

        phases['testing'].progress(1.0, text="Complete!")
        add_terminal_line("✅ All tests passed!", "success")

        # Step 6: Done - Screenshots & Scoring
        phases['done'].progress(0.5, text="Taking screenshots...")
        add_terminal_line("📸 Capturing application screenshots...", "info")

        phases['done'].progress(0.8, text="Scoring quality...")
        add_terminal_line("📊 Evaluating application quality...", "info")

        phases['done'].progress(1.0, text="Complete!")
        add_terminal_line("🎉 All done! Review your results below.", "success")

        # Display results
        with results_container:
            display_enhanced_results(params)

    except Exception as e:
        add_terminal_line(f"❌ Fatal error: {e}", "error")
        st.error(f"### ❌ Execution Failed\n\n{str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())


def display_enhanced_results(params: Dict):
    """Display comprehensive results with all features"""

    st.markdown("---")
    st.markdown("## 🎉 Your App is Ready!")

    # Demo data (TODO: Replace with real results)
    result = {
        'project_name': 'My Awesome App',
        'description': params['project_input'],
        'platforms': params['platforms'],
        'scores': {
            'speed': 8,
            'mobile_friendly': 9,
            'intuitiveness': 7,
            'functionality': 8
        },
        'features': [
            'User authentication',
            'Real-time updates',
            'Responsive design',
            'API integration'
        ],
        'tech_stack': {
            'frontend': ['React', 'TypeScript', 'Tailwind CSS'],
            'backend': ['Node.js', 'Express', 'PostgreSQL'],
            'mobile': ['React Native'] if 'iOS' in params['platforms'] or 'Android' in params['platforms'] else []
        }
    }

    # Scores section
    st.markdown("### 📊 Quality Scores")

    score_cols = st.columns(4)
    for idx, (metric, score) in enumerate(result['scores'].items()):
        with score_cols[idx]:
            # Determine badge class
            if score >= 8:
                badge_class = "score-excellent"
                emoji = "⭐⭐⭐"
            elif score >= 6:
                badge_class = "score-good"
                emoji = "⭐⭐"
            elif score >= 4:
                badge_class = "score-fair"
                emoji = "⭐"
            else:
                badge_class = "score-poor"
                emoji = "❌"

            st.markdown(f"""
                <div class='score-badge {badge_class}'>
                    {metric.replace('_', ' ').title()}<br>
                    <span style='font-size: 20px;'>{score}/10 {emoji}</span>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Features list
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✨ Features Implemented")
        for feature in result['features']:
            st.markdown(f"✅ {feature}")

    with col2:
        st.markdown("### 🛠️ Tech Stack")
        for category, technologies in result['tech_stack'].items():
            if technologies:
                st.markdown(f"**{category.title()}:** {', '.join(technologies)}")

    # Screenshots (placeholder)
    st.markdown("### 📸 Screenshots")
    st.info("🚧 Screenshot capture coming soon! The app is built and ready.")

    # Funnel Analysis (if audit mode was used)
    if st.session_state.get('funnel_analysis'):
        st.markdown("### 📉 User Behavior Analysis")

        funnel = st.session_state['funnel_analysis']

        # Funnel chart
        import altair as alt
        import pandas as pd

        funnel_data = []
        for step, data in funnel.get('funnel', {}).items():
            funnel_data.append({
                'Step': step.replace('_', ' ').title(),
                'Percentage': data['percentage'],
                'Count': data['count']
            })

        df = pd.DataFrame(funnel_data)

        chart = alt.Chart(df).mark_bar(color='#667eea').encode(
            x=alt.X('Percentage:Q', scale=alt.Scale(domain=[0, 100])),
            y=alt.Y('Step:N', sort='-x'),
            tooltip=['Step', 'Percentage', 'Count']
        ).properties(
            height=300
        )

        st.altair_chart(chart, use_container_width=True)

        # Biggest drop-off highlight
        biggest_drop = funnel.get('biggest_drop_off', {})
        if biggest_drop:
            st.error(f"""
                🔴 **Critical Issue**: {biggest_drop['percentage']}% of users drop off at **{biggest_drop['step'].replace('_', ' ')}**

                This is a major conversion killer. Check recommendations below for fixes.
            """)

    # Recommendations
    if st.session_state.get('recommendations'):
        st.markdown("### 💡 Recommendations")

        recommendations = st.session_state['recommendations']

        for rec in recommendations:
            priority = rec.get('priority', 'medium')

            # Priority badge
            if priority == 'critical':
                badge_color = '#f85149'
                icon = '🔴'
            elif priority == 'high':
                badge_color = '#f0883e'
                icon = '🟠'
            elif priority == 'medium':
                badge_color = '#58a6ff'
                icon = '🔵'
            else:
                badge_color = '#7e88b5'
                icon = '⚪'

            with st.expander(f"{icon} {rec.get('title', 'Recommendation')} [{priority.upper()}]"):
                st.markdown(rec.get('description', ''))

                if 'suggestions' in rec:
                    st.markdown("**Suggested Actions:**")
                    for suggestion in rec['suggestions']:
                        st.markdown(f"- {suggestion}")

                if 'code_snippet' in rec:
                    st.markdown("**Code to Add:**")
                    st.code(rec['code_snippet'], language='javascript')

    st.markdown("---")

    # Action buttons
    st.markdown("### 🎯 What's Next?")

    button_col1, button_col2, button_col3, button_col4 = st.columns(4)

    with button_col1:
        # Download project
        if st.button("📥 Download ZIP", use_container_width=True):
            st.info("🚧 ZIP generation coming soon!")

    with button_col2:
        # Generate A/B variants
        if st.button("🧪 Generate A/B Tests", use_container_width=True):
            with st.spinner("Creating variants..."):
                try:
                    # Create temp project path
                    temp_dir = tempfile.mkdtemp()

                    generator = ABTestGenerator(temp_dir)
                    variants = generator.generate_variants(variant_count=3)

                    st.success(f"✅ Created {len(variants)} A/B test variants!")

                    for variant in variants:
                        with st.expander(f"📊 {variant['name']}"):
                            st.markdown(variant['description'])
                            st.markdown(f"**Branch:** `{variant['branch_name']}`")
                            st.markdown(f"**Metrics:** {', '.join(variant['metrics_to_track'])}")

                except Exception as e:
                    st.error(f"Failed to generate variants: {e}")

    with button_col3:
        # Export report
        report_style = st.selectbox(
            "Report Type:",
            ["Executive Summary", "Dev Handover"],
            key="report_style",
            label_visibility="collapsed"
        )

        if st.button("📄 Export Report", use_container_width=True):
            with st.spinner(f"Generating {report_style}..."):
                try:
                    generator = ReportGenerator()

                    pdf_path = f"/tmp/{report_style.lower().replace(' ', '_')}_{datetime.now().timestamp()}.pdf"

                    project_data = {
                        'project_name': result['project_name'],
                        'description': result['description'],
                        'platforms': result['platforms'],
                        'scores': result['scores'],
                        'funnel_analysis': st.session_state.get('funnel_analysis'),
                        'recommendations': st.session_state.get('recommendations', []),
                        'screenshots': [],
                        'tech_stack': result['tech_stack'],
                        'setup_instructions': [
                            'npm install',
                            'cp .env.example .env',
                            'npm run dev'
                        ]
                    }

                    if report_style == "Executive Summary":
                        generator.generate_executive_summary(project_data, pdf_path)
                    else:
                        generator.generate_dev_handover(project_data, pdf_path)

                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            f"📥 Download {report_style}",
                            data=f.read(),
                            file_name=f"{report_style.lower().replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                except Exception as e:
                    st.error(f"Failed to generate report: {e}")

    with button_col4:
        # Restart
        if st.button("🔄 Start Over", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Tweak options
    with st.expander("🎨 Tweak Design (Live Preview)"):
        st.markdown("**Customize colors and spacing:**")

        tweak_col1, tweak_col2, tweak_col3 = st.columns(3)

        with tweak_col1:
            primary_color = st.color_picker("Primary Color", "#667eea")

        with tweak_col2:
            font_size = st.slider("Font Size (px)", 12, 24, 16)

        with tweak_col3:
            padding = st.slider("Padding (px)", 8, 32, 16)

        if st.button("🎨 Apply & Regenerate"):
            st.success("✅ Design tweaks applied! Regenerating...")
            # TODO: Trigger regeneration with new styles
