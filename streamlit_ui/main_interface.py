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
            default=["Web App"]
        )