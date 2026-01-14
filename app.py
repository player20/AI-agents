"""
Code Weaver Pro - Complete Streamlit Entry Point

User-friendly, magical interface for AI-powered application generation.
Built on top of the existing MultiAgentTeam platform with full feature integration.

Features:
- Dynamic agent adaptation (meta_prompt)
- Drop-off analysis (Audit Mode)
- A/B test generation
- Professional report export
- Meta self-improvement loop
"""

import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point for Code Weaver Pro"""

    # Verify API key is set
    if not os.getenv('ANTHROPIC_API_KEY'):
        st.error("⚠️ **ANTHROPIC_API_KEY not set**")
        st.markdown("""
            Please set your API key:

            **Option 1:** Create a `.env` file in the project root:
            ```
            ANTHROPIC_API_KEY=sk-ant-your-key-here
            ```

            **Option 2:** Set environment variable:
            ```bash
            export ANTHROPIC_API_KEY="sk-ant-your-key-here"
            ```

            Then restart the app.
        """)
        st.stop()

    # Page config - centered layout for clean, magical feel
    st.set_page_config(
        page_title="Code Weaver Pro 🪡",
        page_icon="🪡",
        layout="centered",  # Changed from wide to centered for better UX
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

        /* Cards for results */
        .result-card {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px solid #3d4466;
            border-radius: 16px;
            padding: 24px;
            margin: 16px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }

        /* File uploader */
        .stFileUploader {
            background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
            border: 2px dashed #3d4466;
            border-radius: 12px;
            padding: 20px;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(102, 126, 234, 0.05);
            border-radius: 12px;
            color: #e8eaf6 !important;
            font-weight: 600;
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

        /* Smooth transitions */
        * {
            transition: all 0.3s ease;
        }

        /* Responsive navigation tabs */
        @media (max-width: 768px) {
            /* On mobile, make buttons full width and stack */
            .stButton > button {
                width: 100% !important;
                margin: 0.5rem 0 !important;
                font-size: 18px !important;
                padding: 16px 24px !important;
            }

            /* Remove side padding on mobile */
            [data-testid="column"] {
                padding: 0 0.25rem !important;
            }

            /* Title smaller on mobile */
            h1 {
                font-size: 32px !important;
            }

            .subtitle {
                font-size: 14px !important;
            }
        }

        @media (min-width: 768px) {
            /* On desktop, center navigation with max width */
            .navigation-container {
                max-width: 800px;
                margin: 0 auto;
            }
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
            <p class='subtitle'>Tell me your big idea, no tech talk needed.</p>
        </div>
    """, unsafe_allow_html=True)

    # Mode selector (responsive toggle with container for centering)
    st.markdown('<div class="navigation-container">', unsafe_allow_html=True)

    # Use 2 equal columns instead of [1,2,1] centering for better mobile responsiveness
    mode_cols = st.columns(2)

    with mode_cols[0]:
        if st.button(
            "✨ Create App",
            key="mode_create",
            use_container_width=True,
            type="primary" if st.session_state.mode == 'create' else "secondary"
        ):
            st.session_state.mode = 'create'
            st.rerun()

    with mode_cols[1]:
        if st.button(
            "🔄 Self-Improve",
            key="mode_improve",
            use_container_width=True,
            type="primary" if st.session_state.mode == 'self_improve' else "secondary"
        ):
            st.session_state.mode = 'self_improve'
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Render appropriate interface based on mode
    if st.session_state.mode == 'create':
        # Use enhanced interface with all features
        from streamlit_ui.main_interface_enhanced import render_enhanced_interface
        render_enhanced_interface()
    else:
        # Self-improvement mode
        from streamlit_ui.self_improvement import render_self_improvement
        render_self_improvement()

    # Footer with soft emoji
    st.markdown("""
        <div style='text-align: center; margin-top: 60px; padding: 40px; opacity: 0.7;'>
            <p style='font-size: 16px; color: #b8c1ec;'>
                Dream caught. Ready when you are. 😊
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
