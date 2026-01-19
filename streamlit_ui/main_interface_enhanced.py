"""
Enhanced Main Interface for Code Weaver Pro
Integrates all new features: meta_prompt, audit_mode, ab_test, reports

This is the main entry point that imports from modularized components:
- enhanced_interface_input: User input forms with accessibility
- enhanced_interface_execution: Orchestrator execution with error handling
- enhanced_interface_results: Results display with accessibility

Each module is under 400 lines to enable auto-fix capabilities.
"""

import streamlit as st
import sys
from pathlib import Path

# Import constants
try:
    from streamlit_ui.constants import COLORS, SPACING, DIMENSIONS
    CONSTANTS_AVAILABLE = True
except ImportError:
    CONSTANTS_AVAILABLE = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import core modules for validation
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

# Import modularized components with comprehensive error handling
try:
    from streamlit_ui.enhanced_interface_input import render_enhanced_interface, render_clarification_flow
    INPUT_MODULE_AVAILABLE = True
except ImportError as e:
    INPUT_MODULE_AVAILABLE = False
    INPUT_MODULE_ERROR = str(e)

try:
    from streamlit_ui.enhanced_interface_execution import run_enhanced_execution
    EXECUTION_MODULE_AVAILABLE = True
except ImportError as e:
    EXECUTION_MODULE_AVAILABLE = False
    EXECUTION_MODULE_ERROR = str(e)

try:
    from streamlit_ui.enhanced_interface_results import display_enhanced_results_from_orchestrator, display_enhanced_results
    RESULTS_MODULE_AVAILABLE = True
except ImportError as e:
    RESULTS_MODULE_AVAILABLE = False
    RESULTS_MODULE_ERROR = str(e)


def check_module_availability():
    """
    Check if all required modules are available and display errors if not.
    This provides clear debugging information if the split modules fail to load.

    Returns:
        bool: True if all modules available, False otherwise
    """
    all_available = True

    if not INPUT_MODULE_AVAILABLE:
        st.error(f"### ❌ Input Module Error\n\nFailed to load `enhanced_interface_input.py`: {INPUT_MODULE_ERROR}")
        all_available = False

    if not EXECUTION_MODULE_AVAILABLE:
        st.error(f"### ❌ Execution Module Error\n\nFailed to load `enhanced_interface_execution.py`: {EXECUTION_MODULE_ERROR}")
        all_available = False

    if not RESULTS_MODULE_AVAILABLE:
        st.error(f"### ❌ Results Module Error\n\nFailed to load `enhanced_interface_results.py`: {RESULTS_MODULE_ERROR}")
        all_available = False

    if not META_AVAILABLE:
        st.warning(f"### ⚠️ Core Modules Warning\n\nSome core modules failed to load: {IMPORT_ERROR}\n\nBasic functionality may be limited.")

    return all_available


def render_main_interface():
    """
    Render the main interface with responsive design.
    """

    if not check_module_availability():
        return

    st.set_page_config(
        page_title="Code Weaver Pro",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="auto"
    )

    if CONSTANTS_AVAILABLE:
        st.markdown(f"""
        <style>
            .main {{
                max-width: {DIMENSIONS['max_width']}px;
                margin: {SPACING['xxl']} auto;
            }}

            @media (max-width: {DIMENSIONS['breakpoint_lg']}px) {{
                .main {{
                    max-width: {DIMENSIONS['max_width_sm']}px;
                    margin: {SPACING['xl']} auto;
                }}
            }}

            @media (max-width: {DIMENSIONS['breakpoint_sm']}px) {{
                .main {{
                    max-width: 90%;
                    margin: {SPACING['lg']} auto;
                }}
            }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <style>
            .main {{
                max-width: 1200px;
                margin: 40px auto;
            }}

            @media (max-width: 992px) {{
                .main {{
                    max-width: 800px;
                    margin: 32px auto;
                }}
            }}

            @media (max-width: 576px) {{
                .main {{
                    max-width: 90%;
                    margin: 24px auto;
                }}
            }}
        </style>
        """, unsafe_allow_html=True)

    with st.container():
        st.markdown(
            f"""
            <div class="main">
                <h1 style="text-align: center; margin-bottom: {SPACING['lg']};">🧠 Code Weaver Pro</h1>
                <p style="text-align: center; color: {COLORS['text_secondary']}; margin-bottom: {SPACING['xl']};">
                    Generate your next app with AI-powered development and analysis.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        render_enhanced_interface()

        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: {COLORS['text_secondary']}; margin-top: {SPACING['xl']};">
            ⚠️ This is a demo version. Refer to the documentation for the latest features and capabilities.
        </div>
        """.format(COLORS=COLORS, SPACING=SPACING), unsafe_allow_html=True)


if __name__ == "__main__":
    render_main_interface()