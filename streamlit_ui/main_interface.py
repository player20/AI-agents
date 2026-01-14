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
            default=["Web App"]
        )

    # Start button and progress tracker
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        start_button = st.button(
            "🚀 Start",
            use_container_width=True,
            type="primary"
        )

    # Progress tracker
    progress_tracker = ProgressTracker()

    if start_button:
        progress_tracker.start()

        # Simulate progress phases (replace with actual implementation)
        progress_tracker.update(ProgressPhase.MARKET_RESEARCH, 25)
        progress_tracker.update(ProgressPhase.IDEATION, 50)
        progress_tracker.update(ProgressPhase.DESIGN, 75)
        progress_tracker.update(ProgressPhase.IMPLEMENTATION, 100)

        # Display results
        display_results(progress_tracker)