"""
Main user interface for Code Weaver Pro
Simple input + options + "Go" button with progress tracking
"""

import streamlit as st
from streamlit_ui.progress_tracker import ProgressTracker, ProgressPhase
from streamlit_ui.live_terminal import LiveTerminalOutput
from streamlit_ui.results_display import display_results
import zipfile
import io
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import orchestrator
try:
    from core.orchestrator import CodeWeaverOrchestrator
    from core.config import load_config
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    ORCHESTRATOR_AVAILABLE = False
    IMPORT_ERROR = str(e)


def render_main_interface():
    """Render the main creation interface"""

    # Main input - BIG and centered
    project_input = st.text_area(
        "Project Description",
        placeholder="Example: A recipe app where users can save favorites, search by ingredients, and share with friends.",
        height=120,
        key="project_input",
        label_visibility="collapsed"
    )

    # Options row (checkboxes + multiselect)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        do_market_research = st.checkbox(
            "📊 Market research",
            help="Analyze competitors, TAM/SAM/SOM, and get go/no-go decision"
        )

    with col2:
        research_only = st.checkbox(
            "🔍 Research only",
            value=False,
            help="Stop after market research - review results before building",
            disabled=not do_market_research
        )

    with col3:
        has_existing_code = st.checkbox(
            "📦 Upgrade code",
            help="Upload code to improve (paste or zip upload)"
        )

    with col4:
        platforms = st.multiselect(
            "🎯 Platforms",
            ["Website", "Web App", "iOS", "Android"],
            default=["Web App"],
            help="Select target platforms (agents adapt automatically)"
        )

    # Conditional: Upload existing code
    existing_code = None
    if has_existing_code:
        st.markdown("---")
        upload_method = st.radio(
            "Upload method:",
            ["Paste code", "Upload ZIP"],
            horizontal=True
        )

        if upload_method == "Paste code":
            existing_code = st.text_area(
                "Paste your code here:",
                height=200,
                key="code_paste"
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload ZIP file:",
                type=['zip'],
                key="code_zip"
            )
            if uploaded_file:
                existing_code = uploaded_file.read()

    # GO BUTTON - Big and prominent
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        go_button = st.button("🚀 GO", key="go_button", use_container_width=True)

    # Execution flow
    if go_button:
        if not project_input:
            st.error("⚠️ Please describe your project first!")
            return

        # Store execution parameters in session state (use different keys to avoid widget conflicts)
        st.session_state['execution_started'] = True
        st.session_state['exec_project_input'] = project_input
        st.session_state['exec_do_market_research'] = do_market_research
        st.session_state['exec_research_only'] = research_only
        st.session_state['exec_existing_code'] = existing_code
        st.session_state['exec_platforms'] = platforms

        # Create containers for live updates
        st.markdown("---")
        progress_container = st.container()
        terminal_container = st.container()
        results_container = st.container()

        # Display progress tracker
        with progress_container:
            st.markdown("### 📊 Progress")
            progress_tracker = ProgressTracker()
            progress_tracker.render()

        # Display live terminal
        with terminal_container:
            st.markdown("### 💻 Live Output")
            terminal = LiveTerminalOutput()

        # Run real orchestration if available, otherwise demo
        if ORCHESTRATOR_AVAILABLE:
            run_real_execution(
                project_input,
                do_market_research,
                research_only,
                existing_code,
                platforms,
                progress_tracker,
                terminal,
                results_container
            )
        else:
            st.error(f"⚠️ Orchestrator not available: {IMPORT_ERROR}")
            st.info("Running demo mode instead...")
            run_demo_execution(progress_tracker, terminal, results_container)


def run_real_execution(
    project_input: str,
    do_market_research: bool,
    research_only: bool,
    existing_code: str,
    platforms: list,
    progress_tracker: ProgressTracker,
    terminal: LiveTerminalOutput,
    results_container
):
    """
    Run real orchestration with CodeWeaverOrchestrator
    """
    try:
        # Load configuration
        config = load_config()

        # Setup callbacks for live updates
        def progress_callback(phase: str, progress: float):
            """Update progress tracker"""
            phase_map = {
                'planning': ProgressPhase.PLANNING,
                'drafting': ProgressPhase.DRAFTING,
                'testing': ProgressPhase.TESTING,
                'done': ProgressPhase.DONE,
            }
            if phase in phase_map:
                progress_tracker.set_phase(phase_map[phase])
                progress_tracker.update_phase_progress(progress)

        def terminal_callback(message: str, level: str = 'info'):
            """Update terminal output"""
            if level == 'success':
                terminal.add_success(message)
            elif level == 'error':
                terminal.add_error(message)
            elif level == 'warning':
                terminal.add_warning(message)
            else:
                terminal.add_info(message)

        # Attach callbacks to config
        config['orchestration']['progress_callback'] = progress_callback
        config['orchestration']['terminal_callback'] = terminal_callback

        # Create orchestrator
        orchestrator = CodeWeaverOrchestrator(config)

        # Run orchestration
        terminal.add_info("🚀 Starting Code Weaver Pro orchestration...")
        terminal.add_info(f"📝 Project: {project_input[:100]}...")
        terminal.add_info(f"🎯 Platforms: {', '.join(platforms)}")

        result = orchestrator.run(
            user_input=project_input,
            platforms=platforms,
            do_market_research=do_market_research,
            research_only=research_only,
            existing_code=existing_code
        )

        # Display results
        with results_container:
            st.markdown("---")

            if result['status'] == 'success':
                display_results(result)
                terminal.add_success("🎉 Project generation complete!")

            elif result['status'] == 'research_complete':
                # Research-only mode completed
                st.success("### ✅ Market Research Complete!")
                display_market_research(result)

                # Show intermediate outputs
                if result.get('agent_outputs'):
                    display_intermediate_outputs(result['agent_outputs'])

            elif result['status'] == 'no-go':
                st.warning("### ⚠️ Market Research: No-Go Decision")
                display_market_research(result)
                st.info("💡 **Recommendation:** Consider refining your idea based on the analysis above.")

            elif result['status'] == 'error':
                st.error("### ❌ Error During Execution")
                st.markdown(f"**Error:** {result['error']}")
                if result.get('partial_project_path'):
                    st.info(f"Partial project saved to: {result['partial_project_path']}")

    except Exception as e:
        terminal.add_error(f"Fatal error: {str(e)}")
        st.error(f"### ❌ Fatal Error\n\n{str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_market_research(result: dict):
    """Display market research results in a formatted way"""
    research_data = result.get('agent_outputs', {}).get('market_research', '')

    if not research_data:
        st.info("No market research data available.")
        return

    st.markdown("### 📊 Market Analysis")

    # Parse research data
    lines = research_data.split('\n')
    competitors = []
    tam = sam = som = decision = reasoning = ""

    current_section = None
    for line in lines:
        line_upper = line.upper()
        if 'COMPETITORS:' in line_upper:
            current_section = 'competitors'
            competitors_text = line.split(':', 1)[1] if ':' in line else ''
            continue
        elif 'TAM:' in line_upper:
            current_section = 'tam'
            tam = line.split(':', 1)[1].strip() if ':' in line else line
            continue
        elif 'SAM:' in line_upper:
            current_section = 'sam'
            sam = line.split(':', 1)[1].strip() if ':' in line else line
            continue
        elif 'SOM:' in line_upper:
            current_section = 'som'
            som = line.split(':', 1)[1].strip() if ':' in line else line
            continue
        elif 'DECISION:' in line_upper:
            current_section = 'decision'
            decision = line.split(':', 1)[1].strip() if ':' in line else line
            continue
        elif 'REASONING:' in line_upper:
            current_section = 'reasoning'
            reasoning = line.split(':', 1)[1].strip() if ':' in line else ''
            continue

        # Append to current section
        if current_section == 'competitors' and line.strip():
            competitors.append(line.strip())
        elif current_section == 'reasoning' and line.strip():
            reasoning += ' ' + line.strip()

    # Display in columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Market Size")
        if tam:
            st.markdown(f"**TAM:** {tam}")
        if sam:
            st.markdown(f"**SAM:** {sam}")
        if som:
            st.markdown(f"**SOM:** {som}")

        if competitors:
            st.markdown("#### 🏢 Competitors")
            for comp in competitors[:5]:  # Show top 5
                st.markdown(f"- {comp}")

    with col2:
        st.markdown("#### 🎲 Decision")
        # Extract clean decision text
        decision_clean = decision.strip() if decision else "Pending Analysis"
        if 'GO' in decision.upper() and 'NO-GO' not in decision.upper():
            st.markdown(f"""
            <div style="background-color: #1e4620; border-left: 4px solid #44ff44; padding: 16px; border-radius: 4px; margin: 8px 0;">
                <div style="font-size: 24px; font-weight: bold; color: #44ff44;">✅ {decision_clean}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #4a3520; border-left: 4px solid #ffaa44; padding: 16px; border-radius: 4px; margin: 8px 0;">
                <div style="font-size: 24px; font-weight: bold; color: #ffaa44;">⚠️ {decision_clean}</div>
            </div>
            """, unsafe_allow_html=True)

        if reasoning:
            st.markdown("#### 💭 Reasoning")
            st.markdown(reasoning)

    # Professional investor-ready research report
    st.markdown("---")
    st.markdown("### 📄 Full Market Research Report")
    st.markdown("*Professional analysis for investor presentation*")

    # Download button for the report
    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        report_text = _format_investor_report(research_data, tam, sam, som, decision, reasoning, competitors)
        st.download_button(
            label="📥 Download Report (TXT)",
            data=report_text,
            file_name="market_research_report.txt",
            mime="text/plain",
            use_container_width=True
        )

    # Display formatted report
    with st.expander("📊 View Full Research Report", expanded=False):
        st.markdown(f"""
        <div style="background-color: #ffffff; color: #000000; padding: 30px; border-radius: 8px;
                    font-family: 'Georgia', serif; line-height: 1.8; max-width: 100%; overflow-x: auto;">
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #667eea; padding-bottom: 20px;">
                <h1 style="color: #667eea; font-size: 28px; margin: 0;">Market Research Report</h1>
                <p style="color: #666; font-size: 14px; margin-top: 8px;">Generated by Code Weaver Pro Research Agent</p>
                <p style="color: #999; font-size: 12px;">Date: {datetime.now().strftime('%B %d, %Y')}</p>
            </div>

            <div style="margin-bottom: 30px;">
                <h2 style="color: #667eea; font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Executive Summary</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #667eea; margin: 15px 0;">
                    <p style="margin: 0;"><strong>Decision:</strong> {decision_clean}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Market Opportunity:</strong> ${som} SOM within ${tam} TAM</p>
                </div>
            </div>

            <div style="margin-bottom: 30px;">
                <h2 style="color: #667eea; font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Market Size Analysis</h2>
                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Metric</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #ddd;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong>TAM</strong> (Total Addressable Market)</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">{tam}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong>SAM</strong> (Serviceable Addressable Market)</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">{sam}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;"><strong>SOM</strong> (Serviceable Obtainable Market)</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">{som}</td>
                    </tr>
                </table>
            </div>

            <div style="margin-bottom: 30px;">
                <h2 style="color: #667eea; font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Competitive Landscape</h2>
                <ul style="list-style: none; padding: 0; margin: 15px 0;">
                    {"".join([f'<li style="padding: 8px 0; border-bottom: 1px solid #eee;">• {comp}</li>' for comp in competitors[:10]])}
                </ul>
            </div>

            <div style="margin-bottom: 30px;">
                <h2 style="color: #667eea; font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Strategic Analysis</h2>
                <p style="text-align: justify; color: #333;">{reasoning}</p>
            </div>

            <div style="margin-bottom: 30px;">
                <h2 style="color: #667eea; font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">Complete Research Output</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 4px; font-family: 'Courier New', monospace;
                            font-size: 13px; white-space: pre-wrap; overflow-x: auto; max-height: 600px; overflow-y: auto;">
{research_data}
                </div>
            </div>

            <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #667eea; text-align: center; color: #999; font-size: 12px;">
                <p>This report was generated using AI-powered market research analysis.</p>
                <p>Generated by Code Weaver Pro • {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _format_investor_report(research_data: str, tam: str, sam: str, som: str,
                           decision: str, reasoning: str, competitors: list) -> str:
    """Format research data as a professional investor report"""
    from datetime import datetime

    report = f"""
================================================================================
                        MARKET RESEARCH REPORT
================================================================================

Generated by: Code Weaver Pro Research Agent
Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Report Type: Competitive Analysis & Market Sizing

================================================================================
EXECUTIVE SUMMARY
================================================================================

Decision: {decision.strip() if decision else 'Pending Analysis'}

Market Opportunity: {som} SOM within {tam} TAM

This report provides a comprehensive analysis of the market opportunity,
competitive landscape, and strategic recommendations for the proposed venture.

================================================================================
MARKET SIZE ANALYSIS
================================================================================

Total Addressable Market (TAM):
{tam}

Serviceable Addressable Market (SAM):
{sam}

Serviceable Obtainable Market (SOM):
{som}

The market sizing follows a top-down approach, starting with the total market
opportunity (TAM), narrowing to the serviceable portion relevant to our business
model (SAM), and finally estimating the realistic market share we can capture
in the near term (SOM).

================================================================================
COMPETITIVE LANDSCAPE
================================================================================

Key Competitors Identified:

"""

    for i, comp in enumerate(competitors, 1):
        report += f"{i}. {comp}\n"

    if not competitors:
        report += "No direct competitors identified at this time.\n"

    report += f"""

Competitive analysis indicates {"a crowded market requiring differentiation" if len(competitors) > 5 else "moderate competition with room for new entrants"}.

================================================================================
STRATEGIC ANALYSIS & RECOMMENDATIONS
================================================================================

{reasoning}

================================================================================
DETAILED RESEARCH OUTPUT
================================================================================

{research_data}

================================================================================
METHODOLOGY & SOURCES
================================================================================

This market research was conducted using AI-powered analysis with the following
methodology:

1. Market Sizing: Top-down approach using industry reports and comparable
   company analysis

2. Competitive Analysis: Identification of direct and indirect competitors
   through market scanning and feature comparison

3. Strategic Assessment: Evaluation of market opportunity based on size,
   growth potential, competitive dynamics, and strategic fit

4. Go/No-Go Decision: Multi-factor analysis considering market attractiveness,
   competitive positioning, and execution feasibility

Sources:
- Industry market research databases
- Competitive intelligence platforms
- Public company filings and reports
- Market trend analysis
- Expert knowledge synthesis

Note: This report uses AI-generated analysis. For investment decisions, please
validate findings with additional primary research and financial due diligence.

================================================================================
DISCLAIMER
================================================================================

This report is provided for informational purposes only and does not constitute
investment advice. Market estimates are based on available data and AI analysis
as of the report generation date. Actual market conditions may vary. Please
consult with qualified financial advisors before making investment decisions.

================================================================================
                    END OF REPORT
================================================================================

Generated by Code Weaver Pro
© {datetime.now().year} All Rights Reserved
"""

    return report


def display_intermediate_outputs(agent_outputs: dict):
    """Display intermediate agent outputs in expandable sections"""
    st.markdown("---")
    st.markdown("### 🔍 Agent Outputs")
    st.markdown("*Expand to view detailed outputs from each AI agent*")

    # Define display order and friendly names
    agent_display_map = {
        'meta_prompt': ('🔍 Meta Prompt', 'Expanded project specification'),
        'verification_planning': ('✅ Planning Verification', 'Hallucination check for planning phase'),
        'challenger': ('🤔 Challenger Review', 'Critical analysis and gap identification'),
        'pm_plan': ('📋 PM Sprint Plan', 'Project management and task prioritization'),
        'ideas': ('💡 Ideas Brainstorm', 'Creative solutions and innovations'),
        'designs': ('🎨 UI/UX Design', 'Design architecture and user experience'),
        'senior_review': ('👨‍💻 Senior Engineering Review', 'Technical architecture assessment'),
        'reflection_1': ('🔄 Phase 1 Reflection', 'Synthesis of planning and design'),
        'verification_drafting': ('✅ Drafting Verification', 'Consistency check for design phase'),
        'verification_testing': ('✅ Testing Verification', 'Code validation against requirements'),
        'reflection_2': ('🔄 Phase 2 Reflection', 'Implementation quality review'),
        'scorer': ('📊 Quality Scores', 'Application evaluation metrics'),
    }

    for agent_key, (title, description) in agent_display_map.items():
        if agent_key in agent_outputs:
            with st.expander(f"{title} - {description}"):
                output = agent_outputs[agent_key]

                # Special formatting for verification outputs
                if agent_key.startswith('verification_'):
                    if 'VERDICT: PASS' in output.upper():
                        st.success("✅ Verification PASSED - No hallucinations detected")
                    elif 'VERDICT: WARN' in output.upper():
                        st.warning("⚠️ Verification WARNING - Minor issues found")
                    elif 'VERDICT: FAIL' in output.upper():
                        st.error("❌ Verification FAILED - Critical issues detected")

                st.markdown(output)


def run_demo_execution(progress_tracker, terminal, results_container):
    """
    Demo execution to show UI components
    This will be replaced with actual orchestration in Week 2
    """
    import time

    # Phase 1: Planning
    progress_tracker.set_phase(ProgressPhase.PLANNING)
    terminal.add_info("Starting meta prompt expansion...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(0.3)
    terminal.add_info("Analyzing project requirements...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(0.6)
    terminal.add_success("Meta prompt expansion complete")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(1.0)
    terminal.add_info("Challenger reviewing plan...")
    time.sleep(0.5)

    # Phase 2: Drafting
    progress_tracker.set_phase(ProgressPhase.DRAFTING)
    terminal.add_info("PM creating sprint plan...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(0.3)
    terminal.add_info("Design team creating UI/UX...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(0.6)
    terminal.add_info("Senior engineer reviewing architecture...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(1.0)
    terminal.add_success("Design and architecture complete")

    # Phase 3: Testing
    progress_tracker.set_phase(ProgressPhase.TESTING)
    terminal.add_info("Running Playwright tests...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(0.4)
    terminal.add_warning("Found 2 minor issues")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(0.7)
    terminal.add_info("QA agent debugging issues...")
    time.sleep(0.5)

    progress_tracker.update_phase_progress(1.0)
    terminal.add_success("All tests passed!")

    # Phase 4: Done
    progress_tracker.set_phase(ProgressPhase.DONE)
    terminal.add_success("Capturing screenshots...")
    time.sleep(0.5)

    terminal.add_success("Scoring application...")
    time.sleep(0.5)

    terminal.add_success("✅ All done!")

    # Display demo results
    with results_container:
        st.markdown("---")
        demo_results = {
            'project_name': 'Recipe Sharing App',
            'description': 'A beautiful recipe app where users can save favorites, search by ingredients, and share with friends.',
            'features': [
                'User authentication and profiles',
                'Recipe search with ingredient filtering',
                'Favorite recipes collection',
                'Social sharing capabilities',
                'Responsive mobile design'
            ],
            'scores': {
                'speed': 8,
                'mobile': 9,
                'intuitiveness': 9,
                'functionality': 8
            },
            'screenshots': [],  # No screenshots in demo
            'recommendations': [
                'Add offline caching for better performance',
                'Implement push notifications for recipe updates',
                'Consider adding nutrition information'
            ],
            'project_path': None
        }

        display_results(demo_results)

        st.info("ℹ️ **Demo Mode**: This is a demonstration of the UI. The actual orchestration with agent execution will be implemented in Week 2!")


def download_zip(project_path):
    """Create downloadable ZIP of project"""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, project_path)
                zip_file.write(file_path, arc_name)

    zip_buffer.seek(0)
    return zip_buffer
