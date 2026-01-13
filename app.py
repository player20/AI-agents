"""
Code Weaver Pro - Streamlit Entry Point

User-friendly interface for AI-powered application generation.
Built on top of the existing MultiAgentTeam platform.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point for Code Weaver Pro"""

    # Page config
    st.set_page_config(
        page_title="Code Weaver Pro",
        page_icon="🪡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for dark theme with soft glows and professional styling
    st.markdown("""
        <style>
        /* Dark theme base */
        .stApp {
            background-color: #0e1117;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Global text styling - Make everything more visible */
        body, p, div, span, label {
            color: #ffffff !important;
        }

        /* Custom button styling */
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            font-size: 18px;
            font-weight: 700;
            padding: 16px 32px;
            border-radius: 12px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
        }

        /* Progress bar styling */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }

        /* Input field styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background-color: #1e2130;
            color: white !important;
            border: 2px solid #2d3250;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            font-weight: 500;
        }

        /* Placeholder text */
        .stTextArea textarea::placeholder {
            color: #a0a0a0 !important;
        }

        /* Checkbox styling - Make more visible */
        .stCheckbox > label {
            font-size: 16px;
            font-weight: 600;
            color: #ffffff !important;
        }

        /* Checkbox text */
        .stCheckbox > label > div {
            color: #ffffff !important;
        }

        /* MultiSelect styling */
        .stMultiSelect > label {
            font-size: 16px;
            font-weight: 600;
            color: #ffffff !important;
        }

        /* Terminal output styling */
        .terminal-output {
            background-color: #1a1d29;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            padding: 16px;
            border-radius: 8px;
            height: 400px;
            overflow-y: auto;
            margin: 16px 0;
        }

        /* Toggle switch styling */
        .toggle-container {
            display: inline-flex;
            background: #1e2130;
            border-radius: 12px;
            padding: 4px;
            border: 2px solid #2d3250;
            margin-bottom: 24px;
        }

        .toggle-option {
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            font-size: 15px;
        }

        .toggle-option.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
        }

        .toggle-option.inactive {
            background: transparent;
            color: #8B9FFF;
        }

        /* Smooth transitions */
        * {
            transition: all 0.3s ease;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'mode' not in st.session_state:
        st.session_state.mode = 'create'  # 'create' or 'self_improve'

    # Header
    st.markdown("""
        <div style='text-align: center; margin-bottom: 32px;'>
            <h1 style='color: #8B9FFF; margin-bottom: 8px; font-weight: 800; font-size: 48px;'>
                🪡 Code Weaver Pro
            </h1>
            <p style='color: #ffffff; font-size: 20px; font-weight: 500;'>
                Describe your app in 1-2 sentences. We'll handle the rest.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Mode selector - Toggle switch style
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        mode_cols = st.columns(2)
        with mode_cols[0]:
            if st.button("🪄 Create App", key="mode_create", use_container_width=True,
                        type="primary" if st.session_state.mode == 'create' else "secondary"):
                st.session_state['mode'] = 'create'
                st.rerun()
        with mode_cols[1]:
            if st.button("🔄 Self-Improve", key="mode_improve", use_container_width=True,
                        type="primary" if st.session_state.mode == 'self_improve' else "secondary"):
                st.session_state.mode = 'self_improve'
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Render appropriate interface based on mode
    if st.session_state.mode == 'create':
        from streamlit_ui.main_interface import render_main_interface
        render_main_interface()
    else:
        # Self-improvement mode
        from streamlit_ui.self_improvement import render_self_improvement
        render_self_improvement()

    st.markdown("""
        <div style='text-align: center; margin-top: 32px; padding: 32px;'>
            <p style='color: #a0a0a0; font-size: 14px;'>
                Dream caught. Ready when you are. 😊
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
