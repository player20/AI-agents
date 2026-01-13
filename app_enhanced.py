"""
Code Weaver Pro - Enhanced Streamlit Entry Point
Magical, user-friendly interface for AI-powered application generation
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point for Code Weaver Pro"""

    # Page config - centered, no sidebar
    st.set_page_config(
        page_title="Code Weaver Pro 🪡",
        page_icon="🪡",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS - Dark theme with soft glows and magical feel
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Dark theme base */
        .stApp {
            background: linear-gradient(135deg, #0a0e27 0%, #1a1d35 100%);
            font-family: 'Inter', sans-serif;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Global text - highly visible */
        body, p, div, span, label, .stMarkdown {
            color: #e8eaf6 !important;
            font-family: 'Inter', sans-serif;
        }

        /* Title styling */
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
            font-size: 48px;
            text-align: center;
            margin-bottom: 8px;
        }

        /* Subtitle */
        .subtitle {
            text-align: center;
            color: #b8c1ec !important;
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 40px;
        }

        /* Main input area - LARGE and inviting */
        .stTextArea textarea {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px solid #3d4466;
            border-radius: 16px;
            color: #ffffff !important;
            font-size: 18px;
            font-weight: 500;
            padding: 20px;
            min-height: 140px;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
            transition: all 0.3s ease;
        }

        .stTextArea textarea:focus {
            border-color: #667eea;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
            outline: none;
        }

        .stTextArea textarea::placeholder {
            color: #7e88b5 !important;
            font-weight: 400;
        }

        /* Checkboxes - Bigger and more visible */
        .stCheckbox {
            padding: 12px;
            background: rgba(102, 126, 234, 0.05);
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .stCheckbox:hover {
            background: rgba(102, 126, 234, 0.1);
        }

        .stCheckbox > label {
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #e8eaf6 !important;
            cursor: pointer;
        }

        .stCheckbox > label > div {
            color: #e8eaf6 !important;
        }

        /* MultiSelect styling */
        .stMultiSelect > label {
            font-size: 15px !important;
            font-weight: 600 !important;
            color: #e8eaf6 !important;
        }

        .stMultiSelect > div > div {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px solid #3d4466;
            border-radius: 12px;
        }

        /* GO Button - BIG, prominent, glowing */
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            font-size: 24px;
            font-weight: 800;
            padding: 20px 48px;
            border-radius: 16px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .stButton > button:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 48px rgba(102, 126, 234, 0.6);
        }

        .stButton > button:active {
            transform: translateY(-2px);
        }

        /* Progress bars - Smooth gradient */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }

        /* Terminal output */
        .terminal-output {
            background: #0d1117;
            border: 2px solid #21262d;
            border-radius: 12px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #58a6ff;
            max-height: 400px;
            overflow-y: auto;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            margin: 20px 0;
        }

        .terminal-line {
            margin: 4px 0;
            line-height: 1.6;
        }

        .terminal-success {
            color: #3fb950;
        }

        .terminal-error {
            color: #f85149;
        }

        .terminal-warning {
            color: #f0883e;
        }

        .terminal-info {
            color: #58a6ff;
        }

        /* Cards for results */
        .result-card {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px solid #3d4466;
            border-radius: 16px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        .result-card h3 {
            color: #667eea !important;
            margin-bottom: 16px;
        }

        /* Score badges */
        .score-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
            margin: 4px;
        }

        .score-excellent {
            background: linear-gradient(135deg, #3fb950 0%, #2ea043 100%);
            color: white;
        }

        .score-good {
            background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
            color: white;
        }

        .score-fair {
            background: linear-gradient(135deg, #f0883e 0%, #db6d28 100%);
            color: white;
        }

        .score-poor {
            background: linear-gradient(135deg, #f85149 0%, #da3633 100%);
            color: white;
        }

        /* Emoji styling */
        .emoji-large {
            font-size: 48px;
            text-align: center;
            margin: 20px 0;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(102, 126, 234, 0.05);
            border-radius: 12px;
            color: #e8eaf6 !important;
            font-weight: 600;
        }

        /* File uploader */
        .stFileUploader {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px dashed #3d4466;
            border-radius: 12px;
            padding: 20px;
        }

        /* Download button */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #3fb950 0%, #2ea043 100%);
            color: white !important;
            border-radius: 12px;
            font-weight: 600;
            padding: 12px 24px;
        }

        /* Smooth transitions */
        * {
            transition: all 0.3s ease;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1d35;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 6px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'mode' not in st.session_state:
        st.session_state.mode = 'create'
    if 'clarification_needed' not in st.session_state:
        st.session_state.clarification_needed = False
    if 'terminal_lines' not in st.session_state:
        st.session_state.terminal_lines = []

    # Header with magical feel
    st.markdown("""
        <div style='text-align: center; margin-bottom: 40px;'>
            <h1>🪡 Code Weaver Pro</h1>
            <p class='subtitle'>Tell me your big idea. I'll handle everything else.</p>
        </div>
    """, unsafe_allow_html=True)

    # Mode selector (subtle, elegant)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode_cols = st.columns(2)
        with mode_cols[0]:
            if st.button("✨ Create App", key="mode_create", use_container_width=True,
                        type="primary" if st.session_state.mode == 'create' else "secondary"):
                st.session_state.mode = 'create'
                st.rerun()
        with mode_cols[1]:
            if st.button("🔄 Self-Improve", key="mode_improve", use_container_width=True,
                        type="primary" if st.session_state.mode == 'self_improve' else "secondary"):
                st.session_state.mode = 'self_improve'
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Render appropriate interface
    if st.session_state.mode == 'create':
        render_create_interface()
    else:
        render_self_improve_interface()

    # Footer with soft emoji
    st.markdown("""
        <div style='text-align: center; margin-top: 60px; padding: 40px; opacity: 0.7;'>
            <p style='font-size: 16px; color: #b8c1ec;'>
                Dream caught. Ready when you are. 😊
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_create_interface():
    """Render the main creation interface with magical UX"""

    # Import here to avoid circular imports
    from streamlit_ui.main_interface_enhanced import render_enhanced_interface

    render_enhanced_interface()


def render_self_improve_interface():
    """Render the self-improvement interface"""

    st.markdown("""
        <div class='result-card'>
            <h3>🔄 Meta Self-Improvement Mode</h3>
            <p>This mode allows Code Weaver Pro to analyze and improve its own codebase.</p>
        </div>
    """, unsafe_allow_html=True)

    st.info("🚧 Self-improvement mode coming soon! This will allow the platform to autonomously evaluate and enhance its own UI/UX.")

    # Placeholder for self-improvement
    if st.button("🔍 Analyze Platform Code"):
        st.warning("Feature in development. Check back soon!")


if __name__ == "__main__":
    main()
