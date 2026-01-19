import streamlit as st
from streamlit_ui.progress_tracker import ProgressTracker, ProgressPhase
from streamlit_ui.live_terminal import LiveTerminalOutput
from streamlit_ui.results_display import display_results
from streamlit_ui.constants import COLORS, SPACING, DIMENSIONS, GRADIENTS, INTERFACE_POLISH_CSS
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

def render_main_interface() -> None:
    """
    Render the main creation interface.

    This function sets up the user interface for the Code Weaver Pro tool,
    including input fields, options, and a progress tracker.
    """
    # Inject unified polish CSS
    st.markdown(INTERFACE_POLISH_CSS, unsafe_allow_html=True)

    # Add unified professional CSS matching onboarding quality (UI Consistency Fix)
    st.markdown("""
    <style>
        /* ===== ANIMATIONS (Match onboarding) ===== */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes glow {
            0%, 100% { text-shadow: 0 0 20px rgba(102, 126, 234, 0.5); }
            50% { text-shadow: 0 0 40px rgba(102, 126, 234, 0.8), 0 0 60px rgba(118, 75, 162, 0.6); }
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }

        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        /* ===== GRADIENT TEXT HEADERS ===== */
        .main-title {
            font-size: 48px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            animation: fadeInUp 0.8s ease-out, glow 3s ease-in-out infinite;
            text-align: center;
        }

        .main-subtitle {
            font-size: 18px;
            color: #b8c1ec;
            text-align: center;
            margin-bottom: 32px;
            animation: fadeInUp 0.8s ease-out 0.1s both;
        }

        .section-header {
            font-size: 24px;
            font-weight: 700;
            color: #e8eaf6;
            margin: 24px 0 16px 0;
            animation: slideInLeft 0.5s ease-out;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .section-header::before {
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }

        /* ===== STYLED CARDS (Match onboarding capability cards) ===== */
        .input-card {
            background: linear-gradient(135deg, rgba(30, 33, 57, 0.8) 0%, rgba(37, 40, 68, 0.8) 100%);
            border: 2px solid rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 24px;
            margin: 16px 0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: fadeInUp 0.6s ease-out;
        }

        .input-card:hover {
            border-color: rgba(102, 126, 234, 0.6);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
        }

        .option-card {
            background: linear-gradient(135deg, rgba(30, 33, 57, 0.6) 0%, rgba(37, 40, 68, 0.6) 100%);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            transition: all 0.3s ease;
            animation: fadeInUp 0.5s ease-out;
        }

        .option-card:nth-child(1) { animation-delay: 0.1s; }
        .option-card:nth-child(2) { animation-delay: 0.15s; }
        .option-card:nth-child(3) { animation-delay: 0.2s; }
        .option-card:nth-child(4) { animation-delay: 0.25s; }

        .option-card:hover {
            border-color: rgba(102, 126, 234, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
        }

        /* ===== TEXTAREA STYLING ===== */
        .stTextArea textarea {
            background: rgba(30, 33, 57, 0.6) !important;
            border: 2px solid rgba(102, 126, 234, 0.3) !important;
            border-radius: 12px !important;
            color: #e8eaf6 !important;
            font-size: 16px !important;
            padding: 16px !important;
            transition: all 0.3s ease !important;
        }

        .stTextArea textarea:focus {
            border-color: rgba(102, 126, 234, 0.8) !important;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2) !important;
        }

        .stTextArea textarea::placeholder {
            color: #6b7280 !important;
        }

        /* ===== PRIMARY BUTTON (Match onboarding CTA) ===== */
        .stButton > button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-primary"] {
            min-height: 56px !important;
            background: linear-gradient(135deg, #667eea 0%, #8b5cf6 50%, #764ba2 100%) !important;
            color: white !important;
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            padding: 16px 32px !important;
            border-radius: 12px !important;
            border: none !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4) !important;
            animation: fadeInUp 0.6s ease-out 0.3s both, pulse 2s ease-in-out infinite 1s;
        }

        .stButton > button[data-testid="stBaseButton-primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover {
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 16px 48px rgba(102, 126, 234, 0.6) !important;
        }

        /* ===== CHECKBOX STYLING ===== */
        .stCheckbox {
            background: rgba(30, 33, 57, 0.4);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 8px;
            padding: 12px 16px;
            margin: 4px 0;
            transition: all 0.2s ease;
        }

        .stCheckbox:hover {
            border-color: rgba(102, 126, 234, 0.4);
            background: rgba(30, 33, 57, 0.6);
        }

        /* ===== MULTISELECT STYLING ===== */
        .stMultiSelect > div {
            background: rgba(30, 33, 57, 0.6) !important;
            border: 2px solid rgba(102, 126, 234, 0.3) !important;
            border-radius: 12px !important;
        }

        .stMultiSelect > div:focus-within {
            border-color: rgba(102, 126, 234, 0.8) !important;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2) !important;
        }

        /* ===== RESPONSIVE LAYOUT ===== */
        .main .block-container {
            max-width: 100%;
            padding: 1rem;
        }

        /* Mobile (< 768px) */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 0.75rem;
            }

            .main-title {
                font-size: 32px !important;
            }

            .main-subtitle {
                font-size: 16px !important;
            }

            .section-header {
                font-size: 20px;
            }

            [data-testid="column"] {
                width: 100% !important;
                margin-bottom: 1rem;
            }

            .stButton > button {
                min-height: 48px !important;
                padding: 14px 20px !important;
                font-size: 16px !important;
            }

            .input-card, .option-card {
                padding: 16px;
            }
        }

        /* Tablet (768px - 1024px) */
        @media (min-width: 768px) and (max-width: 1024px) {
            .main .block-container {
                padding: 1.5rem;
            }

            .main-title {
                font-size: 40px !important;
            }

            [data-testid="column"] {
                width: 50% !important;
            }
        }

        /* Desktop (> 1024px) */
        @media (min-width: 1024px) {
            .main .block-container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 2rem 3rem;
            }

            .main-title {
                font-size: 48px !important;
            }

            [data-testid="column"] {
                padding: 0 1rem;
            }
        }

        /* ===== FOCUS STATES (Accessibility) ===== */
        *:focus-visible {
            outline: 3px solid #8b9eff !important;
            outline-offset: 3px !important;
            box-shadow: 0 0 0 6px rgba(139, 158, 255, 0.35) !important;
        }

        /* ===== REDUCED MOTION ===== */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Introductory section with professional gradient styling (matching onboarding)
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <div class="main-title">🪡 Code Weaver Pro</div>
        <div class="main-subtitle">Transform your ideas into production-ready code with AI magic</div>
    </div>
    """, unsafe_allow_html=True)

    # Instructions in styled container
    st.markdown("""
    <div class="input-card" style="margin-bottom: 24px;">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="font-size: 32px;">✨</div>
            <div>
                <div style="font-size: 18px; font-weight: 600; color: #e8eaf6; margin-bottom: 8px;">Getting Started</div>
                <ol style="color: #9ca3af; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li>Describe your project idea below</li>
                    <li>Select options to customize your project</li>
                    <li>Click Start and watch the magic happen</li>
                </ol>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main input with styled header
    st.markdown('<div class="section-header">What do you want to build?</div>', unsafe_allow_html=True)
    with st.container():
        project_input = st.text_area(
            "Describe your project",
            placeholder="Example: A recipe app where users can save favorites, search by ingredients, and share with friends.",
            height=120,
            key="project_input",
            label_visibility="visible",
            help="Be specific about features, target users, and key functionality"
        )

    # Validate project input
    if not project_input.strip():
        st.error("⚠️ Please provide a description of your project.")
        st.stop()

    # Options - 2 rows for better mobile layout
    st.markdown('<div class="section-header">Options</div>', unsafe_allow_html=True)

    # Responsive columns - adapt to screen size
    # On mobile (< 768px): stack vertically
    # On tablet (768-1024px): 2 columns
    # On desktop (> 1024px): 3 columns
    col1, col2, col3 = st.columns(2, gap="small")

    with col1:
        do_market_research = st.checkbox(
            "📊 Market research",
            help="Analyze competitors, TAM/SAM/SOM, and get go/no-go decision",
            css={
                'color': COLORS["text_primary"],
                'background-color': COLORS["component_bg"],
                'white-space': 'normal',  # Allow wrapping on mobile
                'height': DIMENSIONS["button_height"],
                'font-size': '1rem',
                'padding': f'{SPACING["sm"]} {SPACING["md"]}',
                'width': '100%'
            }
        )

    with col2:
        # Show explanation when disabled
        if not do_market_research:
            research_only = st.checkbox(
                "🔍 Research only",
                value=False,
                disabled=True,
                help="⚠️ Enable 'Market research' first to use this option",
                css={
                    'color': COLORS["text_secondary"],
                    'background-color': '#444444',
                    'white-space': 'normal',  # Allow wrapping on mobile
                    'height': DIMENSIONS["button_height"],
                    'font-size': '1rem',
                    'padding': f'{SPACING["sm"]} {SPACING["md"]}',
                    'width': '100%'
                }
            )
        else:
            research_only = st.checkbox(
                "🔍 Research only",
                value=False,
                help="Stop after market research - review results before building",
                css={
                    'color': COLORS["text_primary"],
                    'background-color': COLORS["component_bg"],
                    'white-space': 'normal',  # Allow wrapping on mobile
                    'height': DIMENSIONS["button_height"],
                    'font-size': '1rem',
                    'padding': f'{SPACING["sm"]} {SPACING["md"]}',
                    'width': '100%'
                }
            )

    col1, col2 = st.columns(2, gap="small")
    with col1:
        has_existing_code = st.checkbox(
            "📦 Upgrade code",
            help="Upload code to improve (paste or zip upload)",
            css={
                'color': COLORS["text_primary"],
                'background-color': COLORS["component_bg"],
                'white-space': 'normal',  # Allow wrapping on mobile
                'height': DIMENSIONS["button_height"],
                'font-size': '1rem',
                'padding': f'{SPACING["sm"]} {SPACING["md"]}',
                'width': '100%'
            }
        )

    # Platform selection
    with st.container():
        platforms = st.multiselect(
            "🎯 Target Platforms",
            ["Website", "Web App", "iOS", "Android"],
            default=["Web App"],
            help="Select one or more platforms to build for",
            css={
                'color': COLORS["text_primary"],
                'background-color': COLORS["component_bg"],
                'margin-top': SPACING["sm"],
                'font-size': '1rem',
                'padding': f'{SPACING["sm"]} {SPACING["md"]}',
                'width': '100%',
                'max-width': '800px'
            }
        )

    # Start button and progress tracker
    col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
    with col2:
        start_button = st.button(
            "🚀 Start",
            use_container_width=True,
            type="primary",
            disabled=not project_input.strip(),
            help="Describe your project above to get started" if not project_input.strip() else None,
            css={
                'color': COLORS["text_primary"],
                'background-color': '#007bff',
                'border-color': '#007bff',
                'font-weight': 'bold',
                'padding': f'{SPACING["sm"]} {SPACING["md"]}',
                'border-radius': DIMENSIONS["border_radius"],
                'white-space': 'normal',  # Allow wrapping on mobile
                'height': DIMENSIONS["button_height"],
                'font-size': '1rem',
                'width': '100%'
            }
        )

    # Validate project input
    if start_button and not project_input.strip():
        st.error("⚠️ Please provide a description of your project.")
        st.stop()

    # Progress tracker
    progress_tracker = ProgressTracker()

    if start_button:
        try:
            progress_tracker.start()

            # Simulate progress phases (replace with actual implementation)
            progress_tracker.update(ProgressPhase.MARKET_RESEARCH, 25)
            progress_tracker.update(ProgressPhase.IDEATION, 50)
            progress_tracker.update(ProgressPhase.DESIGN, 75)
            progress_tracker.update(ProgressPhase.IMPLEMENTATION, 100)

            # Display results
            display_results(progress_tracker)
        except Exception as e:
            if not ORCHESTRATOR_AVAILABLE:
                st.error(f"⚠️ The Orchestrator is not available: {IMPORT_ERROR}")
                st.error("Please check your configuration and try again later.")
            else:
                st.error(f"⚠️ An unexpected error occurred: {str(e)}")
                st.error("Please check your input and try again. If the issue persists, contact support for assistance.")
            st.stop()