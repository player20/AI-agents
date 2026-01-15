"""
Centralized UI constants for Code Weaver Pro
Defines colors, spacing, sizes, and thresholds used across UI components
"""

# UI Color Palette
UI_COLORS = {
    # Terminal & Background
    "terminal_bg": "#1a1d29",
    "component_bg": "#333333",
    "text_primary": "#ffffff",
    "text_secondary": "#d9d9d9",  # Adjusted to have higher contrast ratio (4.5:1)

    # Status Colors (consistent across all components)
    "status_success": "#44ff44",
    "status_info": "#00ff00",
    "status_warning": "#ffff00",
    "status_error": "#ff4444",
    "status_system": "#00aaff",

    # Test Results
    "test_passed": "#44ff44",
    "test_failed": "#ff4444",
    "test_skipped": "#d9d9d9",
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
    "button_height": "3rem",  # Increased button height to 3rem
    "button_font_size": "1rem",  # Increased button font size to 1rem
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

# Backward compatibility aliases
COLORS = UI_COLORS  # Alias for backward compatibility