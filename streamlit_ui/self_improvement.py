"""
Self-Improvement UI for Code Weaver Pro
Allows the system to analyze and improve its own code
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Callable
from .constants import COLORS, DIMENSIONS
import html  # For XSS protection (Issue 1 fix)

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize session state for terminal (persistent across reruns)
if 'terminal_messages' not in st.session_state:
    st.session_state.terminal_messages = []

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


def sanitize_html(text: str) -> str:
    """
    Sanitize text for safe HTML injection (Issue 1 fix: XSS protection)

    Args:
        text: Input text that may contain user-controlled content

    Returns:
        HTML-escaped safe text
    """
    if not isinstance(text, str):
        return ""
    return html.escape(text)


def sanitize_color(color: str) -> str:
    """
    Validate color is safe for CSS injection (Issue #8 fix: CSS injection protection)

    Args:
        color: Color value to validate

    Returns:
        Safe color value or gray fallback
    """
    import re

    if not isinstance(color, str):
        return "#808080"  # Gray fallback

    # Allow hex colors (#RRGGBB or #RGB)
    if re.match(r'^#[0-9A-Fa-f]{3}$', color) or re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return color

    # Whitelist of safe CSS color names
    safe_colors = {
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'white', 'black',
        'gray', 'grey', 'cyan', 'magenta', 'pink', 'brown', 'navy', 'teal',
        'lime', 'olive', 'maroon', 'aqua', 'silver', 'fuchsia'
    }

    if color.lower() in safe_colors:
        return color

    # Default fallback for unsafe values
    return "#808080"  # Gray


def show_success_celebration(score: float, fixes_applied: int) -> None:
    """
    Display animated success celebration (Phase 28: Success Celebrations)

    Shows confetti animation when cycle completes successfully with high score

    Args:
        score: Quality score achieved (0-10)
        fixes_applied: Number of fixes successfully applied
    """
    # Only celebrate if score is 8+ or 5+ fixes were applied
    should_celebrate = score >= 8.0 or fixes_applied >= 5

    if not should_celebrate:
        return

    # Determine celebration intensity based on achievements
    if score >= 9.5 and fixes_applied >= 10:
        celebration_level = "epic"
        message = "🎉 EPIC SUCCESS! Outstanding improvements!"
    elif score >= 9.0 or fixes_applied >= 7:
        celebration_level = "great"
        message = "🌟 Great work! Excellent improvements applied!"
    else:
        celebration_level = "good"
        message = "✨ Nice! Quality improvements complete!"

    # Issue #7 fix: Sanitize celebration message (defensive coding)
    safe_message = sanitize_html(message)

    # Issue #17 fix: Use dictionary for celebration level validation (defensive coding)
    confetti_counts = {'epic': 100, 'great': 60, 'good': 30}
    confetti_count = confetti_counts.get(celebration_level, 30)  # Default to 30

    # Animated celebration HTML/CSS
    celebration_html = f"""
    <style>
    @keyframes confetti-fall {{
        0% {{ transform: translateY(-100vh) rotate(0deg); opacity: 1; }}
        100% {{ transform: translateY(100vh) rotate(720deg); opacity: 0; }}
    }}

    @keyframes pulse-glow {{
        0%, 100% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.05); opacity: 0.8; }}
    }}

    .celebration-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }}

    .confetti {{
        position: absolute;
        width: 10px;
        height: 10px;
        background-color: #f0f;
        animation: confetti-fall 3s linear;
    }}

    .celebration-message {{
        position: fixed;
        top: 20%;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px 40px;
        border-radius: 12px;
        font-size: 1.5rem;
        font-weight: 700;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        animation: pulse-glow 1s ease-in-out 3;
        z-index: 10000;
    }}
    </style>

    <div class="celebration-container" id="celebration">
        <div class="celebration-message">
            {safe_message}
        </div>
    </div>

    <script>
    // Generate confetti particles
    (function() {{
        const container = document.getElementById('celebration');
        if (!container) return;

        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff',
                        '#ffa500', '#ff69b4', '#00ff7f', '#9370db'];
        const confettiCount = {confetti_count};  // Issue #17 fix: Validated count from Python

        for (let i = 0; i < confettiCount; i++) {{
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = (Math.random() * 2) + 's';
            confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
            container.appendChild(confetti);
        }}

        // Issue #12 fix: Remove celebration with buffer time to ensure animations complete
        // Max animation: 3s fall + pulse, add 500ms buffer
        const maxDuration = 4000;
        setTimeout(function() {{
            if (container && container.parentNode) {{
                container.parentNode.removeChild(container);
            }}
        }}, maxDuration + 500);  // 4.5s total
    }})();
    </script>
    """

    st.markdown(celebration_html, unsafe_allow_html=True)


def get_agent_avatar(message: str) -> str:
    """
    Get agent avatar/icon based on message content (Phase 27: Agent Avatar System)

    Returns unique icon for each agent type for better visual identification

    Args:
        message: Log message that might contain agent names

    Returns:
        Unicode emoji avatar for the agent
    """
    # Agent avatar mapping - Phase 27: Each agent has unique personality
    avatars = {
        'ANALYZER': '🔍',
        'VERIFIER': '✅',
        'CHALLENGER': '⚡',
        'FIXER': '🔧',
        'TESTER': '🧪',
        'SENIOR': '👴',
        'JUNIOR': '👶',
        'DESIGNER': '🎨',
        'PERFORMANCE': '⚡',
        'SECURITY': '🔒',
        'RESEARCH': '📚',
        'IDEAS': '💡',
        'ORCHESTRATOR': '🎯',
        'MANAGER': '👔',
        'CACHE': '💾',
        'BATCH': '📦',
        'FIX': '🔧',
        'TEST': '🧪',
        'QUALITY': '⭐',
        'EVALUATE': '📊',
        'COMPLETE': '✨',
        'CYCLE': '🔄',
        'APPROVAL': '👍',
        'PLANNING': '📋',
        'APPLY': '✏️',
        'GIT': '🌿'
    }

    # Find matching agent in message
    message_upper = message.upper()
    for agent_name, avatar in avatars.items():
        if f'[{agent_name}]' in message_upper:
            return avatar

    # Level-based default avatars
    if 'ERROR' in message_upper or '[X]' in message_upper:
        return '❌'
    elif 'WARNING' in message_upper or '[!]' in message_upper:
        return '⚠️'
    elif 'SUCCESS' in message_upper or '[OK]' in message_upper or '[+]' in message_upper:
        return '✅'

    # Default avatar
    return 'ℹ️'


def create_terminal_callback(terminal_placeholder: Any) -> Callable[[str, str], None]:
    """
    Create a terminal callback function with session state persistence.

    Args:
        terminal_placeholder: Streamlit empty placeholder for terminal output

    Returns:
        Function that logs messages to terminal with color-coded levels
    """
    def terminal_callback(message: str, level: str = "info") -> None:
        """Update terminal output with session state persistence"""
        # Initialize session state if needed (defensive check)
        if 'terminal_messages' not in st.session_state:
            st.session_state.terminal_messages = []

        timestamp = datetime.now().strftime("%H:%M:%S")
        raw_color = {
            "info": COLORS["status_info"],
            "success": COLORS["status_success"],
            "warning": COLORS["status_warning"],
            "error": COLORS["status_error"]
        }.get(level, COLORS["status_info"])

        # Issue #8 fix: Sanitize color for CSS injection protection
        color = sanitize_color(raw_color)

        # Phase 27: Add agent avatar for visual identification
        avatar = get_agent_avatar(message)

        # Issue 1 fix: Sanitize message for XSS protection
        safe_message = sanitize_html(message)

        # Store in session state for persistence
        st.session_state.terminal_messages.append(
            f'<span style="color: {color};">{avatar} [{timestamp}] {safe_message}</span>'
        )

        # Issue #10 fix: Keep fewer messages to reduce memory usage (25 instead of 50)
        MAX_TERMINAL_MESSAGES = 25
        if len(st.session_state.terminal_messages) > MAX_TERMINAL_MESSAGES:
            st.session_state.terminal_messages = st.session_state.terminal_messages[-MAX_TERMINAL_MESSAGES:]

        # Update display with auto-scroll
        terminal_html = f"""
        <div id="terminal-output" style="background-color: {COLORS['terminal_bg']}; border-radius: 8px; padding: 16px;
                    font-family: 'Courier New', monospace; height: 300px; overflow-y: auto;
                    border: 1px solid #444;">
            {'<br>'.join(st.session_state.terminal_messages)}
        </div>
        <script>
            // Auto-scroll to bottom
            var terminalDiv = document.getElementById('terminal-output');
            if (terminalDiv) {{
                terminalDiv.scrollTop = terminalDiv.scrollHeight;
            }}
        </script>
        """
        terminal_placeholder.markdown(terminal_html, unsafe_allow_html=True)

    return terminal_callback


def render_self_improvement() -> None:
    """Render the self-improvement interface"""

    # Issue #7: Maintain unified dark theme for visual continuity
    # Dark mode is now always active - no toggle to prevent theme fragmentation
    st.session_state.dark_mode = True  # Always dark mode for consistency

    # Apply unified dark theme CSS with purple accents (Issue #7: Theme consistency)
    theme_css = """
    <style>
    /* Unified dark theme for Self-Improve mode */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    .stMarkdown, .stText {
        color: #fafafa;
    }

    div[data-testid="stSidebar"] {
        background-color: #1a1d29;
    }

    /* Primary buttons - Purple gradient for brand consistency */
    .stButton > button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"] {
        min-height: 56px !important;
        min-width: 200px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: 2px solid rgba(102, 126, 234, 0.5) !important;
        font-weight: 700;
        font-size: 1.25rem;
        padding: 18px 36px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
        transition: all 0.2s ease !important;
    }

    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.5);
    }

    /* Secondary buttons - Dark theme with purple accents */
    .stButton > button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-secondary"],
    .stButton > button {
        min-height: 44px !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #fafafa !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 12px;
        transition: all 0.2s ease !important;
    }

    .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    .stButton > button:hover {
        background-color: rgba(102, 126, 234, 0.15) !important;
        border-color: #667eea !important;
        transform: translateY(-1px);
    }

    /* Focus states for accessibility */
    .stButton > button:focus-visible {
        outline: 3px solid #8b9eff !important;
        outline-offset: 3px !important;
        box-shadow: 0 0 0 6px rgba(139, 158, 255, 0.4) !important;
    }

    *:focus-visible {
        outline: 3px solid #8b9eff !important;
        outline-offset: 3px !important;
        box-shadow: 0 0 0 6px rgba(139, 158, 255, 0.35) !important;
    }

    /* Mobile touch targets */
    @media (max-width: 768px) {
        .stButton > button {
            min-height: 48px !important;
            width: 100% !important;
            margin-bottom: 16px !important;
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

    /* Input fields - Dark theme */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.05);
        color: #fafafa;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }

    code {
        background-color: #1a1d29;
        color: #667eea;
    }

    .stExpander {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* ===== GRADIENT HEADERS (Match onboarding style) ===== */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    /* Main page title (h2) */
    .stMarkdown h2 {
        font-size: 32px !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f64f59 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 16px !important;
        animation: fadeInUp 0.6s ease-out;
    }

    /* Section headers (h3) */
    .stMarkdown h3 {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #e8eaf6 !important;
        margin: 24px 0 16px 0 !important;
        padding-left: 16px !important;
        border-left: 4px solid;
        border-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%) 1;
        animation: slideInLeft 0.5s ease-out;
    }

    /* Subsection headers (h4) */
    .stMarkdown h4 {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #b8c1ec !important;
        margin: 16px 0 12px 0 !important;
        animation: fadeInUp 0.4s ease-out;
    }

    /* Card-like containers for sections */
    .stExpander {
        background: linear-gradient(135deg, rgba(30, 33, 57, 0.6) 0%, rgba(37, 40, 68, 0.6) 100%) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 12px !important;
        margin: 8px 0 !important;
        transition: all 0.3s ease !important;
    }

    .stExpander:hover {
        border-color: rgba(102, 126, 234, 0.4) !important;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15) !important;
    }

    /* Metric cards styling */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 33, 57, 0.8) 0%, rgba(37, 40, 68, 0.8) 100%) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 12px !important;
        padding: 16px !important;
    }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

    # Enhanced Hero Section for Self-Improve Mode (purple theme for brand consistency)
    st.markdown("""
    <div class="self-improve-hero" style="
        text-align: center;
        padding: 24px 20px;
        margin-bottom: 32px;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
    ">
        <div style="font-size: 48px; margin-bottom: 12px;">🔄</div>
        <h2 style="
            font-size: 28px;
            font-weight: 700;
            color: #e8eaf6;
            margin-bottom: 8px;
        ">Meta Self-Improvement</h2>
        <p style="
            font-size: 16px;
            color: #CBD5E1;
            max-width: 500px;
            margin: 0 auto;
        ">
            AI agents analyze and improve their own code, UI/UX, and capabilities.
            Watch as the system evolves itself in real-time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards explaining what each mode does (purple theme for brand consistency)
    st.markdown("""
    <div style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 32px;
    ">
        <div class="feature-card" style="
            background: rgba(30, 33, 57, 0.6);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <span style="font-size: 32px;">🔍</span>
            <h4 style="color: #e8eaf6; margin: 12px 0 8px; font-size: 15px;">Automated Analysis</h4>
            <p style="color: #9ca3af; font-size: 13px; margin: 0;">
                AI scans codebase for issues, bugs, and optimization opportunities
            </p>
        </div>
        <div class="feature-card" style="
            background: rgba(30, 33, 57, 0.6);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <span style="font-size: 32px;">🧪</span>
            <h4 style="color: #e8eaf6; margin: 12px 0 8px; font-size: 15px;">Test-Driven Fixes</h4>
            <p style="color: #9ca3af; font-size: 13px; margin: 0;">
                Changes are validated with automated tests before applying
            </p>
        </div>
        <div class="feature-card" style="
            background: rgba(30, 33, 57, 0.6);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <span style="font-size: 32px;">📊</span>
            <h4 style="color: #e8eaf6; margin: 12px 0 8px; font-size: 15px;">Quality Scoring</h4>
            <p style="color: #9ca3af; font-size: 13px; margin: 0;">
                Track improvements with objective quality metrics and scores
            </p>
        </div>
        <div class="feature-card" style="
            background: rgba(30, 33, 57, 0.6);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        ">
            <span style="font-size: 32px;">🔄</span>
            <h4 style="color: #e8eaf6; margin: 12px 0 8px; font-size: 15px;">Iterative Cycles</h4>
            <p style="color: #9ca3af; font-size: 13px; margin: 0;">
                Continuously improves until target quality score is reached
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not IMPROVER_AVAILABLE:
        st.error(f"⚠️ Self-improvement engine not available: {IMPORT_ERROR}")
        return

    # Improvement mode selector with section header (purple theme for brand consistency)
    st.markdown("""
    <div style="
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
        padding-bottom: 12px;
        margin-bottom: 20px;
    ">
        <h3 style="color: #e8eaf6; font-size: 18px; font-weight: 600; margin: 0;">
            🎯 Select Improvement Mode
        </h3>
    </div>
    """, unsafe_allow_html=True)

    mode_options = {
        "🎨 UI/UX": (ImprovementMode.UI_UX, "Make the interface more intuitive and user-friendly"),
        "⚡ Performance": (ImprovementMode.PERFORMANCE, "Speed up execution and optimize resource usage"),
        "🧠 Agent Quality": (ImprovementMode.AGENT_QUALITY, "Improve AI agent outputs and prompts"),
        "🔧 Code Quality": (ImprovementMode.CODE_QUALITY, "Refactor and optimize code structure"),
        "✨ Everything": (ImprovementMode.EVERYTHING, "Comprehensive improvement across all areas")
    }

    cols = st.columns([2, 2], gap="medium")

    with cols[0]:
        selected_mode_label = st.radio(
            "Focus Area",
            list(mode_options.keys()),
            index=4,  # Default to "Everything"
            help="Select which part of the codebase to analyze and improve. The agents will scan relevant files and suggest fixes."
        )

    selected_mode, mode_description = mode_options[selected_mode_label]

    with cols[1]:
        st.info(f"**{selected_mode_label}:** {mode_description}")

        # Show what will be analyzed
        if selected_mode == ImprovementMode.UI_UX:
            st.caption("📁 Will analyze: streamlit_ui/, workflow_builder/src/")
        elif selected_mode == ImprovementMode.PERFORMANCE:
            st.caption("📁 Will analyze: core/, server/")
        elif selected_mode == ImprovementMode.AGENT_QUALITY:
            st.caption("📁 Will analyze: core/*agent*, agents.config.json")

    # Iterative mode (LangGraph-powered)
    st.markdown("#### Improvement Strategy")

    cols2 = st.columns([2, 2], gap="medium")

    with cols2[0]:
        iterative_mode = st.checkbox(
            "🔄 Iterative Mode (LangGraph)",
            value=True,
            help="Continuously run improvement cycles until target score is reached or max 10 iterations (recommended for comprehensive improvements)"
        )

    with cols2[1]:
        if iterative_mode:
            target_score = st.slider(
                "Target Quality Score",
                min_value=7.0,
                max_value=10.0,
                value=9.0,
                step=0.5,
                help="System stops improving once this quality score is achieved (calculated based on issues found and fixed)"
            )
        else:
            target_score = None

    if iterative_mode:
        st.info("🧠 **Iterative Mode**: System will automatically run multiple cycles until it reaches the target quality score (max 10 iterations).")
    else:
        st.info("🔄 **Single-Pass Mode**: System will run one improvement cycle and stop.")

    # Enhancement suggestions toggle
    st.markdown("#### Enhancement Options")
    suggest_enhancements = st.checkbox(
        "💡 Include Feature Suggestions",
        value=False,
        help="Add Research & Ideas agents to suggest new features and enhancements (in addition to finding bugs)"
    )

    if suggest_enhancements:
        st.info("💡 **Enhancement Mode**: Research & Ideas agents will analyze the codebase and suggest new features to add.")

    # Forever mode checkbox
    forever_mode = st.checkbox(
        "🔁 Forever mode (manual control)",
        value=False,
        help="Continuously run cycles until you click Stop (ignores target score)"
    )

    # Target specific files (optional)
    st.markdown("#### Target Specific Files (Optional)")
    target_files_text = st.text_area(
        "File paths (one per line)",
        placeholder="core/orchestrator.py\nstreamlit_ui/main_interface.py\n(Leave empty to analyze all files)",
        height=100,
        help="Specify files to analyze, or leave empty to analyze entire codebase"
    )

    # Parse and validate target files (Issue #14 fix)
    if target_files_text.strip():
        target_files = []
        for line in target_files_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Validate path
            try:
                path = Path(line)
                if path.is_absolute():
                    st.warning(f"⚠️ Skipping absolute path: {line}")
                    continue
                if '..' in path.parts:
                    st.warning(f"⚠️ Skipping path traversal: {line}")
                    continue
                target_files.append(line)
            except Exception:
                st.warning(f"⚠️ Invalid path: {line}")
                continue
        target_files = target_files if target_files else None
    else:
        target_files = None

    # Phase 8: Cache Management Section
    st.markdown("---")
    st.markdown("#### 💾 Cache Management")

    try:
        from core.agent_cache import AgentCache
        from pathlib import Path

        # Get cache stats
        config = load_config()
        cache = AgentCache(Path(config['base_dir']))
        stats = cache.get_cache_stats()

        # Display cache stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cached Files", stats['total_entries'])
        with col2:
            st.metric("Cache Size", f"{stats['total_size_mb']:.2f} MB")

        if stats['expired_entries'] > 0:
            st.caption(f"⚠️ {stats['expired_entries']} expired entries")

        st.caption(f"TTL: {stats['ttl_hours']:.0f} hours | Location: `{Path(stats['cache_dir']).name}`")

        # Cache action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All", use_container_width=True, help="Clear all cached analysis results"):
                cleared = cache.clear_cache()
                st.success(f"✅ Cleared {cleared} cache entries")
                st.rerun()
        with col2:
            if st.button("🧹 Clear Expired", use_container_width=True, help="Clear only expired cache entries"):
                cleared = cache.clear_expired()
                if cleared > 0:
                    st.success(f"✅ Cleared {cleared} expired entries")
                    st.rerun()
                else:
                    st.info("No expired entries to clear")

    except Exception as e:
        st.caption(f"Cache unavailable: {str(e)[:50]}")

    # Start button - centered
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_button = st.button(
            "🚀 Start Improvement Cycle",
            use_container_width=True,
            type="primary"
        )

    # Execution
    if start_button:
        if forever_mode:
            run_forever_mode(selected_mode, target_files, suggest_enhancements)
        elif iterative_mode:
            run_iterative_mode(selected_mode, target_score, target_files, suggest_enhancements)
        else:
            run_single_cycle(selected_mode, target_files, suggest_enhancements)


def run_single_cycle(mode: str, target_files: Optional[List[str]] = None, suggest_enhancements: bool = False) -> None:
    """Run a single improvement cycle with optional manual issue selection"""
    st.markdown("---")
    st.markdown("### 📋 Improvement Cycle Results")

    # Create progress container
    progress_container = st.container()
    timeline_container = st.container()  # Phase 24: Timeline visualization
    terminal_container = st.container()
    selection_container = st.container()
    results_container = st.container()

    with timeline_container:
        timeline_placeholder = st.empty()
        # Display initial timeline
        with timeline_placeholder.container():
            display_interactive_timeline('analyze', 0.0)

    with progress_container:
        progress_bar = st.progress(0, text="Initializing...")

    with terminal_container:
        st.markdown("#### 💻 Live Output")
        terminal_placeholder = st.empty()

    # Create terminal callback with session state persistence
    terminal_callback = create_terminal_callback(terminal_placeholder)

    try:
        # Load config
        config = load_config()
        config['orchestration']['terminal_callback'] = terminal_callback

        # Create improver
        improver = SelfImprover(config)
        improver.set_log_callback(terminal_callback)

        # Get mode enum
        from core.self_improver import ImprovementMode
        mode_map = {
            'UI/UX': ImprovementMode.UI_UX,
            'Performance': ImprovementMode.PERFORMANCE,
            'Agent Quality': ImprovementMode.AGENT_QUALITY,
            'Code Quality': ImprovementMode.CODE_QUALITY,
            'Everything': ImprovementMode.EVERYTHING
        }
        improvement_mode = mode_map.get(mode, ImprovementMode.UI_UX)

        # Update progress
        progress_bar.progress(0.1, text="Analyzing codebase...")

        # Phase 24: Update timeline - Analyze stage
        with timeline_placeholder.container():
            display_interactive_timeline('analyze', 0.3)

        # Phase 1: Analyze and identify issues (don't fix yet)
        files_to_analyze = improver._get_files_to_analyze(target_files=target_files, mode=improvement_mode)
        screenshots = improver._capture_app_screenshots() if improvement_mode == ImprovementMode.UI_UX else []

        # Phase 24: Update timeline - Analysis in progress
        with timeline_placeholder.container():
            display_interactive_timeline('analyze', 0.7)

        all_issues = improver._identify_issues(files_to_analyze, improvement_mode, screenshots, suggest_enhancements)

        terminal_callback(f"Found {len(all_issues)} issues total", "success")

        progress_bar.progress(0.4, text="Analysis complete")

        # Phase 24: Update timeline - Verify stage
        with timeline_placeholder.container():
            display_interactive_timeline('verify', 0.5)

        # Phase 2: Show issue selection UI
        with selection_container:
            selected_issues = display_issue_selection_ui(all_issues, improver)

        if selected_issues is None:
            # Auto mode - let agents prioritize
            terminal_callback("Running auto mode - agents will select top 5 issues", "info")
            issues_to_fix = improver._prioritize_issues(all_issues)[:5]
        elif len(selected_issues) > 0:
            # Manual mode - use user selection
            terminal_callback(f"Fixing {len(selected_issues)} user-selected issues", "info")
            issues_to_fix = selected_issues
        else:
            # No selection made yet - stop here
            progress_bar.progress(0.4, text="Waiting for issue selection...")
            return

        # Phase 3: Generate and apply fixes for selected issues
        progress_bar.progress(0.6, text="Generating fixes...")

        # Phase 24: Update timeline - Challenge stage
        with timeline_placeholder.container():
            display_interactive_timeline('challenge', 0.5)

        fixes = improver._generate_fixes(issues_to_fix, improvement_mode)

        progress_bar.progress(0.8, text="Applying fixes...")

        # Phase 24: Update timeline - Fix stage
        with timeline_placeholder.container():
            display_interactive_timeline('fix', 0.5)

        applied_fixes = improver._apply_and_test_fixes(fixes, issues_to_fix, improvement_mode)

        terminal_callback(f"Applied {applied_fixes}/{len(fixes)} fixes", "success")

        # Phase 4: Complete the cycle (git operations, evaluation)
        progress_bar.progress(0.9, text="Finalizing...")

        # Phase 24: Update timeline - Test stage
        with timeline_placeholder.container():
            display_interactive_timeline('test', 0.8)

        # Create git branch and commit
        from datetime import datetime
        import subprocess
        import re

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"improvement/{mode.lower().replace(' ', '_')}_{timestamp}"

        # Issue 2 fix: Validate inputs for command injection protection
        # Validate branch name (alphanumeric, underscore, hyphen, forward slash only)
        if not re.match(r'^[a-zA-Z0-9_/-]+$', branch_name):
            # Issue #13 fix: Don't echo back potentially malicious input in error messages
            terminal_callback("Invalid branch name format", "error")
            raise ValueError("Branch name contains invalid characters")

        # Validate base_dir exists and is a directory
        base_dir_path = Path(improver.base_dir)
        if not base_dir_path.exists() or not base_dir_path.is_dir():
            # Issue #13 fix: Don't reveal internal paths
            terminal_callback("Invalid base directory configuration", "error")
            raise ValueError("Base directory does not exist or is not a directory")

        # Issue 4 fix: Add error handling for external processes
        try:
            result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=str(improver.base_dir),
                check=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            terminal_callback(f"Created branch: {branch_name}", "success")
        except subprocess.CalledProcessError as e:
            terminal_callback(f"Git checkout failed: {e.stderr}", "error")
            raise
        except subprocess.TimeoutExpired:
            terminal_callback("Git checkout timed out (30s)", "error")
            raise
        except Exception as e:
            terminal_callback(f"Git checkout error: {str(e)}", "error")
            raise

        try:
            subprocess.run(
                ['git', 'add', '.'],
                cwd=str(improver.base_dir),
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        except subprocess.CalledProcessError as e:
            terminal_callback(f"Git add failed: {e.stderr}", "error")
            raise
        except subprocess.TimeoutExpired:
            terminal_callback("Git add timed out (30s)", "error")
            raise

        commit_message = f"Apply {applied_fixes} improvements ({mode} mode)"
        try:
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=str(improver.base_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                terminal_callback("Changes committed successfully", "success")
        except subprocess.TimeoutExpired:
            terminal_callback("Git commit timed out (30s)", "error")
            raise

        # Get commit hash with error handling (Issue #6 fix)
        try:
            commit_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(improver.base_dir),
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )
            commit_hash = commit_result.stdout.strip()
        except subprocess.TimeoutExpired:
            terminal_callback("Git rev-parse timed out (10s)", "warning")
            commit_hash = "unknown"
        except Exception as e:
            terminal_callback(f"Failed to get commit hash: {str(e)}", "warning")
            commit_hash = "unknown"

        # Get diff with error handling (Issue #6 fix)
        try:
            diff_result = subprocess.run(
                ['git', 'diff', 'main'],
                cwd=str(improver.base_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            diff_output = diff_result.stdout
        except subprocess.TimeoutExpired:
            terminal_callback("Git diff timed out (30s)", "warning")
            diff_output = ""
        except Exception as e:
            terminal_callback(f"Failed to get diff: {str(e)}", "warning")
            diff_output = ""

        # Evaluate improvement
        scores = improver._evaluate_improvement(diff_output, improvement_mode)

        # Plan next iteration
        next_focus = improver._plan_next_iteration(all_issues, issues_to_fix)

        # Build result dictionary
        # Note: export_path was already written by _identify_issues calling _export_issues_to_file
        # We can construct the expected path or set to None
        from datetime import datetime as dt
        timestamp_approx = dt.now().strftime("%Y%m%d")
        export_path_hint = f"reports/issues_detailed_{mode.lower().replace(' ', '_')}_{timestamp_approx}_*.md"

        result = {
            'files_analyzed': len(files_to_analyze),
            'issues_found': len(all_issues),
            'fixes_applied': applied_fixes,
            'diff': diff_output,
            'scores': scores,
            'next_focus': next_focus,
            'branch_name': branch_name,
            'commit_hash': commit_hash,
            'issues': [improver._format_issue_summary(issue) for issue in issues_to_fix],
            'all_issues': [improver._format_issue_summary(issue) for issue in all_issues],
            'export_path': export_path_hint,  # Hint about where files were exported
            'fixes': fixes  # Phase 23: Store fixes data for diff viewer
        }

        progress_bar.progress(1.0, text="Complete!")

        # Phase 24: Update timeline - Complete!
        with timeline_placeholder.container():
            display_interactive_timeline('complete', 1.0)

        # Phase 28: Celebrate success!
        improvement_score = scores.get('improvement', 0) + scores.get('after', 5.0)
        show_success_celebration(improvement_score, applied_fixes)

        # Display results
        with results_container:
            display_improvement_results(result, improver)

    except Exception as e:
        terminal_callback(f"Fatal error: {str(e)}", "error")
        st.error(f"### ❌ Error\n\n{str(e)}")
        import traceback
        st.code(traceback.format_exc())


def run_iterative_mode(mode: str, target_score: float, target_files: Optional[List[str]] = None, suggest_enhancements: bool = False) -> None:
    """Run iterative improvement cycles until quality threshold is met"""
    st.markdown("---")
    st.markdown("### 🔄 Iterative Improvement - LangGraph Powered")

    st.info(f"🎯 **Target Score**: {target_score}/10 | **Max Iterations**: 10 | **Mode**: {mode}")

    # Create progress containers
    progress_container = st.container()
    terminal_container = st.container()
    results_container = st.container()

    with progress_container:
        iteration_metric = st.empty()
        score_metric = st.empty()
        progress_bar = st.progress(0, text="Initializing LangGraph workflow...")

    with terminal_container:
        st.markdown("#### 💻 Live Output")
        terminal_placeholder = st.empty()

    # Create terminal callback with session state persistence
    terminal_callback = create_terminal_callback(terminal_placeholder)

    try:
        # Import LangGraph workflow
        from core.langgraph_improver import run_iterative_improvement
        from core.self_improver import ImprovementMode

        # Map string mode to ImprovementMode enum value
        mode_map = {
            'ui_ux': 'ui_ux',
            'performance': 'performance',
            'agent_quality': 'agent_quality',
            'code_quality': 'code_quality',
            'everything': 'everything'
        }

        # Get mode value (handle if mode is already ImprovementMode enum)
        if hasattr(mode, 'value'):
            mode_str = mode.value
        else:
            mode_str = mode_map.get(str(mode).lower(), 'ui_ux')

        terminal_callback(f"🚀 Starting iterative improvement with LangGraph", "info")
        terminal_callback(f"   Mode: {mode_str}", "info")
        terminal_callback(f"   Target score: {target_score}/10", "info")
        if target_files:
            terminal_callback(f"   Target files: {len(target_files)} specific files", "info")
        else:
            terminal_callback(f"   Target files: All files in scope", "info")

        progress_bar.progress(0.1, text="Running LangGraph workflow...")

        # Run iterative improvement
        final_state = run_iterative_improvement(
            mode=mode_str,
            target_score=target_score,
            initial_score=5.0,
            suggest_enhancements=suggest_enhancements,
            target_files=target_files
        )

        progress_bar.progress(1.0, text="Complete!")

        # Phase 28: Celebrate iterative success!
        final_score = final_state.get('current_score', 0)
        total_fixes = final_state.get('total_fixes_applied', 0)
        show_success_celebration(final_score, total_fixes)

        # Display iteration history
        with results_container:
            st.markdown("---")
            st.markdown("### 📊 Iterative Improvement Results")

            # Summary metrics
            cols = st.columns(4, gap="small")
            iteration_count = len(final_state.get('iteration_history', []))
            cols[0].metric("Iterations", iteration_count)
            cols[1].metric("Final Score", f"{final_state.get('current_score', 0):.1f}/10")
            cols[2].metric("Total Issues", final_state.get('total_issues_found', 0))
            cols[3].metric("Total Fixes", final_state.get('total_fixes_applied', 0))

            # Iteration history
            st.markdown("### 📈 Iteration History")

            history = final_state.get('iteration_history', [])
            if history:
                # Create a table
                for entry in history:
                    with st.expander(f"Iteration {entry['iteration']} - Score: {entry['score']:.1f}/10", expanded=(entry['iteration'] == 1)):
                        cols = st.columns(3)
                        cols[0].metric("Issues Found", entry['issues_found'])
                        cols[1].metric("Fixes Applied", entry['fixes_applied'])
                        cols[2].metric("Score", f"{entry['score']:.1f}/10")

            # Quality feedback from AI (positive recognition!)
            quality_feedback = final_state.get('quality_feedback', '')
            if quality_feedback:
                st.markdown("### 🎉 Quality Assessment")
                st.info(quality_feedback)

            # Final status
            if final_state.get('current_score', 0) >= target_score:
                st.success(f"✅ **Target score reached!** Final score: {final_state.get('current_score', 0):.1f}/10")
            else:
                st.warning(f"⚠️ **Max iterations reached.** Final score: {final_state.get('current_score', 0):.1f}/10 (target: {target_score}/10)")

            # Next steps
            st.markdown("### 🎯 Next Steps")
            cols = st.columns(2, gap="small")
            if cols[0].button("🔄 Run Another Cycle", use_container_width=True):
                st.rerun()
            if cols[1].button("✅ Done", use_container_width=True):
                st.success("Improvement cycle complete!")

        terminal_callback(f"✅ Iterative improvement complete!", "success")

    except Exception as e:
        terminal_callback(f"Fatal error: {str(e)}", "error")
        st.error(f"### ❌ Error\n\n{str(e)}")
        import traceback
        st.code(traceback.format_exc())


def run_forever_mode(mode: str, target_files: Optional[List[str]] = None, suggest_enhancements: bool = False) -> None:
    """Run continuous improvement cycles"""
    st.markdown("---")
    st.markdown("### 🔁 Forever Mode - Continuous Improvement")

    # Issue 6 fix: Add maximum cycle limit to prevent infinite loops and memory leaks
    MAX_FOREVER_CYCLES = 100

    st.warning(f"⚠️ **Forever mode is running!** The system will continuously improve until you stop it (max {MAX_FOREVER_CYCLES} cycles).")

    # Stop button
    cols = st.columns(3, gap="small")
    stop_button = cols[1].button("🛑 STOP Forever Mode", use_container_width=True, type="secondary")

    if stop_button:
        st.session_state['forever_mode_active'] = False
        # Issue 6 fix: Clear accumulated data when stopping
        if 'forever_cycles' in st.session_state:
            del st.session_state['forever_cycles']
        st.success("✅ Forever mode stopped and cleaned up")
        return

    # Initialize session state
    if 'forever_mode_active' not in st.session_state:
        st.session_state['forever_mode_active'] = True
        st.session_state['forever_cycles'] = 0

    # Cycle counter
    current_cycles = st.session_state.get('forever_cycles', 0)
    st.metric("Cycles Completed", f"{current_cycles}/{MAX_FOREVER_CYCLES}")

    # Terminal
    terminal_placeholder = st.empty()

    # Create terminal callback with session state persistence
    terminal_callback = create_terminal_callback(terminal_placeholder)

    try:
        config = load_config()
        config['orchestration']['terminal_callback'] = terminal_callback
        improver = SelfImprover(config)

        # Run cycles
        while st.session_state.get('forever_mode_active', False):
            # Issue #5 fix: Double-check flag before expensive operation (race condition protection)
            if not st.session_state.get('forever_mode_active', False):
                break

            cycle_num = st.session_state['forever_cycles'] + 1

            # Issue 6 fix: Enforce maximum cycle limit
            if cycle_num > MAX_FOREVER_CYCLES:
                terminal_callback(f"⚠️ Reached maximum cycle limit ({MAX_FOREVER_CYCLES}). Stopping forever mode.", "warning")
                st.session_state['forever_mode_active'] = False
                # Clear accumulated data
                if 'forever_cycles' in st.session_state:
                    del st.session_state['forever_cycles']
                st.rerun()
                break

            terminal_callback(f"🔄 Starting cycle {cycle_num}/{MAX_FOREVER_CYCLES}...", "info")

            result = improver.run_cycle(
                mode=mode,
                target_files=target_files,
                max_issues=3,  # Fewer issues per cycle in forever mode
                suggest_enhancements=suggest_enhancements
            )

            st.session_state['forever_cycles'] = cycle_num
            terminal_callback(f"✅ Cycle {cycle_num} complete!", "success")

            # Check if there are more issues
            if result['issues_found'] == 0:
                terminal_callback("🎉 No more issues found! Codebase is optimized.", "success")
                st.session_state['forever_mode_active'] = False
                # Issue 6 fix: Clear accumulated data when done
                if 'forever_cycles' in st.session_state:
                    del st.session_state['forever_cycles']
                # Force UI update to show final counter
                st.rerun()
                break

            # Issue #5 fix: Check flag again before rerun (prevent extra cycles after stop)
            if not st.session_state.get('forever_mode_active', False):
                break

            # Rerun to update UI
            st.rerun()
            break  # Issue #5 fix: Prevent code after rerun from executing

    except Exception as e:
        terminal_callback(f"Fatal error: {str(e)}", "error")
        st.session_state['forever_mode_active'] = False
        # Issue 6 fix: Clear accumulated data on error
        if 'forever_cycles' in st.session_state:
            del st.session_state['forever_cycles']


def generate_markdown_report(result: Dict[str, Any]) -> str:
    """Generate a comprehensive markdown report of improvement results"""
    from datetime import datetime

    all_issues = result.get('all_issues', [])

    # Handle "no issues" case with a positive report
    if not all_issues:
        report = f"""# Code Improvement Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Files Analyzed:** {result['files_analyzed']}
- **Issues Found:** 0
- **Assessment:** ✅ Code quality is excellent!

## Analysis Details
{result['files_analyzed']} files were thoroughly analyzed by specialized AI agents.
No bugs or enhancements were identified. Your codebase follows best practices.

**Score:** {result['scores']['after']}/10

**Next Focus:** {result.get('next_focus', 'Maintain current quality standards')}

---

*Report generated by Code Weaver Pro Self-Improvement System*
"""
        return report

    # Normal report when issues exist
    report = f"""# Code Improvement Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Files Analyzed:** {result['files_analyzed']}
- **Issues Found:** {result['issues_found']}
- **Fixes Applied:** {result['fixes_applied']}
- **Score Before:** {result['scores']['before']}/10
- **Score After:** {result['scores']['after']}/10
- **Improvement:** +{result['scores']['improvement']}/10
- **Git Branch:** `{result.get('branch_name', 'N/A')}`
- **Commit Hash:** `{result.get('commit_hash', 'N/A')}`

---

## All Issues Found ({len(all_issues)})

"""

    # Group by type and severity
    bugs = [i for i in all_issues if i.get('type') == 'BUG']
    enhancements = [i for i in all_issues if i.get('type') == 'ENHANCEMENT']

    # Issue #16 fix: Use list concatenation instead of repeated += for better performance
    report_parts = [report]

    if bugs:
        report_parts.append(f"### 🐛 Bugs ({len(bugs)})\n\n")
        for i, issue in enumerate(bugs, 1):
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
            report_parts.append(f"{i}. {severity_emoji} **[{issue['severity']}]** {issue['title']}\n")
            report_parts.append(f"   - **File:** `{issue['file']}`\n")
            report_parts.append(f"   - **Description:** {issue['description']}\n")
            report_parts.append(f"   - **Suggested Fix:** {issue['suggestion']}\n\n")

    if enhancements:
        report_parts.append(f"### 💡 Enhancements ({len(enhancements)})\n\n")
        for i, issue in enumerate(enhancements, 1):
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
            report_parts.append(f"{i}. {severity_emoji} **[{issue['severity']}]** {issue['title']}\n")
            report_parts.append(f"   - **File:** `{issue['file']}`\n")
            report_parts.append(f"   - **Description:** {issue['description']}\n")
            report_parts.append(f"   - **Suggested Enhancement:** {issue['suggestion']}\n\n")

    # Continue building report with list (Issue #16 fix)
    report_parts.append(f"""
---

## Issues Prioritized & Fixed ({len(result.get('issues', []))})

""")

    for i, issue in enumerate(result.get('issues', []), 1):
        severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(issue['severity'], "⚪")
        report_parts.append(f"{i}. {severity_emoji} **[{issue['severity']}]** {issue['title']}\n")
        report_parts.append(f"   - **File:** `{issue['file']}`\n")
        report_parts.append(f"   - **Status:** ✅ FIXED\n")
        report_parts.append(f"   - **Description:** {issue['description']}\n")
        report_parts.append(f"   - **Fix Applied:** {issue['suggestion']}\n\n")

    report_parts.append(f"""
---

## Next Focus
{result.get('next_focus', 'Continue improving code quality')}

---

*Report generated by Code Weaver Pro Self-Improvement System*
""")

    # Join all parts once at the end (much more efficient than repeated +=)
    return ''.join(report_parts)


def generate_json_report(result: Dict[str, Any]) -> str:
    """Generate a JSON report of improvement results"""
    import json
    from datetime import datetime

    report_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "files_analyzed": result['files_analyzed'],
            "issues_found": result['issues_found'],
            "fixes_applied": result['fixes_applied'],
            "scores": result['scores'],
            "git_branch": result.get('branch_name', 'N/A'),
            "commit_hash": result.get('commit_hash', 'N/A')
        },
        "all_issues": result.get('all_issues', []),
        "prioritized_issues": result.get('issues', []),
        "next_focus": result.get('next_focus', ''),
        "diff_summary": result.get('diff', '')[:500] + "..." if len(result.get('diff', '')) > 500 else result.get('diff', '')
    }

    return json.dumps(report_data, indent=2)


def display_issue_card(issue: Dict[str, Any], index: int, is_fixed: bool = False) -> None:
    """
    Display a single issue as a visual card (Phase 22: Visual Issue Cards)

    Args:
        issue: Issue dictionary
        index: Issue number
        is_fixed: Whether this issue has been fixed
    """
    # Color scheme by severity
    severity_colors = {
        'HIGH': {'border': COLORS["severity_high"], 'bg': '#2a1a1a', 'badge': COLORS["severity_high"]},
        'MEDIUM': {'border': COLORS["severity_medium"], 'bg': '#2a2410', 'badge': COLORS["severity_medium"]},
        'LOW': {'border': COLORS["severity_low"], 'bg': '#1a2a1a', 'badge': COLORS["severity_low"]}
    }

    severity = issue.get('severity', 'LOW')
    colors = severity_colors.get(severity, severity_colors['LOW'])

    # Icon by type
    icon = '🐛' if issue.get('type') == 'BUG' else '💡'

    # Issue 1 fix: Sanitize all user-controlled content for XSS protection
    title_text = sanitize_html(issue.get('title', 'Untitled Issue'))
    description_text = sanitize_html(issue.get('description', 'No description available'))
    suggestion_text = sanitize_html(issue.get('suggestion', 'No suggestion available'))
    file_text = sanitize_html(issue.get('file', 'unknown'))
    type_text = sanitize_html(issue.get('type', 'BUG'))

    # Status badge
    status_badge = ""
    if is_fixed:
        status_badge = f"""
        <span style="
            background: {COLORS["status_success"]};
            color: #000;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 8px;
        ">
            ✓ FIXED
        </span>
        """

    # Card HTML with hover animation
    card_html = f"""
    <div style="
        border-left: 4px solid {colors['border']};
        background: {colors['bg']};
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
    " onmouseover="this.style.transform='translateX(4px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)';"
       onmouseout="this.style.transform='translateX(0)'; this.style.boxShadow='none';">

        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <div style="flex: 1;">
                <span style="font-size: 1.3rem; margin-right: 8px;">{icon}</span>
                <span style="font-weight: 600; font-size: 1.05rem; color: white;">
                    {title_text}
                </span>
                {status_badge}
            </div>
            <div style="display: flex; gap: 8px;">
                <span style="
                    background: {colors['badge']};
                    color: #000;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    font-weight: 600;
                ">
                    {severity}
                </span>
                <span style="
                    background: #333;
                    color: #fff;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                ">
                    {type_text}
                </span>
            </div>
        </div>

        <div style="color: #bbb; font-size: 0.9rem; margin-bottom: 8px;">
            📁 <code style="background: #1a1d29; padding: 2px 6px; border-radius: 3px; color: {COLORS["status_system"]};">
                {file_text}
            </code>
        </div>

        <div style="color: #ddd; font-size: 0.95rem; line-height: 1.5; margin-bottom: 12px;">
            {description_text}
        </div>

        <details style="color: #aaa; font-size: 0.9rem;">
            <summary style="cursor: pointer; color: {COLORS["status_system"]}; font-weight: 500;">
                💡 {'Fix Applied' if is_fixed else 'Suggested Fix'}
            </summary>
            <div style="margin-top: 8px; padding: 12px; background: #1a1d29; border-radius: 6px; color: #ddd;">
                {suggestion_text}
            </div>
        </details>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def display_interactive_timeline(current_stage: str, progress: float = 0.5) -> None:
    """
    Display animated workflow timeline (Phase 24: Interactive Progress Visualization)

    Shows horizontal timeline with:
    - Stage indicators (Analyze → Verify → Challenge → Fix → Test)
    - Animated progress bar
    - Status colors (complete, active, pending)
    - Live progress within current stage

    Args:
        current_stage: One of 'analyze', 'verify', 'challenge', 'fix', 'test', 'complete'
        progress: Progress within current stage (0.0 to 1.0)
    """
    stages = [
        {'id': 'analyze', 'name': 'Analyze', 'icon': '🔍', 'color': '#00aaff'},
        {'id': 'verify', 'name': 'Verify', 'icon': '✓', 'color': '#44ff44'},
        {'id': 'challenge', 'name': 'Challenge', 'icon': '⚡', 'color': '#ffaa44'},
        {'id': 'fix', 'name': 'Fix', 'icon': '🔧', 'color': '#ff44ff'},
        {'id': 'test', 'name': 'Test', 'icon': '🧪', 'color': '#44ffff'},
        {'id': 'complete', 'name': 'Done', 'icon': '✅', 'color': '#44ff44'}
    ]

    # Determine status for each stage
    try:
        current_idx = next(i for i, s in enumerate(stages) if s['id'] == current_stage)
    except StopIteration:
        current_idx = 0  # Default to first stage if not found

    for i, stage in enumerate(stages):
        if i < current_idx:
            stage['status'] = 'complete'
        elif i == current_idx:
            stage['status'] = 'active'
        else:
            stage['status'] = 'pending'

    # Build timeline HTML with animations
    timeline_html = """
    <style>
    @keyframes pulse {
        0%, 100% { transform: scale(1); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        50% { transform: scale(1.08); box-shadow: 0 6px 20px rgba(0,150,255,0.6); }
    }
    @keyframes shimmer {
        0% { background-position: -100% 0; }
        100% { background-position: 100% 0; }
    }
    .timeline-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 24px;
        background: linear-gradient(135deg, #1a1d29 0%, #2a2d39 100%);
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .timeline-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    .timeline-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .timeline-circle.active {
        animation: pulse 1.5s infinite;
    }
    .timeline-label {
        margin-top: 8px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .timeline-connector {
        flex: 1;
        height: 3px;
        margin: 0 -10px;
        position: relative;
        top: -30px;
        transition: all 0.3s ease;
    }
    .timeline-progress {
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, transparent 0%, #333 0%);
        border-radius: 2px;
        margin-top: 4px;
        overflow: hidden;
    }
    .timeline-progress-bar {
        height: 100%;
        background: linear-gradient(90deg, rgba(0,170,255,0.3) 0%, rgba(0,170,255,1) 50%, rgba(0,170,255,0.3) 100%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite linear;
        transition: width 0.3s ease;
    }
    </style>
    """

    timeline_html += '<div class="timeline-container">'

    for i, stage in enumerate(stages):
        status = stage['status']

        # Determine circle style
        if status == 'complete':
            bg_color = stage['color']
            border_color = stage['color']
            icon_opacity = '1'
            animation_class = ''
        elif status == 'active':
            bg_color = stage['color']
            border_color = stage['color']
            icon_opacity = '1'
            animation_class = 'active'
        else:
            bg_color = '#333'
            border_color = '#555'
            icon_opacity = '0.4'
            animation_class = ''

        label_color = 'white' if status != 'pending' else '#888'

        timeline_html += f"""
        <div class="timeline-stage">
            <div class="timeline-circle {animation_class}" style="
                background: {bg_color};
                border: 3px solid {border_color};
                opacity: {icon_opacity};
            ">
                {stage['icon']}
            </div>
            <div class="timeline-label" style="color: {label_color};">
                {stage['name']}
            </div>
        """

        # Show progress bar for active stage
        if status == 'active':
            # Issue #15 fix: Clamp progress to [0, 1] range to prevent overflow
            clamped_progress = max(0.0, min(1.0, progress))
            progress_width = int(clamped_progress * 100)
            timeline_html += f"""
            <div class="timeline-progress">
                <div class="timeline-progress-bar" style="width: {progress_width}%;"></div>
            </div>
            """

        timeline_html += '</div>'

        # Add connector line between stages
        if i < len(stages) - 1:
            connector_color = stage['color'] if status == 'complete' else '#555'
            timeline_html += f'<div class="timeline-connector" style="background: {connector_color};"></div>'

    timeline_html += '</div>'

    st.markdown(timeline_html, unsafe_allow_html=True)


def display_issue_heat_map(issues: List[Dict[str, Any]]) -> None:
    """
    Display visual heat map of issues by file/folder (Phase 25: Issue Density Visualization)

    Shows:
    - Color-coded folders by issue count (red = many, green = few)
    - Issue count badges on each file
    - Expandable folder tree structure
    - Quick visual identification of problem areas

    Args:
        issues: List of all issues found
    """
    from collections import defaultdict

    if not issues:
        st.info("✅ No issues found! Heat map not needed.")
        return

    st.markdown("### 🗺️ Issue Heat Map")
    st.caption("Color intensity shows issue density - red = high, yellow = medium, green = low")

    # Count issues per file
    issue_counts = defaultdict(int)
    for issue in issues:
        file_path = issue.get('file', '')
        if file_path:
            # Issue 3 & 9 fix: Validate file path to prevent path traversal (improved normalization)
            try:
                path_obj = Path(file_path)

                # Issue #9 fix: Normalize path to resolve . and .. (catches more traversal attempts)
                try:
                    normalized = path_obj.resolve(strict=False)  # strict=False allows non-existent paths
                except Exception:
                    st.warning(f"⚠️ Invalid file path in issue: {file_path}")
                    continue

                # Check for absolute paths (security risk)
                if path_obj.is_absolute() or normalized.is_absolute():
                    st.warning(f"⚠️ Skipping absolute path in issue: {file_path}")
                    continue

                # Check for path traversal in original path
                if '..' in path_obj.parts:
                    st.warning(f"⚠️ Skipping path traversal attempt: {file_path}")
                    continue

                # Path is safe, count it
                issue_counts[file_path] += 1
            except Exception as e:
                st.warning(f"⚠️ Invalid file path in issue: {file_path} ({str(e)})")
                continue

    if not issue_counts:
        st.info("No file paths in issues")
        return

    # Build folder tree (bug fix: store full paths to avoid path separator issues)
    folder_tree = defaultdict(list)
    for file_path in issue_counts.keys():
        path = Path(file_path)
        folder = str(path.parent)
        # Store tuple of (filename, full_path) to preserve original path
        folder_tree[folder].append((path.name, file_path))

    # Determine color based on issue count
    def get_color(count):
        if count == 0:
            return COLORS["severity_low"]  # Green
        elif count <= 2:
            return '#ffaa44'  # Orange
        elif count <= 5:
            return '#ff8844'  # Dark orange
        else:
            return COLORS["severity_high"]  # Red

    # Build heat map HTML
    heat_map_html = """
    <style>
    .heatmap-container {
        background: #1a1d29;
        padding: 20px;
        border-radius: 12px;
        max-height: 500px;
        overflow-y: auto;
    }
    .heatmap-folder {
        margin-bottom: 12px;
    }
    .heatmap-folder-header {
        cursor: pointer;
        padding: 10px;
        border-radius: 6px;
        font-weight: 600;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .heatmap-folder-header:hover {
        transform: translateX(2px);
    }
    .heatmap-file {
        padding: 8px 12px;
        margin-bottom: 4px;
        margin-left: 20px;
        border-radius: 4px;
        color: #ddd;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .heatmap-file:hover {
        transform: translateX(4px);
    }
    .heatmap-badge {
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 700;
        color: #000;
    }
    </style>
    <div class="heatmap-container">
    """

    # Sort folders by total issue count (descending)
    folder_issue_counts = {
        folder: sum(issue_counts[full_path] for _, full_path in files)
        for folder, files in folder_tree.items()
    }
    sorted_folders = sorted(folder_issue_counts.items(), key=lambda x: x[1], reverse=True)

    for folder, folder_issue_count in sorted_folders:
        files = folder_tree[folder]
        folder_color = get_color(folder_issue_count)

        # Issue 1 fix: Sanitize folder name for XSS protection
        safe_folder = sanitize_html(folder if folder != '.' else 'Root')

        # Folder summary
        heat_map_html += f"""
        <details class="heatmap-folder" open>
            <summary class="heatmap-folder-header" style="
                background: linear-gradient(90deg, {folder_color}22 0%, transparent 100%);
                border-left: 4px solid {folder_color};
            ">
                <span>📁 {safe_folder}</span>
                <span class="heatmap-badge" style="background: {folder_color};">
                    {folder_issue_count}
                </span>
            </summary>
        """

        # Files in folder (sorted by issue count)
        # Bug fix: files is now a list of (filename, full_path) tuples
        file_issues = [(file_name, issue_counts[full_path]) for file_name, full_path in files]
        sorted_files = sorted(file_issues, key=lambda x: x[1], reverse=True)

        for file_name, count in sorted_files:
            color = get_color(count)

            # Issue 1 fix: Sanitize file name for XSS protection
            safe_file_name = sanitize_html(file_name)

            heat_map_html += f"""
            <div class="heatmap-file" style="
                background: linear-gradient(90deg, {color}11 0%, transparent 100%);
                border-left: 2px solid {color};
            ">
                <span>📄 {safe_file_name}</span>
                <span class="heatmap-badge" style="background: {color};">
                    {count}
                </span>
            </div>
            """

        heat_map_html += '</details>'

    heat_map_html += '</div>'

    st.markdown(heat_map_html, unsafe_allow_html=True)

    # Summary statistics
    col1, col2, col3 = st.columns(3)

    # Issue #18 fix: Add defensive check for division by zero
    if issue_counts:
        max_issues = max(issue_counts.values())
        avg_issues = sum(issue_counts.values()) / len(issue_counts)
        col1.metric("Total Files", len(issue_counts))
        col2.metric("Most Issues (1 file)", max_issues)
        col3.metric("Avg Issues/File", f"{avg_issues:.1f}")
    else:
        col1.metric("Total Files", 0)
        col2.metric("Most Issues (1 file)", 0)
        col3.metric("Avg Issues/File", "0.0")


def display_syntax_highlighted_diff(file_path: str, before_content: str, after_content: str) -> None:
    """
    Display side-by-side syntax-highlighted diff (Phase 23: Visual Diff Viewer)

    Shows before/after code comparison with:
    - Side-by-side layout
    - Syntax highlighting (language-specific)
    - Line-level diff highlighting
    - Change metrics

    Args:
        file_path: Path to file being compared
        before_content: Original file content
        after_content: Fixed file content
    """
    import difflib
    from pathlib import Path

    # Issue #11 fix: Validate file_path before use
    try:
        safe_path = Path(file_path)
        # Check for absolute paths or path traversal
        if safe_path.is_absolute() or '..' in safe_path.parts:
            st.error(f"⚠️ Invalid file path: {file_path}")
            return
        display_name = sanitize_html(safe_path.name)
    except Exception as e:
        st.error(f"⚠️ Invalid file path: {file_path}")
        return

    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_for_filename, TextLexer
        from pygments.formatters import HtmlFormatter
        from pygments.util import ClassNotFound
        has_pygments = True
    except ImportError:
        has_pygments = False
        st.warning("⚠️ Pygments not installed. Install with: pip install pygments")

    st.markdown("### 🔍 Code Comparison")
    st.info(f"**File:** `{display_name}`")

    # Generate diff statistics
    diff_lines = list(difflib.unified_diff(
        before_content.splitlines(keepends=False),
        after_content.splitlines(keepends=False),
        lineterm=''
    ))

    # Count changes
    added_lines = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    removed_lines = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

    # Show metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Lines Added", f"+{added_lines}", delta_color="normal")
    col2.metric("Lines Removed", f"-{removed_lines}", delta_color="inverse")
    col3.metric("Net Change", f"{added_lines - removed_lines:+d}")

    if has_pygments:
        # Detect language and get lexer
        try:
            lexer = get_lexer_for_filename(file_path)
            language = lexer.name
        except (ClassNotFound, ValueError):
            # Unknown file type or extension - fallback to plain text
            lexer = TextLexer()
            language = "Text"

        st.caption(f"Language: {language}")

        # Create formatter with line numbers
        formatter = HtmlFormatter(
            style='monokai',
            linenos='inline',
            cssclass='highlight',
            wrapcode=True
        )

        # Highlight both versions
        before_html = highlight(before_content, lexer, formatter)
        after_html = highlight(after_content, lexer, formatter)

        # Get CSS for syntax highlighting
        css = formatter.get_style_defs('.highlight')

        # Issue #19 fix: Use viewport-relative height instead of hardcoded 600px
        # This adapts better to different screen sizes (70% of viewport height)
        diff_max_height = "70vh"

        # Build side-by-side comparison
        diff_html = f"""
        <style>
        {css}
        .diff-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            max-height: {diff_max_height};
            background: #1e1e1e;
            border-radius: 8px;
            padding: 16px;
            overflow: hidden;
        }}
        .diff-column {{
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}
        .diff-header {{
            padding: 8px;
            border-radius: 6px 6px 0 0;
            font-weight: 600;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        .diff-before {{
            background: #2a1a1a;
            color: {COLORS["severity_high"]};
        }}
        .diff-after {{
            background: #1a2a1a;
            color: {COLORS["severity_low"]};
        }}
        .diff-content {{
            padding: 12px;
            overflow-x: auto;
            overflow-y: auto;
            flex: 1;
            background: #1e1e1e;
        }}
        .diff-content .highlight {{
            background: transparent !important;
            margin: 0;
            font-size: 0.85rem;
            line-height: 1.4;
        }}
        .diff-content pre {{
            margin: 0;
            background: transparent !important;
        }}
        </style>

        <div class="diff-container">
            <!-- Before column -->
            <div class="diff-column" style="border-right: 2px solid #444;">
                <div class="diff-header diff-before">
                    ❌ Before ({len(before_content.splitlines())} lines)
                </div>
                <div class="diff-content">
                    {before_html}
                </div>
            </div>

            <!-- After column -->
            <div class="diff-column">
                <div class="diff-header diff-after">
                    ✅ After ({len(after_content.splitlines())} lines)
                </div>
                <div class="diff-content">
                    {after_html}
                </div>
            </div>
        </div>
        """

        st.markdown(diff_html, unsafe_allow_html=True)
    else:
        # Fallback to plain text columns without syntax highlighting
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**❌ Before**")
            st.code(before_content, language=None)

        with col2:
            st.markdown("**✅ After**")
            st.code(after_content, language=None)

    # Show unified diff in expander
    with st.expander("📝 View Unified Diff"):
        diff_text = '\n'.join(diff_lines)
        if diff_text:
            st.code(diff_text, language='diff')
        else:
            st.info("No differences found")


def display_improvement_results(result: Dict[str, Any], improver: 'SelfImprover') -> None:
    """Display improvement cycle results"""
    st.markdown("---")

    # Quick Actions Panel (prominent at top)
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">📥 Quick Actions</h3>
        </div>
        """, unsafe_allow_html=True)

        issue_count = len(result.get('all_issues', []))
        bug_count = len([i for i in result.get('all_issues', []) if i.get('type') == 'BUG'])
        enhancement_count = len([i for i in result.get('all_issues', []) if i.get('type') == 'ENHANCEMENT'])

        # Show summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Issues", issue_count)
        col2.metric("🐛 Bugs", bug_count)
        col3.metric("💡 Enhancements", enhancement_count)

        # Download buttons (prominent)
        st.markdown("**Download Full Reports:**")

        markdown_report = generate_markdown_report(result)
        json_report = generate_json_report(result)

        button_cols = st.columns(2)
        with button_cols[0]:
            st.download_button(
                "📄 Markdown (All Issues)",
                markdown_report,
                f"all_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
                type="primary"
            )
        with button_cols[1]:
            st.download_button(
                "📊 JSON (All Issues)",
                json_report,
                f"all_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                type="primary"
            )

        # Show export path if available
        if result.get('export_path'):
            st.info(f"💾 **Files also exported to:** `{result['export_path']}`")

    st.markdown("---")

    # Summary metrics
    cols = st.columns(4, gap="small")
    cols[0].metric("Files Analyzed", result['files_analyzed'])
    cols[1].metric("Issues Found", result['issues_found'])
    cols[2].metric("Fixes Applied", result['fixes_applied'])
    improvement = result['scores']['improvement']
    cols[3].metric(
        "Improvement",
        f"+{improvement}" if improvement > 0 else str(improvement),
        delta=f"{improvement}/10"
    )

    # Export buttons - ALWAYS show (even if no issues found)
    st.markdown("---")
    st.markdown("### 📥 Export Reports")

    # Generate reports
    markdown_report = generate_markdown_report(result)
    json_report = generate_json_report(result)

    # Show issue count with appropriate message
    issue_count = len(result.get('all_issues', []))
    if issue_count > 0:
        st.info(f"📊 **{issue_count} issues found** - Download comprehensive reports below")
    else:
        st.success("✅ **No issues found!** Your codebase is in excellent shape. Download report for details.")

    cols = st.columns(2, gap="small")

    with cols[0]:
        st.download_button(
            label="📄 Download Markdown Report",
            data=markdown_report,
            file_name=f"improvement_report_{result.get('branch_name', 'report')}.md",
            mime="text/markdown",
            use_container_width=True,
            help="Human-readable report with all findings and suggestions"
        )

    with cols[1]:
        st.download_button(
            label="📊 Download JSON Report",
            data=json_report,
            file_name=f"improvement_report_{result.get('branch_name', 'report')}.json",
            mime="application/json",
            use_container_width=True,
            help="Machine-readable report for programmatic analysis"
        )

    # Issues found (prioritized for fixing) - Phase 22: Visual Issue Cards
    if result['issues']:
        st.markdown("### 🔍 Issues Prioritized & Fixed")

        for i, issue in enumerate(result['issues'], 1):
            display_issue_card(issue, i, is_fixed=True)

    # All issues found
    if result.get('all_issues') and len(result.get('all_issues', [])) > len(result.get('issues', [])):
        remaining_issues = len(result['all_issues']) - len(result['issues'])
        st.markdown(f"### 📋 All Issues Found ({len(result['all_issues'])} total)")
        st.info(f"**Note:** {len(result['issues'])} issues were prioritized and fixed. {remaining_issues} additional issues were identified for future improvement.")

        # Phase 25: Display heat map for visual issue density
        st.markdown("---")
        display_issue_heat_map(result['all_issues'])
        st.markdown("---")

        with st.expander(f"View All {len(result['all_issues'])} Issues", expanded=False):
            # Group by type (Phase 22: Visual Issue Cards)
            bugs = [i for i in result['all_issues'] if i.get('type') == 'BUG']
            enhancements = [i for i in result['all_issues'] if i.get('type') == 'ENHANCEMENT']

            if bugs:
                st.markdown(f"#### 🐛 Bugs ({len(bugs)})")
                for i, issue in enumerate(bugs, 1):
                    display_issue_card(issue, i, is_fixed=False)

            if enhancements:
                st.markdown(f"#### 💡 Enhancements ({len(enhancements)})")
                for i, issue in enumerate(enhancements, 1):
                    display_issue_card(issue, i, is_fixed=False)

    # Phase 23: Visual Diff Viewer for Applied Fixes
    if result.get('fixes') and result['fixes_applied'] > 0:
        st.markdown("---")
        st.markdown("### 🔍 Code Changes Review")
        st.info(f"💡 **Tip:** Review the before/after comparisons below to see exactly what was changed")

        applied_fixes = [fix for fix in result.get('fixes', []) if fix.get('fixed_content')]

        if applied_fixes:
            for idx, fix in enumerate(applied_fixes[:5], 1):  # Show first 5 fixes
                file_path = fix.get('file', 'unknown')
                issue = fix.get('issue', {})

                with st.expander(f"📄 Fix {idx}: {Path(file_path).name} - {issue.get('title', 'Untitled')}", expanded=(idx == 1)):
                    # Show issue context
                    st.caption(f"**Issue Type:** {issue.get('type', 'UNKNOWN')} | **Severity:** {issue.get('severity', 'UNKNOWN')}")

                    # Display syntax-highlighted diff
                    display_syntax_highlighted_diff(
                        file_path,
                        fix.get('original_content', ''),
                        fix.get('fixed_content', '')
                    )

            if len(applied_fixes) > 5:
                st.caption(f"ℹ️ Showing first 5 of {len(applied_fixes)} fixes. Use git diff to see all changes.")

    # Git diff
    if result['diff']:
        st.markdown("### 📝 Git Summary")
        st.markdown(f"**Branch:** `{result['branch_name']}`")
        st.markdown(f"**Commit:** `{result['commit_hash'][:8]}`")

        with st.expander("View Complete Git Diff", expanded=False):
            # Issue #20 fix: Warn user if diff is truncated
            diff_text = result['diff']
            if len(diff_text) > 3000:
                st.warning(f"⚠️ Diff truncated ({len(diff_text)} → 3000 chars). Download full report to see all changes.")
                st.code(diff_text[:3000], language="diff")
            else:
                st.code(diff_text, language="diff")

    # Impact scores
    st.markdown("### 📊 Impact Assessment")

    cols = st.columns(3, gap="small")
    cols[0].metric("Before", f"{result['scores']['before']}/10")
    cols[1].metric("After", f"{result['scores']['after']}/10")
    improvement = result['scores']['improvement']
    delta_color = "normal" if improvement > 0 else "inverse"
    cols[2].metric(
        "Improvement",
        f"+{improvement}" if improvement > 0 else str(improvement),
        delta=f"{abs(improvement)} points",
        delta_color=delta_color
    )

    # Next focus
    st.markdown("### 🎯 Next Focus")
    st.info(result['next_focus'])

    # Action buttons
    st.markdown("### 🎯 Next Steps")

    cols = st.columns(3, gap="small")
    if cols[0].button("✅ Merge to Main", use_container_width=True):
        merge_to_main(result['branch_name'])
    if cols[1].button("🔄 Run Another Cycle", use_container_width=True):
        st.rerun()
    if cols[2].button("🔙 Rollback Changes", use_container_width=True):
        if improver.rollback_to_main():
            st.success("✅ Rolled back to main branch")
        else:
            st.error("❌ Rollback failed")


def display_issue_selection_ui(all_issues: List[Dict[str, Any]], improver: 'SelfImprover') -> Optional[List[Dict[str, Any]]]:
    """
    Display interactive UI for user to select issues to fix

    Returns:
        Selected issues, or None if user chooses auto-selection
    """
    st.markdown("---")
    st.markdown("### 🎯 Select Issues to Fix")

    # Choice buttons
    col1, col2 = st.columns(2)

    with col1:
        manual_mode = st.button(
            "📝 I'll Pick Issues",
            use_container_width=True,
            type="primary",
            help="Review all issues and manually select which to fix"
        )

    with col2:
        auto_mode = st.button(
            "🤖 Let Agents Decide",
            use_container_width=True,
            type="secondary",
            help="Agents will automatically prioritize and fix top 5 issues"
        )

    if manual_mode:
        st.session_state['selection_mode'] = 'manual'
    elif auto_mode:
        st.session_state['selection_mode'] = 'auto'

    # Show selection UI if manual mode
    if st.session_state.get('selection_mode') == 'manual':
        st.markdown("#### Select Issues to Fix")
        st.info("💡 **Tip:** Start with HIGH severity bugs for maximum impact")

        # Group by type and severity
        bugs_high = [i for i in all_issues if i.get('type') == 'BUG' and i.get('severity') == 'HIGH']
        bugs_medium = [i for i in all_issues if i.get('type') == 'BUG' and i.get('severity') == 'MEDIUM']
        bugs_low = [i for i in all_issues if i.get('type') == 'BUG' and i.get('severity') == 'LOW']
        enh_high = [i for i in all_issues if i.get('type') == 'ENHANCEMENT' and i.get('severity') == 'HIGH']
        enh_medium = [i for i in all_issues if i.get('type') == 'ENHANCEMENT' and i.get('severity') == 'MEDIUM']
        enh_low = [i for i in all_issues if i.get('type') == 'ENHANCEMENT' and i.get('severity') == 'LOW']

        selected_issues = []

        # Tabs for better organization
        tab1, tab2 = st.tabs(["🐛 Bugs", "💡 Enhancements"])

        with tab1:
            # HIGH priority bugs
            if bugs_high:
                st.markdown("##### 🔴 HIGH Priority")
                for idx, issue in enumerate(bugs_high):
                    key = f"bug_high_{idx}"
                    selected = st.checkbox(
                        f"{issue.get('title', 'Untitled')} - `{issue.get('file', 'unknown')}`",
                        key=key,
                        help=issue.get('description', 'No description')
                    )
                    if selected:
                        selected_issues.append(issue)

            # MEDIUM priority bugs
            if bugs_medium:
                st.markdown("##### 🟡 MEDIUM Priority")
                with st.expander(f"View {len(bugs_medium)} medium priority bugs"):
                    for idx, issue in enumerate(bugs_medium):
                        key = f"bug_medium_{idx}"
                        selected = st.checkbox(
                            f"{issue.get('title', 'Untitled')} - `{issue.get('file', 'unknown')}`",
                            key=key,
                            help=issue.get('description', 'No description')
                        )
                        if selected:
                            selected_issues.append(issue)

            # LOW priority bugs
            if bugs_low:
                st.markdown("##### 🟢 LOW Priority")
                with st.expander(f"View {len(bugs_low)} low priority bugs"):
                    for idx, issue in enumerate(bugs_low):
                        key = f"bug_low_{idx}"
                        selected = st.checkbox(
                            f"{issue.get('title', 'Untitled')} - `{issue.get('file', 'unknown')}`",
                            key=key,
                            help=issue.get('description', 'No description')
                        )
                        if selected:
                            selected_issues.append(issue)

        with tab2:
            # HIGH priority enhancements
            if enh_high:
                st.markdown("##### 🔴 HIGH Priority")
                for idx, issue in enumerate(enh_high):
                    key = f"enh_high_{idx}"
                    selected = st.checkbox(
                        f"{issue.get('title', 'Untitled')} - `{issue.get('file', 'unknown')}`",
                        key=key,
                        help=issue.get('description', 'No description')
                    )
                    if selected:
                        selected_issues.append(issue)

            # MEDIUM priority enhancements
            if enh_medium:
                st.markdown("##### 🟡 MEDIUM Priority")
                with st.expander(f"View {len(enh_medium)} medium priority enhancements"):
                    for idx, issue in enumerate(enh_medium):
                        key = f"enh_medium_{idx}"
                        selected = st.checkbox(
                            f"{issue.get('title', 'Untitled')} - `{issue.get('file', 'unknown')}`",
                            key=key,
                            help=issue.get('description', 'No description')
                        )
                        if selected:
                            selected_issues.append(issue)

            # LOW priority enhancements
            if enh_low:
                st.markdown("##### 🟢 LOW Priority")
                with st.expander(f"View {len(enh_low)} low priority enhancements"):
                    for idx, issue in enumerate(enh_low):
                        key = f"enh_low_{idx}"
                        selected = st.checkbox(
                            f"{issue.get('title', 'Untitled')} - `{issue.get('file', 'unknown')}`",
                            key=key,
                            help=issue.get('description', 'No description')
                        )
                        if selected:
                            selected_issues.append(issue)

        # Show selection summary and action button
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"✅ **{len(selected_issues)} issues selected**")
        with col2:
            if st.button("🔧 Fix Selected", use_container_width=True, type="primary", disabled=len(selected_issues) == 0):
                return selected_issues

    elif st.session_state.get('selection_mode') == 'auto':
        st.success("✅ **Auto mode**: Agents will prioritize and fix top 5 issues")
        return None  # None = auto mode

    return []  # Empty list = no selection yet


def merge_to_main(branch_name: str) -> None:
    """Merge improvement branch to main"""
    import subprocess
    import re
    from core.config import load_config

    try:
        # CRITICAL FIX (Issue #1): Validate branch name for command injection protection
        if not re.match(r'^[a-zA-Z0-9_/-]+$', branch_name):
            st.error("❌ Invalid branch name format")
            return

        # Get base directory from config
        config = load_config()
        base_dir = Path(config.get('base_dir', '.'))

        # Validate base directory
        if not base_dir.exists() or not base_dir.is_dir():
            st.error("❌ Invalid base directory configuration")
            return

        # Switch to main with proper error handling
        subprocess.run(
            ['git', 'checkout', 'main'],
            cwd=str(base_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Merge branch with proper error handling
        subprocess.run(
            ['git', 'merge', branch_name],
            cwd=str(base_dir),
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        st.success(f"✅ Merged {branch_name} to main!")

    except subprocess.TimeoutExpired:
        st.error("❌ Git operation timed out (30s)")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        st.error(f"❌ Merge failed: {error_msg}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")