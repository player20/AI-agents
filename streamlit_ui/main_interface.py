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

    # Introductory section with instructions
    st.markdown("## 🚀 Code Weaver Pro")
    st.markdown("Welcome to Code Weaver Pro! This tool helps you create a new project by providing market research, generating code, and more.")
    st.markdown("To get started, please follow these steps:")
    st.markdown("1. Describe your project in the input below.")
    st.markdown("2. Select the relevant options to customize your project.")
    st.markdown("3. Click the 'Start' button to begin the creation process.")

    # Main input - BIG and centered
    st.markdown("### What do you want to build?")
    project_input = st.text_area(
        "Describe your project",
        placeholder="Example: A recipe app where users can save favorites, search by ingredients, and share with friends.",
        height=120,
        key="project_input",
        label_visibility="visible",
        help="Be specific about features, target users, and key functionality"
    )

    # Options - 2 rows for better mobile layout
    st.markdown("### Options")

    # First row - checkboxes
    col1, col2, col3 = st.columns(3)

    with col1:
        do_market_research = st.checkbox(
            "📊 Market research",
            help="Analyze competitors, TAM/SAM/SOM, and get go/no-go decision"
        )

    with col2:
        # Show explanation when disabled
        if not do_market_research:
            research_only = st.checkbox(
                "🔍 Research only",
                value=False,
                disabled=True,
                help="⚠️ Enable 'Market research' first to use this option"
            )
        else:
            research_only = st.checkbox(
                "🔍 Research only",
                value=False,
                help="Stop after market research - review results before building"
            )

    with col3:
        has_existing_code = st.checkbox(
            "📦 Upgrade code",
            help="Upload code to improve (paste or zip upload)"
        )

    # Second row - platforms
    platforms = st.multiselect(
        "🎯 Target Platforms",
        ["Website", "Web App", "iOS", "Android"],
        default=["Web App"],
        help="Select one or more platforms to build for"
    )

    # Start button and progress tracker
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        start_button = st.button(
            "🚀 Start",
            use_container_width=True,
            type="primary",
            disabled=not project_input.strip(),  # Disable if empty
            help="Describe your project above to get started" if not project_input.strip() else None
        )

    # Validation message
    if start_button and not project_input.strip():
        st.error("⚠️ Please describe your project before starting.")
        st.stop()

    # Progress tracker
    progress_tracker = ProgressTracker()

    if start_button:
        progress_tracker.start()

        try:
            # Simulate progress phases (replace with actual implementation)
            progress_tracker.update(ProgressPhase.MARKET_RESEARCH, 25)
            progress_tracker.update(ProgressPhase.IDEATION, 50)
            progress_tracker.update(ProgressPhase.DESIGN, 75)
            progress_tracker.update(ProgressPhase.IMPLEMENTATION, 100)

            # Display results
            display_results(progress_tracker)
        except Exception as e:
            st.error(f"⚠️ An unexpected error occurred: {str(e)}")
            st.error("Please try again or contact support if the issue persists.")
            st.stop()