"""
Enhanced Interface - Input Module
Handles user input and form rendering with full accessibility support
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional, Dict

# Import constants
try:
    from streamlit_ui.constants import COLORS, SPACING, DIMENSIONS
    CONSTANTS_AVAILABLE = True
except ImportError:
    CONSTANTS_AVAILABLE = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import core modules
try:
    from core.audit_mode import extract_code_from_zip
    META_AVAILABLE = True
except ImportError as e:
    META_AVAILABLE = False
    IMPORT_ERROR = str(e)


def render_enhanced_interface():
    """
    Render the main creation interface with all features.
    Includes full accessibility support (ARIA labels, keyboard navigation, focus management).
    """

    # Handle clarification flow first
    if st.session_state.get('clarification_needed', False):
        render_clarification_flow()
        return

    # Main input - LARGE and inviting with accessibility
    if CONSTANTS_AVAILABLE:
        label_html = f"""
        <div style='margin: {SPACING['xl']} 0;' role="group" aria-labelledby="project-idea-label">
            <label id="project-idea-label" style='font-size: 16px; font-weight: 600; color: {COLORS['text_primary']}; margin-bottom: 12px; display: block;'>
                💭 Your Idea <span style='color: #ff4444;' aria-label="required">*</span>
            </label>
        </div>
        """
    else:
        label_html = """
        <div style='margin: 20px 0;' role="group" aria-labelledby="project-idea-label">
            <label id="project-idea-label" style='font-size: 16px; font-weight: 600; color: #e8eaf6; margin-bottom: 12px; display: block;'>
                💭 Your Idea <span style='color: #ff4444;' aria-label="required">*</span>
            </label>
        </div>
        """
    st.markdown(label_html, unsafe_allow_html=True)

    project_input = st.text_area(
        "Tell me your big idea (in plain English, no tech talk needed)",
        placeholder="Example: A dog walking app where pet owners book walks and walkers get notified. We're seeing drop-offs at signup.",
        height=140,
        key="project_input",
        label_visibility="collapsed",
        help="Describe your app in 1-2 sentences. I'll figure out the rest! This field is required."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Options grid with accessibility
    if CONSTANTS_AVAILABLE:
        options_html = f"""
        <div style='margin: {SPACING['xxl']} 0 {SPACING['lg']} 0;' role="group" aria-labelledby="options-label">
            <label id="options-label" style='font-size: 16px; font-weight: 600; color: {COLORS['text_primary']};'>
                🎛️ Options
            </label>
            <p style='font-size: 14px; color: {COLORS['text_secondary']}; margin-top: 4px;' id="options-description">
                Customize your app generation process
            </p>
        </div>
        """
    else:
        options_html = """
        <div style='margin: 24px 0 16px 0;' role="group" aria-labelledby="options-label">
            <label id="options-label" style='font-size: 16px; font-weight: 600; color: #e8eaf6;'>
                🎛️ Options
            </label>
            <p style='font-size: 14px; color: #888888; margin-top: 4px;' id="options-description">
                Customize your app generation process
            </p>
        </div>
        """
    st.markdown(options_html, unsafe_allow_html=True)

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

    # Platform selection with accessibility
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div role="group" aria-labelledby="platforms-label">
        <label id="platforms-label" style='font-size: 14px; font-weight: 500;'>
            🎯 Build for these platforms (agents will choose the best tech stack)
        </label>
    </div>
    """, unsafe_allow_html=True)

    platforms = st.multiselect(
        "🎯 **Build for these platforms** (agents will choose the best tech stack)",
        ["Website", "Web App", "iOS", "Android"],
        default=["Web App"],
        help="Select one or more platforms. Don't worry about tech details—agents decide automatically.",
        label_visibility="collapsed"
    )

    # Conditional: Upload existing code with accessibility
    existing_code = None
    code_files = None
    app_url = None

    if has_existing_code or analyze_dropoffs:
        st.markdown("---")
        st.markdown("""
        <div role="region" aria-labelledby="code-upload-heading">
            <h3 id="code-upload-heading">📂 Upload Your Code</h3>
        </div>
        """, unsafe_allow_html=True)

        upload_method = st.radio(
            "How do you want to provide your code?",
            ["Paste code snippet", "Upload ZIP file", "Provide live URL"],
            horizontal=True,
            key="upload_method",
            help="Choose the method that works best for you. All methods support keyboard navigation."
        )

        if upload_method == "Paste code snippet":
            existing_code = st.text_area(
                "Paste your code here:",
                height=200,
                key="code_paste",
                placeholder="Paste your React, Python, Swift, or any other code...",
                help="Paste your source code. The text area supports standard keyboard shortcuts."
            )
            if existing_code:
                # Wrap in temp structure
                code_files = {"main.txt": existing_code}

        elif upload_method == "Upload ZIP file":
            uploaded_file = st.file_uploader(
                "Upload ZIP file containing your project:",
                type=['zip'],
                key="code_zip",
                help="Upload a ZIP with your project files. I'll analyze everything. Press Tab to focus, Enter to open file dialog."
            )
            if uploaded_file:
                try:
                    existing_code = uploaded_file.read()
                    code_files = extract_code_from_zip(existing_code)
                    st.success(f"✅ Extracted {len(code_files)} code files")
                except Exception as e:
                    st.error(f"❌ Failed to extract ZIP: {str(e)}")
                    st.info("💡 **Tip**: Ensure your ZIP file contains valid source code files.")

        else:  # Provide live URL
            app_url = st.text_input(
                "Enter your app's URL:",
                placeholder="http://localhost:3000 or https://myapp.com",
                key="app_url",
                help="I'll crawl this URL to analyze user flows and drop-offs. Include protocol (http:// or https://)."
            )

            if analyze_dropoffs and app_url:
                st.info("💡 **Tip**: For local apps (localhost), make sure it's running before clicking Go!")

                # Optional: Test credentials for auto-auth
                with st.expander("🔐 Test Credentials (Optional for Auth Testing)", expanded=False):
                    st.markdown("""
                    <p id="credentials-description">
                        Provide test credentials if your app requires authentication.
                        These will be used to test authenticated flows.
                    </p>
                    """, unsafe_allow_html=True)

                    test_email = st.text_input(
                        "Test email:",
                        key="test_email",
                        help="Email for test account login"
                    )
                    test_password = st.text_input(
                        "Test password:",
                        type="password",
                        key="test_password",
                        help="Password for test account login. This is stored only in session state."
                    )

                    if test_email and test_password:
                        st.session_state['test_credentials'] = {
                            'email': test_email,
                            'password': test_password
                        }
                        st.success("✅ Test credentials saved for this session")

    # Advanced options (hidden in expander) with accessibility
    with st.expander("⚙️ Advanced Options", expanded=False):
        st.markdown("""
        <div role="region" aria-labelledby="advanced-options-heading">
            <p id="advanced-options-description" style='color: #888888; font-size: 14px; margin-bottom: 16px;'>
                Fine-tune agent behavior and model selection. These are optional settings for advanced users.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Agent Selection** (leave default for automatic)")
        use_custom_workflow = st.checkbox(
            "Use custom workflow YAML",
            key="custom_workflow",
            help="Upload a custom workflow configuration file to control agent behavior"
        )

        if use_custom_workflow:
            st.file_uploader(
                "Upload workflow YAML:",
                type=['yaml', 'yml'],
                key="workflow_yaml",
                help="YAML file defining custom agent workflow"
            )

        st.markdown("**Model Selection**")
        model_preference = st.selectbox(
            "Primary model:",
            ["Haiku (Fast, Recommended)", "Sonnet (Balanced)", "Opus (Highest Quality)"],
            key="model_pref",
            help="Choose the AI model for agent execution. Haiku is fastest, Opus is highest quality."
        )

    # GO BUTTON - BIG and prominent with accessibility
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div role="region" aria-labelledby="submit-section">
            <p id="submit-section" class="sr-only">Submit form to start generation</p>
        </div>
        """, unsafe_allow_html=True)

        go_button = st.button(
            "🚀 GO",
            key="go_button",
            use_container_width=True,
            type="primary",
            help="Start the app generation process. Shortcut: Ctrl+Enter"
        )

    # Add screen reader only CSS for accessibility
    st.markdown("""
    <style>
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }

        /* Focus indicators for keyboard navigation */
        button:focus,
        input:focus,
        textarea:focus,
        select:focus {
            outline: 2px solid #4CAF50 !important;
            outline-offset: 2px;
        }

        /* Skip to content link for screen readers */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: #000;
            color: #fff;
            padding: 8px;
            z-index: 100;
        }

        .skip-link:focus {
            top: 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Execution flow
    if go_button:
        # Validate required fields
        if not project_input:
            st.error("⚠️ Please describe your project first! The 'Your Idea' field is required.")
            # Announce error to screen readers
            st.markdown('<div role="alert" aria-live="assertive" class="sr-only">Error: Project description is required</div>', unsafe_allow_html=True)
            return

        # Validate dependent inputs
        if analyze_dropoffs and not (app_url or code_files):
            st.error("⚠️ For drop-off analysis, provide either a URL or upload code.")
            st.markdown('<div role="alert" aria-live="assertive" class="sr-only">Error: URL or code required for drop-off analysis</div>', unsafe_allow_html=True)
            return

        # Validate URL format if provided
        if app_url and not (app_url.startswith('http://') or app_url.startswith('https://')):
            st.error("⚠️ Please enter a valid URL starting with http:// or https://")
            st.markdown('<div role="alert" aria-live="assertive" class="sr-only">Error: Invalid URL format</div>', unsafe_allow_html=True)
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

        # Announce execution start to screen readers
        st.markdown('<div role="status" aria-live="polite" class="sr-only">Generation started successfully</div>', unsafe_allow_html=True)

        # Import and run execution (delayed import to avoid circular dependency)
        from streamlit_ui.enhanced_interface_execution import run_enhanced_execution
        run_enhanced_execution()


def render_clarification_flow():
    """
    Render clarification questions when system needs more info.
    Includes full accessibility support.
    """

    st.markdown("""
    <div role="region" aria-labelledby="clarification-heading">
        <h2 id="clarification-heading">🤔 Quick Clarification</h2>
        <p id="clarification-description">I need a bit more information to build exactly what you want.</p>
    </div>
    """, unsafe_allow_html=True)

    questions = st.session_state.get('clarification_questions', [])

    if not questions:
        st.error("No clarification questions available.")
        return

    answers = {}

    for idx, question in enumerate(questions):
        st.markdown(f"**Question {idx + 1}:**")
        st.info(question['question'])

        answer = st.text_area(
            f"Your answer for question {idx + 1}:",
            key=f"clarification_{idx}",
            height=100,
            help=f"Answer for: {question['question'][:50]}...",
            label_visibility="collapsed"
        )
        answers[question['key']] = answer

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state['clarification_needed'] = False
            st.rerun()

    with col3:
        if st.button("✅ Submit Answers", use_container_width=True, type="primary"):
            # Validate all questions answered
            if all(answers.values()):
                st.session_state['clarification_answers'] = answers
                st.session_state['clarification_needed'] = False
                st.success("✅ Thanks! Processing your answers...")
                st.rerun()
            else:
                st.error("⚠️ Please answer all questions before submitting.")
                st.markdown('<div role="alert" aria-live="assertive" class="sr-only">Error: All questions must be answered</div>', unsafe_allow_html=True)
