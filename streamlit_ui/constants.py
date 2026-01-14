"""
Centralized constants for Streamlit UI
Defines colors, spacing, sizes, and thresholds used across UI components
"""

# Color Palette
COLORS = {
    # Terminal & Background
    "terminal_bg": "#1a1d29",
    "component_bg": "#333333",
    "text_primary": "#ffffff",
    "text_secondary": "#888888",

    # Status Colors (consistent across all components)
    "success": "#44ff44",
    "info": "#00ff00",
    "warning": "#ffff00",
    "error": "#ff4444",
    "system": "#00aaff",

    # Test Results
    "test_passed": "#44ff44",
    "test_failed": "#ff4444",
    "test_skipped": "#888888",
    "test_warning": "#ffaa44",

    # Severity Levels (for issues/bugs)
    "severity_high": "#ff4444",
    "severity_medium": "#ffaa44",
    "severity_low": "#44ff44",
}

# Typography & Spacing
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "xxl": "2.5rem",
}

# Component Dimensions
DIMENSIONS = {
    "terminal_height": "400px",
    "progress_bar_height": "1.5rem",
    "button_height": "2.5rem",
    "border_radius": "0.5rem",
    "border_radius_lg": "0.8rem",
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