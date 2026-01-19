"""
Centralized UI constants for Weaver Pro
Defines colors, spacing, sizes, and thresholds used across UI components
Aligned with design-tokens.json for cross-platform consistency
"""

# Unified Font Family (matches design tokens)
FONT_FAMILY = {
    "sans": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "mono": "'JetBrains Mono', 'SF Mono', Monaco, 'Cascadia Code', monospace",
}

# UI Color Palette - Dark Mode (default for Streamlit terminal style)
UI_COLORS = {
    # Terminal & Background
    "terminal_bg": "#0a0a0a",
    "component_bg": "#171717",
    "card_bg": "#1f1f1f",
    "surface_bg": "#141414",
    "overlay_bg": "rgba(0, 0, 0, 0.6)",
    "text_primary": "#fafafa",
    "text_secondary": "#a3a3a3",  # WCAG AA compliant (4.5:1+ contrast ratio)
    "text_muted": "#737373",      # WCAG AA compliant (4.5:1 ratio on dark bg)
    "placeholder": "#a3a3a3",    # WCAG AA compliant

    # Focus & Interactive States (enhanced for visibility)
    "focus_ring": "#667eea",     # Brand primary for focus
    "focus_glow": "rgba(102, 126, 234, 0.4)",
    "hover_bg": "rgba(102, 126, 234, 0.1)",
    "active_bg": "rgba(102, 126, 234, 0.2)",

    # Primary & Accent Colors (unified brand)
    "primary": "#667eea",
    "primary_hover": "#5a6fd6",
    "primary_light": "rgba(102, 126, 234, 0.15)",
    "secondary": "#764ba2",
    "secondary_hover": "#6a4190",
    "accent": "#10b981",
    "accent_hover": "#059669",

    # Gradient Colors
    "gradient_start": "#667eea",
    "gradient_end": "#764ba2",

    # Button Colors (using brand gradient for primary)
    "button_primary_bg": "#667eea",
    "button_primary_hover": "#5a6fd6",
    "button_secondary_bg": "#262626",
    "button_secondary_hover": "#404040",
    "button_success_bg": "#10b981",
    "button_success_hover": "#059669",
    "button_danger_bg": "#ef4444",
    "button_danger_hover": "#dc2626",

    # Border Colors
    "border_default": "rgba(255, 255, 255, 0.12)",
    "border_focus": "#667eea",
    "border_error": "#ef4444",
    "border_success": "#10b981",
    "border_warning": "#f59e0b",

    # Status Colors (professional, accessible)
    "status_success": "#10b981",
    "status_info": "#3b82f6",
    "status_warning": "#f59e0b",
    "status_error": "#ef4444",
    "status_system": "#667eea",

    # Test Results
    "test_passed": "#10b981",
    "test_failed": "#ef4444",
    "test_skipped": "#737373",
    "test_warning": "#f59e0b",

    # Severity Levels (for issues/bugs)
    "severity_high": "#ef4444",
    "severity_medium": "#f59e0b",
    "severity_low": "#10b981",

    # Link Colors
    "link": "#667eea",
    "link_hover": "#8b9eff",
    "link_visited": "#764ba2",
}

# Light Mode Colors (for optional light theme support)
UI_COLORS_LIGHT = {
    "terminal_bg": "#ffffff",
    "component_bg": "#fafafa",
    "card_bg": "#ffffff",
    "surface_bg": "#f5f5f5",
    "text_primary": "#171717",
    "text_secondary": "#525252",
    "text_muted": "#737373",
    "border_default": "#e5e5e5",
}

# Typography & Spacing (Issue #6 - Consistent spacing system)
SPACING = {
    "xs": "4px",      # 0.25rem
    "sm": "8px",      # 0.5rem
    "md": "16px",     # 1rem - base unit
    "lg": "24px",     # 1.5rem
    "xl": "40px",     # 2.5rem
    "xxl": "56px",    # 3.5rem
}

# CSS Spacing Variables (for use in st.markdown CSS blocks)
SPACING_CSS_VARS = """
:root {
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 40px;
    --space-xxl: 56px;
}
"""

# Component Dimensions
DIMENSIONS = {
    "terminal_height": "400px",
    "progress_bar_height": "1.5rem",

    # Button Sizing (Issue #1 - Primary CTA prominence)
    "button_height": "48px",
    "button_height_primary": "56px",  # Larger for primary CTAs
    "button_min_width_primary": "200px",
    "button_font_size": "1rem",
    "button_font_size_primary": "1.25rem",  # 20px for primary CTAs

    # Mobile Touch Targets (Issue #2 - WCAG 2.1 compliance)
    "touch_target_min": "44px",
    "touch_spacing": "20px",

    # Border Radius
    "border_radius": "0.5rem",
    "border_radius_lg": "0.8rem",
    "border_radius_xl": "12px",

    # Container Widths (Issue #10 - Desktop optimization)
    "max_width_desktop": "1200px",
    "max_width_content": "800px",
}

# Thresholds
THRESHOLDS = {
    "page_load_ms_good": 3000,      # < 3s = good load time
    "bundle_size_kb_good": 1024,    # < 1MB = good bundle size
    "max_screenshots": 3,           # Max screenshots to display
    "score_excellent": 9,           # Score >= 9 = excellent
    "score_good": 7,                # Score >= 7 = good
    "score_fair": 5,                # Score >= 5 = fair
}

# Standardized Status Emojis (use consistently across all UI components)
STATUS_EMOJIS = {
    # General Status
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "loading": "⏳",
    "complete": "🎉",

    # Process States
    "running": "🔄",
    "stopped": "🛑",
    "paused": "⏸️",
    "cancelled": "🚫",

    # Scores (color-coded circles)
    "score_excellent": "🟢",  # >= 9
    "score_good": "🟡",       # >= 7
    "score_fair": "🟠",       # >= 5
    "score_poor": "🔴",       # < 5

    # Features
    "feature_enabled": "✅",
    "feature_disabled": "⬜",

    # Actions
    "download": "💾",
    "upload": "📤",
    "delete": "🗑️",
    "edit": "✏️",
    "view": "👁️",
    "settings": "⚙️",
    "help": "❓",
}

# Model Selection Info
MODEL_INFO = {
    "haiku": {"emoji": "⚡", "speed": "~30s", "quality": "Good"},
    "sonnet": {"emoji": "⏱️", "speed": "~60s", "quality": "Better"},
    "opus": {"emoji": "🎯", "speed": "~90s", "quality": "Best"},
}

# Unified Gradient System (Issue #3 - Color scheme unification)
GRADIENTS = {
    # Primary gradients
    "primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "primary_hover": "linear-gradient(135deg, #5a6fd6 0%, #6a4190 100%)",

    # Subtle accent backgrounds
    "accent_subtle": "linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1))",
    "accent_medium": "linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2))",
    "accent_strong": "linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3))",

    # Card/section backgrounds
    "card_bg": "linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08))",
    "section_bg": "linear-gradient(180deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)",

    # Button gradients
    "button_primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "button_success": "linear-gradient(135deg, #10b981 0%, #059669 100%)",

    # Border gradients (for accent borders)
    "border_accent": "linear-gradient(135deg, rgba(102, 126, 234, 0.5), rgba(118, 75, 162, 0.5))",
}

# Typography System (Issue #5 - Typography hierarchy)
TYPOGRAPHY = {
    # Font sizes
    "h1": "2rem",        # 32px
    "h2": "1.5rem",      # 24px
    "h3": "1.25rem",     # 20px
    "h4": "1.125rem",    # 18px
    "body": "1rem",      # 16px (base)
    "small": "0.875rem", # 14px
    "caption": "0.75rem",# 12px

    # Font weights
    "weight_normal": "400",
    "weight_medium": "500",
    "weight_semibold": "600",
    "weight_bold": "700",

    # Line heights
    "line_height_tight": "1.2",
    "line_height_normal": "1.5",
    "line_height_relaxed": "1.6",
}

# CSS Typography Classes (inject with st.markdown)
TYPOGRAPHY_CSS = """
<style>
    /* Typography hierarchy to match onboarding polish */
    h1 { font-size: 2rem !important; font-weight: 700 !important; line-height: 1.2 !important; }
    h2 { font-size: 1.5rem !important; font-weight: 600 !important; line-height: 1.3 !important; }
    h3 { font-size: 1.25rem !important; font-weight: 600 !important; line-height: 1.4 !important; }
    h4 { font-size: 1.125rem !important; font-weight: 500 !important; line-height: 1.4 !important; }
    p, .stMarkdown p { font-size: 1rem !important; line-height: 1.6 !important; }
    .text-secondary { font-size: 0.875rem; color: #B8C4D4; }
    .text-muted { font-size: 0.75rem; color: #94A3B8; }

    /* Mobile typography adjustments */
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.125rem !important; }
    }
</style>
"""

# Unified CSS for main interface polish (matches onboarding quality)
INTERFACE_POLISH_CSS = """
<style>
    /* Gradient accent system matching onboarding */
    .primary-section {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 24px;
    }

    /* Textarea size constraints (Issue #2) */
    .stTextArea textarea {
        max-height: 150px !important;
        min-height: 100px !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    @media (max-width: 768px) {
        .stTextArea textarea {
            max-height: 120px !important;
            min-height: 80px !important;
        }
    }

    /* Mobile touch targets (Issue #4) */
    @media (max-width: 768px) {
        .stButton > button {
            min-height: 44px !important;
            padding: 12px 16px !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            min-height: 44px !important;
            font-size: 16px !important; /* Prevent iOS zoom */
        }
    }

    /* Form section cards (Issue #9) */
    .stExpander {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }
    .stExpander:hover {
        border-color: rgba(102, 126, 234, 0.3) !important;
    }

    /* Professional polish - hover states (Issue #10) */
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transition: all 0.2s ease;
    }

    /* Mode button active states (Issue #8) */
    .mode-btn-active {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2)) !important;
        border-color: #667eea !important;
        position: relative;
    }
    .mode-btn-active::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 3px 3px 0 0;
    }

    /* Card shadows */
    .card-elevated {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease;
    }
    .card-elevated:hover {
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
</style>
"""

# Backward compatibility aliases
COLORS = UI_COLORS  # Alias for backward compatibility