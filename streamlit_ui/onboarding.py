"""
Impressive First-Run Onboarding Experience

Creates an engaging, magical welcome experience for new users.
Features animated transitions, capability showcases, and smooth entry into the app.
"""

import streamlit as st
from typing import Dict, List, Optional
import time


def check_first_run() -> bool:
    """Check if this is the user's first run."""
    if 'onboarding_complete' not in st.session_state:
        st.session_state.onboarding_complete = False
    return not st.session_state.onboarding_complete


def complete_onboarding():
    """Mark onboarding as complete."""
    st.session_state.onboarding_complete = True
    st.session_state.onboarding_step = 0


def render_onboarding() -> bool:
    """
    Render the onboarding experience.

    Returns:
        True if onboarding should continue, False if complete
    """
    if 'onboarding_step' not in st.session_state:
        st.session_state.onboarding_step = 0

    step = st.session_state.onboarding_step

    # Inject onboarding CSS
    _inject_onboarding_css()

    if step == 0:
        _render_welcome_screen()
    elif step == 1:
        _render_capabilities_screen()
    elif step == 2:
        _render_agents_screen()
    elif step == 3:
        _render_ready_screen()
    else:
        complete_onboarding()
        return False

    return True


def _inject_onboarding_css():
    """Inject CSS for onboarding animations and styling."""
    st.markdown("""
    <style>
    /* Onboarding container */
    .onboarding-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40px;
        text-align: center;
    }

    /* Animated logo */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }

    @keyframes glow {
        0%, 100% { text-shadow: 0 0 20px rgba(102, 126, 234, 0.5); }
        50% { text-shadow: 0 0 40px rgba(102, 126, 234, 0.8), 0 0 60px rgba(118, 75, 162, 0.6); }
    }

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

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
}
    
    /* High contrast capability icons - WCAG AA compliant (4.5:1+ ratio) */
    .cap-icon,
    .capability-icon,
    .feature-icon,
    .gen-complete-icon,
    .ready-icon,
    .progress-dot.active {
        color: #94a3fd !important; /* Darker indigo - high contrast on dark backgrounds */
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6) !important;
        filter: brightness(1.1) contrast(1.3) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5)) !important;
        font-size: clamp(48px, 12vw, 72px) !important;
        line-height: 1 !important;
    }
    
    /* Ensure icon containers have proper contrast bg if needed */
    [class*="cap"] > .cap-icon,
    [class*="capability"] > *,
    .cap-item {
        background: rgba(30, 33, 57, 0.8) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Darken glow effects for better base contrast */
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 20px rgba(148, 163, 253, 0.8); }
        50% { text-shadow: 0 0 40px rgba(148, 163, 253, 1), 0 0 60px rgba(148, 163, 253, 0.7); }
    }
        }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    .welcome-logo {
        font-size: 120px;
        animation: float 3s ease-in-out infinite, glow 2s ease-in-out infinite;
        margin-bottom: 24px;
    }

    .welcome-title {
        font-size: 56px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 16px;
        animation: fadeInUp 1s ease-out;
    }

    .welcome-subtitle {
        font-size: 24px;
        color: #b8c1ec;
        margin-bottom: 48px;
        animation: fadeInUp 1s ease-out 0.2s both;
    }

    /* Capability cards */
    .capability-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 24px;
        max-width: 1000px;
        margin: 32px auto;
    }

    .capability-card {
        background: linear-gradient(135deg, rgba(30, 33, 57, 0.8) 0%, rgba(37, 40, 68, 0.8) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 32px;
        text-align: left;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: fadeInUp 0.6s ease-out both;
    }

    .capability-card:nth-child(1) { animation-delay: 0.1s; }
    .capability-card:nth-child(2) { animation-delay: 0.2s; }
    .capability-card:nth-child(3) { animation-delay: 0.3s; }
    .capability-card:nth-child(4) { animation-delay: 0.4s; }

    .capability-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: rgba(102, 126, 234, 0.8);
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }

    .capability-icon {
        font-size: 48px;
        margin-bottom: 16px;
    }

    .capability-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .capability-desc {
        font-size: 14px;
        color: #9ca3af;
        line-height: 1.6;
    }

    /* Agent showcase */
    .agent-flow {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-wrap: wrap;
        gap: 16px;
        margin: 32px 0;
    }

    .agent-node {
        background: linear-gradient(135deg, #1e2139 0%, #252844 100%);
        border: 2px solid #3d4466;
        border-radius: 16px;
        padding: 16px 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        animation: slideInLeft 0.5s ease-out both;
    }

    .agent-node:nth-of-type(1) { animation-delay: 0.1s; }
    .agent-node:nth-of-type(2) { animation-delay: 0.2s; }
    .agent-node:nth-of-type(3) { animation-delay: 0.3s; }
    .agent-node:nth-of-type(4) { animation-delay: 0.4s; }
    .agent-node:nth-of-type(5) { animation-delay: 0.5s; }
    .agent-node:nth-of-type(6) { animation-delay: 0.6s; }
    .agent-node:nth-of-type(7) { animation-delay: 0.7s; }
    .agent-node:nth-of-type(8) { animation-delay: 0.8s; }

    .agent-emoji {
        font-size: 32px;
    }

    .agent-name {
        font-size: 14px;
        font-weight: 600;
        color: #e8eaf6;
    }

    .agent-arrow {
        font-size: 24px;
        color: #667eea;
        animation: pulse 1s ease-in-out infinite;
    }

    /* CTA button */
    .onboarding-cta {
        margin-top: 48px;
        animation: fadeInUp 1s ease-out 0.5s both;
    }

    /* Progress dots */
    .progress-dots {
        display: flex;
        gap: 12px;
        justify-content: center;
        margin-top: 40px;
    }

    .progress-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #3d4466;
        transition: all 0.3s ease;
    }

    .progress-dot.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transform: scale(1.3);
    }

    /* Section header */
    .section-header {
        font-size: 36px;
        font-weight: 700;
        color: #e8eaf6;
        margin-bottom: 16px;
        animation: fadeInUp 0.6s ease-out;
    }

    .section-subheader {
        font-size: 18px;
        color: #9ca3af;
        margin-bottom: 32px;
        animation: fadeInUp 0.6s ease-out 0.1s both;
    }

    /* Ready screen */
    .ready-container {
        text-align: center;
        padding: 60px 40px;
    }

    .ready-icon {
        font-size: 100px;
        animation: float 2s ease-in-out infinite, pulse 1s ease-in-out infinite;
        margin-bottom: 24px;
    }

    .ready-title {
        font-size: 48px;
        font-weight: 800;
        color: #10b981;
        margin-bottom: 16px;
        animation: fadeInUp 0.6s ease-out;
    }

    .ready-message {
        font-size: 20px;
        color: #b8c1ec;
        margin-bottom: 40px;
        animation: fadeInUp 0.6s ease-out 0.2s both;
    }

    /* Button styling for onboarding - Issue #1 Enhanced Primary CTA */
    .stButton > button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"] {
        min-height: 56px !important;
        min-width: 200px !important;
        background: linear-gradient(135deg, #667eea 0%, #8b5cf6 50%, #764ba2 100%) !important;
        color: white !important;
        font-size: 1.25rem;
        font-weight: 700;
        padding: 18px 36px;
        border-radius: 12px;
        border: none !important;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.5);
    }

    .stButton > button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 16px 48px rgba(102, 126, 234, 0.7);
    }

    .stButton > button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-secondary"] {
        min-height: 44px !important;
        background: linear-gradient(135deg, #1e2139 0%, #252844 100%) !important;
        color: #e8eaf6 !important;
        font-size: 16px;
        font-weight: 600;
        padding: 12px 24px;
        border-radius: 12px;
        border: 2px solid #3d4466 !important;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover {
        background: linear-gradient(135deg, #252844 0%, #2d3154 100%) !important;
        border-color: #667eea !important;
        color: #ffffff !important;
        transform: translateY(-2px);
    }

    /* Fallback for all buttons */
    .stButton > button {
        color: #e8eaf6 !important;
        min-height: 44px !important;
    }

    /* Focus states for accessibility - Issue #7, #11 (Enhanced) */
    .stButton > button:focus-visible {
        outline: 3px solid #8b9eff !important;
        outline-offset: 3px !important;
        box-shadow: 0 0 0 6px rgba(139, 158, 255, 0.4),
                    0 8px 32px rgba(102, 126, 234, 0.6) !important;
    }

    /* All interactive elements focus */
    *:focus-visible {
        outline: 3px solid #8b9eff !important;
        outline-offset: 3px !important;
        box-shadow: 0 0 0 6px rgba(139, 158, 255, 0.35) !important;
    }

    /* Mobile touch targets - Issue #2 */
    @media (max-width: 768px) {
        .stButton > button {
            min-height: 48px !important;
            width: 100% !important;
            padding: 16px 24px !important;
        }
    }

    /* Reduced motion preference */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def _render_welcome_screen():
    """Render the initial welcome screen."""
    st.markdown("""
    <div class="onboarding-container">
        <div class="welcome-logo">🪡</div>
        <div class="welcome-title">Code Weaver Pro</div>
        <div class="welcome-subtitle">Where ideas become reality, powered by AI magic</div>
    </div>
    """, unsafe_allow_html=True)

    _render_progress_dots(0)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Begin Your Journey", key="onboard_start", use_container_width=True, type="primary"):
            st.session_state.onboarding_step = 1
            st.rerun()


def _render_capabilities_screen():
    """Render the capabilities showcase screen."""
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <div class="section-header">What Can You Create?</div>
        <div class="section-subheader">From idea to production-ready code in minutes</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="capability-grid">
        <div class="capability-card">
            <div class="capability-icon">🌐</div>
            <div class="capability-title">Web Applications</div>
            <div class="capability-desc">Full-stack web apps with React, Vue, or vanilla JS. Complete with authentication, databases, and APIs.</div>
        </div>
        <div class="capability-card">
            <div class="capability-icon">📱</div>
            <div class="capability-title">Mobile Apps</div>
            <div class="capability-desc">Native iOS and Android apps, or cross-platform with React Native and Flutter.</div>
        </div>
        <div class="capability-card">
            <div class="capability-icon">📊</div>
            <div class="capability-title">Business Audits</div>
            <div class="capability-desc">Comprehensive UX audits, funnel analysis, and actionable recommendations with real metrics.</div>
        </div>
        <div class="capability-card">
            <div class="capability-icon">🔄</div>
            <div class="capability-title">Code Optimization</div>
            <div class="capability-desc">Upload existing code and let AI improve performance, security, and maintainability.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _render_progress_dots(1)
    _render_navigation_buttons(back=True)


def _render_agents_screen():
    """Render the AI agents showcase screen."""
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <div class="section-header">Meet Your AI Team</div>
        <div class="section-subheader">8+ specialized agents working together on your project</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="agent-flow">
        <div class="agent-node">
            <span class="agent-emoji">🎯</span>
            <span class="agent-name">Meta Prompt</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">📊</span>
            <span class="agent-name">Researcher</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">🤔</span>
            <span class="agent-name">Challenger</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">📋</span>
            <span class="agent-name">PM Agent</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">💡</span>
            <span class="agent-name">Ideas</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">🎨</span>
            <span class="agent-name">Designer</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">👨‍💻</span>
            <span class="agent-name">Senior Dev</span>
        </div>
        <span class="agent-arrow">→</span>
        <div class="agent-node">
            <span class="agent-emoji">🔄</span>
            <span class="agent-name">Reflector</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show what each agent does
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🎯 Meta Prompt Agent**
        Expands your idea into a comprehensive specification

        **📊 Research Agent**
        Analyzes market viability and competition

        **🤔 Challenger Agent**
        Stress-tests your concept for weaknesses

        **📋 PM Agent**
        Creates detailed requirements and user stories
        """)

    with col2:
        st.markdown("""
        **💡 Ideas Agent**
        Generates innovative feature suggestions

        **🎨 Design Agent**
        Creates UI/UX mockups and design systems

        **👨‍💻 Senior Dev Agent**
        Architects and implements the solution

        **🔄 Reflector Agent**
        Reviews and iteratively improves output
        """)

    _render_progress_dots(2)
    _render_navigation_buttons(back=True)


def _render_ready_screen():
    """Render the final ready screen."""
    st.markdown("""
    <div class="ready-container">
        <div class="ready-icon">✨</div>
        <div class="ready-title">You're All Set!</div>
        <div class="ready-message">
            Just describe your idea in plain English.<br>
            No technical knowledge required.<br>
            We'll handle the rest.
        </div>
    </div>
    """, unsafe_allow_html=True)

    _render_progress_dots(3)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Creating", key="onboard_finish", use_container_width=True, type="primary"):
            complete_onboarding()
            st.rerun()


def _render_progress_dots(current_step: int):
    """Render progress indicator dots."""
    dots_html = '<div class="progress-dots">'
    for i in range(4):
        active = "active" if i == current_step else ""
        dots_html += f'<div class="progress-dot {active}"></div>'
    dots_html += '</div>'
    st.markdown(dots_html, unsafe_allow_html=True)


def _render_navigation_buttons(back: bool = False):
    """Render navigation buttons."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if back and st.button("← Back", key=f"onboard_back_{st.session_state.onboarding_step}"):
            st.session_state.onboarding_step -= 1
            st.rerun()

    with col3:
        if st.button("Next →", key=f"onboard_next_{st.session_state.onboarding_step}", type="primary"):
            st.session_state.onboarding_step += 1
            st.rerun()


def render_skip_option():
    """Render a skip option for returning users."""
    st.markdown("""
    <div style="text-align: center; margin-top: 20px;">
        <p style="color: #6b7280; font-size: 14px;">
            Returning user? <span id="skip-link" style="color: #667eea; cursor: pointer;">Skip intro</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Use a small button styled as text
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Skip intro", key="skip_onboarding", type="secondary"):
            complete_onboarding()
            st.rerun()