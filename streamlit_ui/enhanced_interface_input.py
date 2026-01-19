"""
Enhanced Interface - Input Module
Handles user input and form rendering with full accessibility support
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Import constants
try:
    from streamlit_ui.constants import (
        COLORS, SPACING, DIMENSIONS, GRADIENTS, TYPOGRAPHY,
        TYPOGRAPHY_CSS, INTERFACE_POLISH_CSS
    )
    CONSTANTS_AVAILABLE = True
except ImportError:
    CONSTANTS_AVAILABLE = False
    # Fallback CSS for polish if constants not available
    TYPOGRAPHY_CSS = ""
    INTERFACE_POLISH_CSS = ""

# Import loading states for form progress
try:
    from streamlit_ui.loading_states import render_form_progress, render_character_counter
    LOADING_STATES_AVAILABLE = True
except ImportError:
    LOADING_STATES_AVAILABLE = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import core modules
try:
    from core.audit_mode import extract_code_from_zip
    META_AVAILABLE = True
except ImportError as e:
    META_AVAILABLE = False
    IMPORT_ERROR = str(e)


def _calculate_form_progress() -> tuple:
    """Calculate form completion progress based on filled fields."""
    steps = ["Your Idea", "Business", "Brand", "Scope", "Contact"]

    # Check each section's completion
    idea_complete = bool(st.session_state.get('project_input', '').strip())
    business_complete = bool(
        st.session_state.get('business_name', '') or
        st.session_state.get('target_users', '')
    )
    brand_complete = bool(
        st.session_state.get('brand_personality', []) or
        st.session_state.get('existing_colors', '')
    )
    scope_complete = bool(
        st.session_state.get('budget_range', 'Not specified') != 'Not specified' or
        st.session_state.get('success_metrics', [])
    )
    contact_complete = bool(
        st.session_state.get('company_name', '') or
        st.session_state.get('contact_email', '')
    )

    # Determine current step (furthest incomplete section)
    if not idea_complete:
        current = 0
    elif not business_complete:
        current = 1
    elif not brand_complete:
        current = 2
    elif not scope_complete:
        current = 3
    elif not contact_complete:
        current = 4
    else:
        current = 5  # All complete

    return steps, current


def _get_section_status(section: str) -> tuple:
    """Get status icon and color for a form section."""
    if section == "business":
        complete = bool(
            st.session_state.get('business_name', '') and
            st.session_state.get('target_users', '')
        )
        partial = bool(
            st.session_state.get('business_name', '') or
            st.session_state.get('target_users', '')
        )
    elif section == "brand":
        complete = bool(
            st.session_state.get('brand_personality', []) and
            st.session_state.get('design_style', 'Let AI decide') != 'Let AI decide'
        )
        partial = bool(
            st.session_state.get('brand_personality', []) or
            st.session_state.get('existing_colors', '')
        )
    elif section == "scope":
        complete = bool(
            st.session_state.get('budget_range', 'Not specified') != 'Not specified' and
            st.session_state.get('timeline', 'Not specified') != 'Not specified'
        )
        partial = bool(
            st.session_state.get('success_metrics', []) or
            st.session_state.get('budget_range', 'Not specified') != 'Not specified'
        )
    elif section == "contact":
        complete = bool(
            st.session_state.get('company_name', '') and
            st.session_state.get('contact_email', '')
        )
        partial = bool(
            st.session_state.get('company_name', '') or
            st.session_state.get('contact_email', '')
        )
    else:
        complete = False
        partial = False

    if complete:
        return "✓", "#34d399", "Complete"
    elif partial:
        return "●", "#667eea", "In Progress"
    else:
        return "○", "#6b7280", "Not Started"


def render_enhanced_interface() -> None:
    """
    Render the main creation interface with all features.
    Includes full accessibility support (ARIA labels, keyboard navigation, focus management).
    Enhanced with business context fields for richer report generation.
    """

    # Inject unified polish CSS (Issues #1, #2, #4, #8, #9, #10)
    if CONSTANTS_AVAILABLE:
        st.markdown(TYPOGRAPHY_CSS, unsafe_allow_html=True)
        st.markdown(INTERFACE_POLISH_CSS, unsafe_allow_html=True)

    # Handle clarification flow first
    if st.session_state.get('clarification_needed', False):
        render_clarification_flow()
        return

    # ===== FORM PROGRESS INDICATOR =====
    if LOADING_STATES_AVAILABLE:
        steps, current_step = _calculate_form_progress()
        render_form_progress(steps, current_step, show_percentage=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ===== SECTION 1: Your Idea (Required) - PROMINENT STYLING =====
    st.markdown("""
    <div class="primary-input-container card-hover section-compact" role="group" aria-labelledby="project-idea-label" style="padding: 24px; background: rgba(102, 126, 234, 0.08); border-radius: 16px; border: 1px solid rgba(102, 126, 234, 0.2); transition: all 0.3s ease;">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
            <div style="width: 56px; height: 56px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 14px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);">
                <span style="font-size: 28px;">🧠</span>
            </div>
            <div>
                <label id="project-idea-label" class="primary-input-label" style="font-size: 20px; font-weight: 700; color: #E5E7EB; display: block; margin-bottom: 4px;">
                    Your Idea <span class="badge badge-primary" style="font-size: 11px; padding: 3px 8px; margin-left: 8px; vertical-align: middle;">Required</span>
                </label>
                <p class="primary-input-helper" style="color: #94A3B8; font-size: 14px; margin: 0;">
                    Describe your app in 1-2 sentences. This is the only required field.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    project_input = st.text_area(
        "Tell me your big idea (in plain English, no tech talk needed)",
        placeholder="e.g., A productivity app for freelancers that tracks time, generates invoices, and syncs with calendars. Users are abandoning during onboarding.",
        height=130,  # Reduced height per Issue #2
        key="project_input",
        label_visibility="collapsed",
        help="Describe your app in 1-2 sentences. Be specific about your target users and key features. I'll figure out the rest!",
        on_change=lambda: st.session_state.get('project_input')
    )

    # Character counter with feedback
    if LOADING_STATES_AVAILABLE:
        char_count = len(project_input) if project_input else 0
        render_character_counter(char_count, min_chars=20, max_chars=500, optimal_min=50)

    # ===== SECTION 2: Business Context (For richer reports) =====
    st.markdown("<br>", unsafe_allow_html=True)

    # Show section status with WCAG AA compliant colors
    biz_icon, biz_color, biz_status = _get_section_status("business")
    st.markdown(f"""
    <div class="expander-status" style="color: {biz_color}; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;" role="status" aria-label="Business section status: {biz_status}">
        <span aria-hidden="true">{biz_icon}</span>
        <span>{biz_status}</span>
        <span style="color: #A3B1C6; font-size: 11px;">• 2 fields recommended</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🏢 Business Context (Recommended)", expanded=False):
        st.markdown("""
        <p style='color: #CBD5E1; font-size: 14px; margin-bottom: 16px;'>
            Fill these in to get a polished, client-ready proposal like the Brew & Co report.
        </p>
        """, unsafe_allow_html=True)

        biz_col1, biz_col2 = st.columns(2)

        with biz_col1:
            business_name = st.text_input(
                "Business/Project Name",
                placeholder="e.g., Brew & Co, PetPal, FitTrack",
                key="business_name",
                help="The name that will appear on the cover page and throughout the proposal"
            )

            industry = st.selectbox(
                "Industry",
                [
                    "Not specified",
                    "Restaurant / Food Service",
                    "Retail / E-commerce",
                    "Healthcare / Wellness",
                    "Finance / Fintech",
                    "Education / EdTech",
                    "Real Estate",
                    "Travel / Hospitality",
                    "Professional Services",
                    "Entertainment / Media",
                    "SaaS / Software",
                    "Non-profit",
                    "Other"
                ],
                key="industry",
                help="Helps us provide industry-specific insights and competitor analysis"
            )

        with biz_col2:
            target_users = st.text_input(
                "Target Users",
                placeholder="e.g., Young professionals, Pet owners, Busy parents",
                key="target_users",
                help="Who will use this app? Helps us design the right user experience"
            )

            business_stage = st.selectbox(
                "Business Stage",
                [
                    "Just an idea",
                    "Have a prototype",
                    "Launched but need improvements",
                    "Scaling up"
                ],
                key="business_stage",
                help="Helps us tailor recommendations to your current situation"
            )

    # ===== SECTION 3: Brand & Design Preferences =====
    brand_icon, brand_color, brand_status = _get_section_status("brand")
    st.markdown(f"""
    <div class="expander-status" style="color: {brand_color}; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;" role="status" aria-label="Brand section status: {brand_status}">
        <span aria-hidden="true">{brand_icon}</span>
        <span>{brand_status}</span>
        <span style="color: #A3B1C6; font-size: 11px;">• Optional</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🎨 Brand & Design", expanded=False):
        st.markdown("""
        <p style='color: #CBD5E1; font-size: 14px; margin-bottom: 16px;'>
            Already have brand guidelines? Let us know so the design feels like you.
        </p>
        """, unsafe_allow_html=True)

        brand_col1, brand_col2 = st.columns(2)

        with brand_col1:
            brand_personality = st.multiselect(
                "Brand Personality",
                [
                    "Professional",
                    "Friendly",
                    "Bold",
                    "Minimalist",
                    "Playful",
                    "Luxurious",
                    "Trustworthy",
                    "Innovative",
                    "Warm",
                    "Modern"
                ],
                default=[],
                key="brand_personality",
                help="Select words that describe how your brand should feel"
            )

            existing_colors = st.text_input(
                "Existing Brand Colors (hex codes)",
                placeholder="e.g., #00B894, #2D3436",
                key="existing_colors",
                help="If you have brand colors, enter them here (comma-separated)"
            )

        with brand_col2:
            design_style = st.selectbox(
                "Design Style Preference",
                [
                    "Let AI decide",
                    "Clean & Minimal",
                    "Bold & Colorful",
                    "Dark Mode",
                    "Corporate / Professional",
                    "Fun & Playful",
                    "Elegant / Luxury"
                ],
                key="design_style",
                help="Overall visual direction for the app"
            )

            competitor_apps = st.text_input(
                "Apps You Admire (for inspiration)",
                placeholder="e.g., Airbnb, Stripe, Notion",
                key="competitor_apps",
                help="Apps whose design or UX you'd like to emulate"
            )

    # ===== SECTION 4: Project Scope & Budget =====
    scope_icon, scope_color, scope_status = _get_section_status("scope")
    st.markdown(f"""
    <div class="expander-status" style="color: {scope_color}; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;" role="status" aria-label="Scope section status: {scope_status}">
        <span aria-hidden="true">{scope_icon}</span>
        <span>{scope_status}</span>
        <span style="color: #A3B1C6; font-size: 11px;">• For accurate estimates</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("💰 Project Scope", expanded=False):
        st.markdown("""
        <p style='color: #CBD5E1; font-size: 14px; margin-bottom: 16px;'>
            Help us provide realistic investment ranges and timelines.
        </p>
        """, unsafe_allow_html=True)

        scope_col1, scope_col2 = st.columns(2)

        with scope_col1:
            budget_range = st.selectbox(
                "Budget Range",
                [
                    "Not specified",
                    "Under $5,000",
                    "$5,000 - $15,000",
                    "$15,000 - $35,000",
                    "$35,000 - $65,000",
                    "$65,000 - $100,000",
                    "$100,000+"
                ],
                key="budget_range",
                help="Helps us recommend features that fit your investment level"
            )

            timeline = st.selectbox(
                "Timeline Expectations",
                [
                    "Not specified",
                    "ASAP (under 4 weeks)",
                    "Standard (4-8 weeks)",
                    "Flexible (8-12 weeks)",
                    "Long-term (3+ months)"
                ],
                key="timeline",
                help="When do you need this launched?"
            )

        with scope_col2:
            success_metrics = st.multiselect(
                "What Success Looks Like",
                [
                    "More users signing up",
                    "Higher conversion rates",
                    "Reduced drop-offs",
                    "Increased revenue",
                    "Better user engagement",
                    "Faster task completion",
                    "Higher customer satisfaction",
                    "Lower support tickets"
                ],
                default=[],
                key="success_metrics",
                help="Select the outcomes that matter most to you"
            )

            known_competitors = st.text_input(
                "Known Competitors",
                placeholder="e.g., DoorDash, Uber Eats, Grubhub",
                key="known_competitors",
                help="Competitors you're aware of in your space"
            )

    # ===== SECTION 5: Contact Info (For proposals) =====
    contact_icon, contact_color, contact_status = _get_section_status("contact")
    st.markdown(f"""
    <div class="expander-status" style="color: {contact_color}; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;" role="status" aria-label="Contact section status: {contact_status}">
        <span aria-hidden="true">{contact_icon}</span>
        <span>{contact_status}</span>
        <span style="color: #A3B1C6; font-size: 11px;">• For proposal footer</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📧 Your Info", expanded=False):
        st.markdown("""
        <p style='color: #CBD5E1; font-size: 14px; margin-bottom: 16px;'>
            Add your details for a branded, shareable proposal.
        </p>
        """, unsafe_allow_html=True)

        contact_col1, contact_col2 = st.columns(2)

        with contact_col1:
            company_name = st.text_input(
                "Your Company/Agency Name",
                placeholder="e.g., Acme Studios",
                key="company_name",
                help="Appears in proposal footer"
            )

            contact_email = st.text_input(
                "Contact Email",
                placeholder="hello@yourcompany.com",
                key="contact_email",
                help="For the 'Next Steps' section"
            )

        with contact_col2:
            company_tagline = st.text_input(
                "Tagline (optional)",
                placeholder="e.g., Digital Transformation Specialists",
                key="company_tagline",
                help="Your company's tagline for the footer"
            )

            contact_phone = st.text_input(
                "Phone (optional)",
                placeholder="(555) 123-4567",
                key="contact_phone",
                help="Contact phone for the proposal"
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

        # Research only - with clear disabled state explanation
        research_only_label = "🔍 Research only (don't build yet)"
        if not do_market_research:
            research_only_label = "🔍 Research only (enable market check first)"

        research_only = st.checkbox(
            research_only_label,
            value=False,
            help="Stop after market research to review findings before building. Requires 'Quick market check' to be enabled.",
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
        label_visibility="collapsed",
        key="platforms"
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

    # Model Selection - VISIBLE for important decision
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div role="group" aria-labelledby="model-label">
        <label id="model-label" style='font-size: 14px; font-weight: 500;'>
            🧠 AI Model (affects speed and quality)
        </label>
    </div>
    """, unsafe_allow_html=True)

    model_cols = st.columns([2, 1])
    with model_cols[0]:
        model_preference = st.selectbox(
            "🧠 AI Model",
            ["Haiku (Fast, Recommended)", "Sonnet (Balanced)", "Opus (Highest Quality)"],
            key="model_pref",
            help="Haiku: Fast & affordable | Sonnet: Balanced | Opus: Highest quality but slower",
            label_visibility="collapsed"
        )
    with model_cols[1]:
        # Show model info based on selection
        if "Haiku" in model_preference:
            st.caption("⚡ ~30s generation")
        elif "Sonnet" in model_preference:
            st.caption("⏱️ ~60s generation")
        else:
            st.caption("🎯 ~90s generation")

    # Advanced options (hidden in expander) with accessibility
    with st.expander("⚙️ Advanced Options", expanded=False):
        st.markdown("""
        <div role="region" aria-labelledby="advanced-options-heading">
            <p id="advanced-options-description" style='color: #888888; font-size: 14px; margin-bottom: 16px;'>
                Fine-tune agent behavior with custom workflows.
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
/* Enhanced error input styling - red border, tint, message */
        div[data-testid="stTextInput"] > div > div > input,
        div[data-testid="stTextArea"] > div > div > textarea {
            background: linear-gradient(135deg, #252844 0%, #1e2139 100%) !important;
            border: 2px solid #3d4466 !important;
            border-radius: 12px !important;
            color: #f1f5f9 !important;
            padding: 14px 18px !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }

        /* Error state: red border and background tint */
        div[data-testid="stTextInput"] > div > div > input:invalid,
        div[data-testid="stTextInput"] > div > div > input.ng-invalid,
        div[data-testid="stTextArea"] > div > div > textarea:invalid {
            border-color: #ef4444 !important;
            box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.3) !important;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.08) 100%) !important;
        }

        /* Error help/message text below input */
        div[data-testid="stTextInput"] label small,
        div[data-testid="stTextArea"] label small {
            color: #f87171 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            margin-top: 6px !important;
        }

        /* Enhance st.error blocks */
        [data-testid="stAlert"] section {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.15) 100%) !important;
            border: 1px solid #ef4444 !important;
            border-radius: 12px !important;
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

        # Store parameters - including all business context fields
        st.session_state['execution_started'] = True
        st.session_state['exec_params'] = {
            # Core inputs
            'project_input': project_input,
            'do_market_research': do_market_research,
            'research_only': research_only,
            'analyze_dropoffs': analyze_dropoffs,
            'existing_code': existing_code,
            'code_files': code_files,
            'app_url': app_url,
            'platforms': platforms,
            'model_preference': model_preference,

            # Business context (for rich proposals)
            'business_name': st.session_state.get('business_name', ''),
            'industry': st.session_state.get('industry', 'Not specified'),
            'target_users': st.session_state.get('target_users', ''),
            'business_stage': st.session_state.get('business_stage', 'Just an idea'),

            # Brand & Design preferences
            'brand_personality': st.session_state.get('brand_personality', []),
            'existing_colors': st.session_state.get('existing_colors', ''),
            'design_style': st.session_state.get('design_style', 'Let AI decide'),
            'competitor_apps': st.session_state.get('competitor_apps', ''),

            # Project scope
            'budget_range': st.session_state.get('budget_range', 'Not specified'),
            'timeline': st.session_state.get('timeline', 'Not specified'),
            'success_metrics': st.session_state.get('success_metrics', []),
            'known_competitors': st.session_state.get('known_competitors', ''),

            # Contact info (for proposal footer)
            'company_name': st.session_state.get('company_name', ''),
            'company_tagline': st.session_state.get('company_tagline', ''),
            'contact_email': st.session_state.get('contact_email', ''),
            'contact_phone': st.session_state.get('contact_phone', '')
        }

        # Announce execution start to screen readers
        st.markdown('<div role="status" aria-live="polite" class="sr-only">Generation started successfully</div>', unsafe_allow_html=True)

        # Import and run execution (delayed import to avoid circular dependency)
        from streamlit_ui.enhanced_interface_execution import run_enhanced_execution
        run_enhanced_execution()


def render_clarification_flow() -> None:
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

        answer = st