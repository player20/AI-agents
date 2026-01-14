"""
Self-Improvement UI for Code Weaver Pro
Allows the system to analyze and improve its own code
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
from typing import TYPE_CHECKING

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

if TYPE_CHECKING:
    from core.self_improver import SelfImprover, ImprovementMode

try:
    from core.self_improver import SelfImprover, ImprovementMode
    from core.config import load_config
    IMPROVER_AVAILABLE = True
except ImportError as e:
    IMPROVER_AVAILABLE = False
    IMPORT_ERROR = str(e)
    SelfImprover = None  # Define as None for type hints if import fails


def render_self_improvement():
    """Render the self-improvement interface"""

    st.set_page_config(layout="wide")  # Set the layout to wide for better responsiveness
    st.markdown("### 🔄 Meta Self-Improvement")
    st.markdown("The system evaluates and improves its own code, UI/UX, and capabilities.")

    if not IMPROVER_AVAILABLE:
        st.error(f"⚠️ Self-improvement engine not available: {IMPORT_ERROR}")
        return

    # Improvement mode selector
    st.markdown("#### Select Improvement Mode")

    mode_options = {
        "🎨 UI/UX": (ImprovementMode.UI_UX, "Make the interface more intuitive and user-friendly"),
        "⚡ Performance": (ImprovementMode.PERFORMANCE, "Speed up execution and optimize resource usage"),
        "🧠 Agent Quality": (ImprovementMode.AGENT_QUALITY, "Improve AI agent outputs and prompts"),
        "🔧 Code Quality": (ImprovementMode.CODE_QUALITY, "Refactor and optimize code structure"),
        "✨ Everything": (ImprovementMode.EVERYTHING, "Comprehensive improvement across all areas")
    }

    selected_mode_label = st.radio(
        "Focus Area",
        list(mode_options.keys()),
        index=4,  # Default to "Everything"
        help="Choose what aspect of the system to improve"
    )

    selected_mode, mode_description = mode_options[selected_mode_label]
    st.info(f"**{selected_mode_label}:** {mode_description}")

    # Forever mode checkbox
    col1, col2 = st.columns([3, 1])
    with col1:
        forever_mode = st.checkbox(
            "🔁 Improve me forever (run until stopped)",
            value=False,
            help="Continuously run improvement cycles until you click Stop"
        )

    # Target specific files (optional)
    st.markdown("#### Target Specific Files (Optional)")
    target_files_text = st.text_area(
        "File paths (one per line)",
        placeholder="core/orchestrator.py\nstreamlit_ui/main_interface.py\n(Leave empty to analyze all files)",
        height=100,
        help="Specify files to analyze, or leave empty to analyze entire codebase"
    )

    # Parse target files
    target_files = [
        line.strip() for line in target_files_text.split('\n')
        if line.strip()
    ] if target_files_text.strip() else None

    # Start button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        start_button = st.button(
            "🚀 Start Improvement",
            help="Begin the self-improvement process"
        )