"""
Weaver Pro Report Themes
========================

Visual themes for audit reports. Each theme provides a complete CSS color scheme
and styling that transforms the look and feel of the report.

Available Themes:
- original: Professional red/orange gradient (default)
- cyberpunk: Neon pink/cyan on dark with glitch effects
- jetsons: Retro-futuristic with rounded shapes and space-age colors
- matrix: Green digital rain aesthetic with terminal styling
- synthwave: 80s neon sunset vibes with purple/pink gradients
- minimal: Clean, modern with lots of whitespace
- corporate: Traditional business blue with conservative styling
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Theme:
    """Theme configuration for audit reports"""
    name: str
    display_name: str
    description: str

    # Core colors
    primary: str
    primary_light: str
    secondary: str
    accent: str

    # Background colors
    dark: str
    dark_secondary: str
    light: str

    # Text colors
    text: str
    text_light: str

    # Status colors
    success: str
    warning: str
    danger: str
    info: str

    # Fonts
    heading_font: str
    body_font: str
    mono_font: str

    # Special effects (CSS)
    special_effects: str = ""

    # Cover background override
    cover_background: str = ""

    # Card styling
    card_background: str = ""
    card_border: str = ""
    card_shadow: str = ""

    # Button styling
    button_radius: str = "30px"

    def get_css_variables(self) -> str:
        """Generate CSS custom properties for this theme"""
        return f"""
        :root {{
            --primary: {self.primary};
            --primary-light: {self.primary_light};
            --secondary: {self.secondary};
            --accent: {self.accent};
            --dark: {self.dark};
            --dark-secondary: {self.dark_secondary};
            --light: {self.light};
            --text: {self.text};
            --text-light: {self.text_light};
            --success: {self.success};
            --warning: {self.warning};
            --danger: {self.danger};
            --info: {self.info};
            --heading-font: {self.heading_font};
            --body-font: {self.body_font};
            --mono-font: {self.mono_font};
            --button-radius: {self.button_radius};
        }}
        """


# =============================================================================
# THEME DEFINITIONS
# =============================================================================

THEME_ORIGINAL = Theme(
    name="original",
    display_name="Original",
    description="Professional red/orange gradient - the classic Weaver Pro look",

    primary="#EF4444",
    primary_light="#FCA5A5",
    secondary="#F97316",
    accent="#10B981",

    dark="#0F172A",
    dark_secondary="#1E293B",
    light="#F8FAFC",

    text="#334155",
    text_light="#64748B",

    success="#10B981",
    warning="#F59E0B",
    danger="#EF4444",
    info="#3B82F6",

    heading_font="'Playfair Display', serif",
    body_font="'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    mono_font="'JetBrains Mono', monospace",
)


THEME_CYBERPUNK = Theme(
    name="cyberpunk",
    display_name="Cyberpunk 2077",
    description="Neon-soaked night city vibes with glitch effects",

    primary="#FF00FF",  # Magenta
    primary_light="#FF66FF",
    secondary="#00FFFF",  # Cyan
    accent="#FFFF00",  # Yellow

    dark="#0a0a0f",
    dark_secondary="#12121a",
    light="#1a1a2e",

    text="#e0e0e0",
    text_light="#a0a0a0",

    success="#00FF9F",
    warning="#FFD700",
    danger="#FF0055",
    info="#00BFFF",

    heading_font="'Orbitron', 'Rajdhani', sans-serif",
    body_font="'Rajdhani', 'Share Tech', sans-serif",
    mono_font="'Share Tech Mono', 'Fira Code', monospace",

    button_radius="0px 12px 0px 12px",

    special_effects="""
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

        /* Glitch effect on headings */
        @keyframes glitch {
            0% { text-shadow: 2px 0 #FF00FF, -2px 0 #00FFFF; }
            25% { text-shadow: -2px 0 #FF00FF, 2px 0 #00FFFF; }
            50% { text-shadow: 2px 2px #FF00FF, -2px -2px #00FFFF; }
            75% { text-shadow: -2px 2px #FF00FF, 2px -2px #00FFFF; }
            100% { text-shadow: 2px 0 #FF00FF, -2px 0 #00FFFF; }
        }

        .cover h1 {
            animation: glitch 3s infinite;
            text-transform: uppercase;
            letter-spacing: 4px;
        }

        /* Scanline effect */
        .cover::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                rgba(0,0,0,0.1) 0px,
                rgba(0,0,0,0.1) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 2;
        }

        /* Neon glow on cards */
        .section {
            border: 1px solid rgba(255, 0, 255, 0.3);
            box-shadow: 0 0 20px rgba(255, 0, 255, 0.1), inset 0 0 20px rgba(0, 255, 255, 0.05);
        }

        /* Cyber grid background */
        body {
            background-image:
                linear-gradient(rgba(255, 0, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 0, 255, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
        }

        /* Accent borders */
        .cover-stat {
            border: 1px solid rgba(0, 255, 255, 0.5);
            background: rgba(0, 255, 255, 0.05);
        }

        .section-icon {
            border: 2px solid currentColor;
            box-shadow: 0 0 10px currentColor;
        }
    """,

    cover_background="""
        background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a1a2e 100%);
        background-image:
            linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a1a2e 100%),
            url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23FF00FF' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    """,

    card_background="rgba(26, 26, 46, 0.8)",
    card_border="1px solid rgba(255, 0, 255, 0.2)",
    card_shadow="0 0 30px rgba(255, 0, 255, 0.1)",
)


THEME_JETSONS = Theme(
    name="jetsons",
    display_name="Jetsons",
    description="Retro-futuristic space age with atomic-era styling",

    primary="#FF6B6B",  # Coral
    primary_light="#FFA5A5",
    secondary="#4ECDC4",  # Teal
    accent="#FFE66D",  # Yellow

    dark="#2C3E50",
    dark_secondary="#34495E",
    light="#ECF0F1",

    text="#2C3E50",
    text_light="#7F8C8D",

    success="#2ECC71",
    warning="#F39C12",
    danger="#E74C3C",
    info="#3498DB",

    heading_font="'Quicksand', 'Comfortaa', sans-serif",
    body_font="'Nunito', 'Quicksand', sans-serif",
    mono_font="'Space Mono', monospace",

    button_radius="50px",

    special_effects="""
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Nunito:wght@400;500;600;700&family=Space+Mono:wght@400;700&family=Comfortaa:wght@400;500;600;700&display=swap');

        /* Atomic-era styling */
        .section {
            border-radius: 30px;
            border: 3px solid #4ECDC4;
        }

        .cover-stat {
            border-radius: 50%;
            width: 140px;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border: 3px solid rgba(255, 255, 255, 0.3);
        }

        /* Bubble/orbit decorations */
        .cover::before {
            content: '';
            position: absolute;
            top: 10%;
            right: 10%;
            width: 200px;
            height: 200px;
            border: 3px solid rgba(78, 205, 196, 0.3);
            border-radius: 50%;
        }

        .cover::after {
            content: '';
            position: absolute;
            bottom: 20%;
            left: 5%;
            width: 150px;
            height: 150px;
            border: 3px solid rgba(255, 107, 107, 0.3);
            border-radius: 50%;
        }

        /* Floating animation */
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .section-icon {
            animation: float 3s ease-in-out infinite;
            border-radius: 50%;
        }

        /* Space-age gradients */
        .cover-badge {
            background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
            border-radius: 50px;
        }

        /* Rounded everything */
        .metrics-table, .issues-grid, .heuristics-grid {
            border-radius: 20px;
            overflow: hidden;
        }

        /* Playful shadows */
        .section {
            box-shadow: 8px 8px 0 rgba(78, 205, 196, 0.3);
        }
    """,

    cover_background="""
        background: linear-gradient(135deg, #2C3E50 0%, #4A6572 50%, #2C3E50 100%);
    """,

    card_background="#ffffff",
    card_border="3px solid #4ECDC4",
    card_shadow="8px 8px 0 rgba(78, 205, 196, 0.2)",
)


THEME_MATRIX = Theme(
    name="matrix",
    display_name="Matrix",
    description="Digital rain and terminal aesthetics - take the red pill",

    primary="#00FF41",  # Matrix green
    primary_light="#39FF14",
    secondary="#008F11",
    accent="#00FF41",

    dark="#0D0D0D",
    dark_secondary="#0a0a0a",
    light="#0D0D0D",

    text="#00FF41",
    text_light="#008F11",

    success="#00FF41",
    warning="#FFFF00",
    danger="#FF0000",
    info="#00FF41",

    heading_font="'Share Tech Mono', 'Courier New', monospace",
    body_font="'Share Tech Mono', 'Courier New', monospace",
    mono_font="'Share Tech Mono', 'Courier New', monospace",

    button_radius="0",

    special_effects="""
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

        /* Everything is monospace in the Matrix */
        * {
            font-family: 'Share Tech Mono', 'Courier New', monospace !important;
        }

        /* Digital rain effect on cover */
        .cover {
            position: relative;
            overflow: hidden;
        }

        .cover::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='100'%3E%3Ctext x='0' y='20' fill='%2300FF41' opacity='0.1' font-family='monospace' font-size='14'%3E1%3C/text%3E%3Ctext x='0' y='40' fill='%2300FF41' opacity='0.15' font-family='monospace' font-size='14'%3E0%3C/text%3E%3Ctext x='0' y='60' fill='%2300FF41' opacity='0.1' font-family='monospace' font-size='14'%3E1%3C/text%3E%3Ctext x='0' y='80' fill='%2300FF41' opacity='0.2' font-family='monospace' font-size='14'%3E0%3C/text%3E%3C/svg%3E");
            animation: rain 20s linear infinite;
            pointer-events: none;
            z-index: 0;
        }

        @keyframes rain {
            0% { background-position: 0 0; }
            100% { background-position: 0 1000px; }
        }

        /* Terminal-style cards */
        .section {
            background: #0D0D0D;
            border: 1px solid #00FF41;
            border-radius: 0;
            position: relative;
        }

        .section::before {
            content: '> ';
            position: absolute;
            top: 10px;
            left: 10px;
            color: #00FF41;
            font-size: 14px;
        }

        /* Blinking cursor effect */
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }

        .cover h1::after {
            content: '_';
            animation: blink 1s infinite;
        }

        /* Green glow on everything */
        .section-icon {
            box-shadow: 0 0 10px #00FF41, 0 0 20px #00FF41;
            border: 1px solid #00FF41;
            border-radius: 0;
        }

        /* Scanlines */
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                rgba(0, 255, 65, 0.03) 0px,
                rgba(0, 255, 65, 0.03) 1px,
                transparent 1px,
                transparent 2px
            );
            pointer-events: none;
            z-index: 9999;
        }

        /* Table styling */
        table {
            border: 1px solid #00FF41;
        }

        th, td {
            border: 1px solid #008F11;
        }

        /* Cover stats */
        .cover-stat {
            border: 1px solid #00FF41;
            background: transparent;
        }

        /* Text shadow glow */
        h1, h2, h3, .cover-stat-value {
            text-shadow: 0 0 10px #00FF41;
        }
    """,

    cover_background="""
        background: #0D0D0D;
    """,

    card_background="#0D0D0D",
    card_border="1px solid #00FF41",
    card_shadow="0 0 20px rgba(0, 255, 65, 0.2)",
)


THEME_SYNTHWAVE = Theme(
    name="synthwave",
    display_name="Synthwave",
    description="80s neon sunset with retro-futuristic vibes",

    primary="#F72585",  # Hot pink
    primary_light="#FF69B4",
    secondary="#7209B7",  # Purple
    accent="#4CC9F0",  # Cyan

    dark="#10002B",
    dark_secondary="#240046",
    light="#3C096C",

    text="#F8F8F8",
    text_light="#B8B8D1",

    success="#4CC9F0",
    warning="#FFBE0B",
    danger="#F72585",
    info="#7209B7",

    heading_font="'Audiowide', 'Orbitron', sans-serif",
    body_font="'Exo 2', 'Roboto', sans-serif",
    mono_font="'VT323', 'Courier New', monospace",

    button_radius="0 20px 0 20px",

    special_effects="""
        @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Exo+2:wght@400;500;600;700&family=VT323&display=swap');

        /* Sunset gradient background */
        .cover {
            background: linear-gradient(
                180deg,
                #10002B 0%,
                #240046 20%,
                #3C096C 40%,
                #5A189A 55%,
                #7209B7 65%,
                #9D4EDD 75%,
                #E040FB 85%,
                #F72585 95%,
                #FF0A54 100%
            );
        }

        /* Grid floor effect */
        .cover::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40%;
            background:
                linear-gradient(transparent 0%, rgba(16, 0, 43, 0.8) 100%),
                repeating-linear-gradient(
                    90deg,
                    rgba(247, 37, 133, 0.3) 0px,
                    rgba(247, 37, 133, 0.3) 1px,
                    transparent 1px,
                    transparent 60px
                ),
                repeating-linear-gradient(
                    0deg,
                    rgba(247, 37, 133, 0.3) 0px,
                    rgba(247, 37, 133, 0.3) 1px,
                    transparent 1px,
                    transparent 30px
                );
            transform: perspective(500px) rotateX(60deg);
            transform-origin: bottom;
        }

        /* Neon glow text */
        .cover h1 {
            text-shadow:
                0 0 10px #F72585,
                0 0 20px #F72585,
                0 0 40px #F72585,
                0 0 80px #7209B7;
        }

        /* Chrome text effect */
        .cover h1 span {
            background: linear-gradient(
                180deg,
                #fff 0%,
                #F72585 50%,
                #7209B7 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Glowing borders */
        .section {
            border: 2px solid transparent;
            background: linear-gradient(#10002B, #10002B) padding-box,
                        linear-gradient(135deg, #F72585, #7209B7, #4CC9F0) border-box;
            border-radius: 10px;
        }

        .section-icon {
            box-shadow:
                0 0 10px currentColor,
                0 0 20px currentColor;
        }

        /* Animated glow pulse */
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 20px rgba(247, 37, 133, 0.5); }
            50% { box-shadow: 0 0 40px rgba(247, 37, 133, 0.8), 0 0 60px rgba(114, 9, 183, 0.5); }
        }

        .cover-stat {
            animation: pulse 2s ease-in-out infinite;
            border: 1px solid rgba(247, 37, 133, 0.5);
        }

        /* Sun behind grid */
        .cover::before {
            content: '';
            position: absolute;
            bottom: 30%;
            left: 50%;
            transform: translateX(-50%);
            width: 300px;
            height: 300px;
            background: linear-gradient(
                180deg,
                #FFBE0B 0%,
                #F72585 50%,
                transparent 100%
            );
            border-radius: 50%;
            filter: blur(2px);
            z-index: 0;
        }
    """,

    cover_background="",  # Handled in special_effects

    card_background="rgba(16, 0, 43, 0.9)",
    card_border="2px solid rgba(247, 37, 133, 0.5)",
    card_shadow="0 0 30px rgba(247, 37, 133, 0.3)",
)


THEME_MINIMAL = Theme(
    name="minimal",
    display_name="Minimal",
    description="Clean, modern design with lots of whitespace",

    primary="#000000",
    primary_light="#333333",
    secondary="#666666",
    accent="#000000",

    dark="#000000",
    dark_secondary="#1a1a1a",
    light="#FFFFFF",

    text="#1a1a1a",
    text_light="#666666",

    success="#22C55E",
    warning="#EAB308",
    danger="#EF4444",
    info="#3B82F6",

    heading_font="'DM Sans', 'Helvetica Neue', sans-serif",
    body_font="'DM Sans', 'Helvetica Neue', sans-serif",
    mono_font="'DM Mono', 'SF Mono', monospace",

    button_radius="8px",

    special_effects="""
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

        /* Ultra-clean styling */
        .section {
            border: 1px solid #e5e5e5;
            box-shadow: none;
            border-radius: 8px;
        }

        .cover {
            background: #000000;
        }

        .cover h1 {
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .cover h1 span {
            background: none;
            -webkit-text-fill-color: #ffffff;
            color: #ffffff;
        }

        /* Simple underline accents */
        h2 {
            border-bottom: 2px solid #000000;
            padding-bottom: 8px;
            display: inline-block;
        }

        /* Minimal icons */
        .section-icon {
            background: transparent !important;
            border: 2px solid currentColor;
        }

        /* Clean tables */
        table {
            border-collapse: collapse;
        }

        th {
            background: #f5f5f5;
            font-weight: 600;
        }

        td, th {
            border-bottom: 1px solid #e5e5e5;
            border-left: none;
            border-right: none;
        }

        /* Subtle hover states */
        .section:hover {
            border-color: #000000;
        }

        /* No gradients */
        .cover-badge {
            background: #000000;
            border-radius: 4px;
        }

        .cover-stat {
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
        }
    """,

    cover_background="background: #000000;",

    card_background="#ffffff",
    card_border="1px solid #e5e5e5",
    card_shadow="none",
)


THEME_CORPORATE = Theme(
    name="corporate",
    display_name="Corporate",
    description="Traditional business styling with conservative colors",

    primary="#1E40AF",  # Navy blue
    primary_light="#3B82F6",
    secondary="#0F766E",  # Teal
    accent="#1E40AF",

    dark="#1E3A5F",
    dark_secondary="#2C4A6E",
    light="#F5F7FA",

    text="#1F2937",
    text_light="#6B7280",

    success="#059669",
    warning="#D97706",
    danger="#DC2626",
    info="#2563EB",

    heading_font="'Merriweather', 'Georgia', serif",
    body_font="'Source Sans Pro', 'Arial', sans-serif",
    mono_font="'Source Code Pro', monospace",

    button_radius="4px",

    special_effects="""
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Source+Sans+Pro:wght@400;600;700&family=Source+Code+Pro:wght@400;500&display=swap');

        /* Conservative, trustworthy styling */
        .section {
            border: 1px solid #D1D5DB;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .cover {
            background: linear-gradient(135deg, #1E3A5F 0%, #2C4A6E 100%);
        }

        /* Traditional serif headings */
        .cover h1 {
            font-family: 'Merriweather', Georgia, serif;
            font-weight: 700;
        }

        .cover h1 span {
            background: none;
            -webkit-text-fill-color: #ffffff;
            color: #ffffff;
        }

        /* Professional badges */
        .cover-badge {
            background: #1E40AF;
            border-radius: 4px;
        }

        /* Structured tables */
        table {
            border: 1px solid #D1D5DB;
        }

        th {
            background: #1E40AF;
            color: white;
        }

        /* Subtle section icons */
        .section-icon {
            border-radius: 4px;
        }

        /* Footer styling */
        .footer {
            background: #1E3A5F;
        }

        /* Conservative stat boxes */
        .cover-stat {
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 4px;
        }
    """,

    cover_background="background: linear-gradient(135deg, #1E3A5F 0%, #2C4A6E 100%);",

    card_background="#ffffff",
    card_border="1px solid #D1D5DB",
    card_shadow="0 1px 3px rgba(0,0,0,0.1)",
)


# =============================================================================
# THEME REGISTRY
# =============================================================================

THEMES: Dict[str, Theme] = {
    "original": THEME_ORIGINAL,
    "cyberpunk": THEME_CYBERPUNK,
    "jetsons": THEME_JETSONS,
    "matrix": THEME_MATRIX,
    "synthwave": THEME_SYNTHWAVE,
    "minimal": THEME_MINIMAL,
    "corporate": THEME_CORPORATE,
}


def get_theme(name: str) -> Theme:
    """Get a theme by name, defaults to original if not found"""
    return THEMES.get(name.lower(), THEME_ORIGINAL)


def list_themes() -> list:
    """List all available themes"""
    return [
        {
            "name": t.name,
            "display_name": t.display_name,
            "description": t.description
        }
        for t in THEMES.values()
    ]


def get_theme_css(theme_name: str) -> str:
    """Get complete CSS for a theme including variables and special effects"""
    theme = get_theme(theme_name)
    return theme.get_css_variables() + "\n" + theme.special_effects


# =============================================================================
# THEME PREVIEW GENERATOR
# =============================================================================

def generate_theme_preview_html() -> str:
    """Generate an HTML page showing all themes"""
    previews = []

    for theme in THEMES.values():
        previews.append(f"""
        <div class="theme-preview" style="
            background: {theme.dark};
            color: {theme.text if theme.name != 'minimal' else '#fff'};
            padding: 30px;
            border-radius: 12px;
            margin: 20px 0;
        ">
            <h3 style="color: {theme.primary}; margin-bottom: 10px;">{theme.display_name}</h3>
            <p style="color: {theme.text_light}; margin-bottom: 20px;">{theme.description}</p>
            <div style="display: flex; gap: 10px;">
                <div style="width: 40px; height: 40px; background: {theme.primary}; border-radius: 8px;" title="Primary"></div>
                <div style="width: 40px; height: 40px; background: {theme.secondary}; border-radius: 8px;" title="Secondary"></div>
                <div style="width: 40px; height: 40px; background: {theme.accent}; border-radius: 8px;" title="Accent"></div>
                <div style="width: 40px; height: 40px; background: {theme.success}; border-radius: 8px;" title="Success"></div>
                <div style="width: 40px; height: 40px; background: {theme.warning}; border-radius: 8px;" title="Warning"></div>
                <div style="width: 40px; height: 40px; background: {theme.danger}; border-radius: 8px;" title="Danger"></div>
            </div>
        </div>
        """)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Weaver Pro Themes</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
                background: #f5f5f5;
            }}
            h1 {{
                text-align: center;
                margin-bottom: 40px;
            }}
        </style>
    </head>
    <body>
        <h1>Weaver Pro Themes</h1>
        {''.join(previews)}
    </body>
    </html>
    """


if __name__ == "__main__":
    # Generate theme preview
    preview_html = generate_theme_preview_html()
    with open("THEME_PREVIEW.html", "w", encoding="utf-8") as f:
        f.write(preview_html)
    print("Theme preview saved to THEME_PREVIEW.html")

    # List themes
    print("\nAvailable themes:")
    for theme_info in list_themes():
        print(f"  - {theme_info['name']}: {theme_info['description']}")
