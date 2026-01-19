"""
Design System Generator

AI-powered design system generation for projects including:
- Color palette generation based on industry/brand
- Typography pairing (heading + body fonts)
- Spacing and component tokens
- Export to CSS variables, Tailwind config, or Figma

Leverages industry profiles and LLM for intelligent design decisions.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging
import colorsys
import re

logger = logging.getLogger(__name__)


# ===========================================
# Design System Models
# ===========================================

class ColorFormat(str, Enum):
    """Color format options"""
    HEX = "hex"
    RGB = "rgb"
    HSL = "hsl"


class DesignStyle(str, Enum):
    """Design style preferences"""
    MODERN = "modern"
    CLASSIC = "classic"
    PLAYFUL = "playful"
    MINIMAL = "minimal"
    BOLD = "bold"
    ELEGANT = "elegant"
    TECH = "tech"
    ORGANIC = "organic"


class ColorPalette(BaseModel):
    """Complete color palette for a design system"""
    # Brand colors
    primary: str = Field(description="Primary brand color")
    primary_light: str = Field(description="Lighter shade of primary")
    primary_dark: str = Field(description="Darker shade of primary")

    secondary: str = Field(description="Secondary brand color")
    secondary_light: str = Field(description="Lighter shade of secondary")
    secondary_dark: str = Field(description="Darker shade of secondary")

    accent: str = Field(description="Accent color for highlights")

    # Neutral colors
    neutral_50: str = Field(default="#FAFAFA")
    neutral_100: str = Field(default="#F5F5F5")
    neutral_200: str = Field(default="#E5E5E5")
    neutral_300: str = Field(default="#D4D4D4")
    neutral_400: str = Field(default="#A3A3A3")
    neutral_500: str = Field(default="#737373")
    neutral_600: str = Field(default="#525252")
    neutral_700: str = Field(default="#404040")
    neutral_800: str = Field(default="#262626")
    neutral_900: str = Field(default="#171717")

    # Semantic colors
    success: str = Field(default="#10B981")
    warning: str = Field(default="#F59E0B")
    error: str = Field(default="#EF4444")
    info: str = Field(default="#3B82F6")

    # Background colors
    background: str = Field(default="#FFFFFF")
    surface: str = Field(default="#F8FAFC")
    surface_elevated: str = Field(default="#FFFFFF")

    # Text colors
    text_primary: str = Field(default="#1F2937")
    text_secondary: str = Field(default="#6B7280")
    text_muted: str = Field(default="#9CA3AF")
    text_inverse: str = Field(default="#FFFFFF")


class Typography(BaseModel):
    """Typography system"""
    # Font families
    heading_font: str = Field(description="Font family for headings")
    body_font: str = Field(description="Font family for body text")
    mono_font: str = Field(default="'JetBrains Mono', 'Fira Code', monospace")

    # Font sizes (rem)
    size_xs: str = Field(default="0.75rem")
    size_sm: str = Field(default="0.875rem")
    size_base: str = Field(default="1rem")
    size_lg: str = Field(default="1.125rem")
    size_xl: str = Field(default="1.25rem")
    size_2xl: str = Field(default="1.5rem")
    size_3xl: str = Field(default="1.875rem")
    size_4xl: str = Field(default="2.25rem")
    size_5xl: str = Field(default="3rem")

    # Font weights
    weight_light: int = Field(default=300)
    weight_normal: int = Field(default=400)
    weight_medium: int = Field(default=500)
    weight_semibold: int = Field(default=600)
    weight_bold: int = Field(default=700)

    # Line heights
    line_tight: str = Field(default="1.25")
    line_normal: str = Field(default="1.5")
    line_relaxed: str = Field(default="1.75")

    # Letter spacing
    tracking_tight: str = Field(default="-0.025em")
    tracking_normal: str = Field(default="0")
    tracking_wide: str = Field(default="0.025em")


class Spacing(BaseModel):
    """Spacing scale"""
    unit: str = Field(default="4px", description="Base spacing unit")
    scale: Dict[str, str] = Field(
        default_factory=lambda: {
            "0": "0",
            "1": "0.25rem",
            "2": "0.5rem",
            "3": "0.75rem",
            "4": "1rem",
            "5": "1.25rem",
            "6": "1.5rem",
            "8": "2rem",
            "10": "2.5rem",
            "12": "3rem",
            "16": "4rem",
            "20": "5rem",
            "24": "6rem",
        }
    )


class Borders(BaseModel):
    """Border tokens"""
    radius_none: str = Field(default="0")
    radius_sm: str = Field(default="0.125rem")
    radius_default: str = Field(default="0.25rem")
    radius_md: str = Field(default="0.375rem")
    radius_lg: str = Field(default="0.5rem")
    radius_xl: str = Field(default="0.75rem")
    radius_2xl: str = Field(default="1rem")
    radius_full: str = Field(default="9999px")

    width_thin: str = Field(default="1px")
    width_default: str = Field(default="2px")
    width_thick: str = Field(default="4px")


class Shadows(BaseModel):
    """Shadow tokens"""
    sm: str = Field(default="0 1px 2px 0 rgb(0 0 0 / 0.05)")
    default: str = Field(default="0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)")
    md: str = Field(default="0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)")
    lg: str = Field(default="0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)")
    xl: str = Field(default="0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)")
    inner: str = Field(default="inset 0 2px 4px 0 rgb(0 0 0 / 0.05)")


class DesignSystem(BaseModel):
    """Complete design system"""
    name: str = Field(description="Design system name")
    version: str = Field(default="1.0.0")

    colors: ColorPalette
    typography: Typography
    spacing: Spacing = Field(default_factory=Spacing)
    borders: Borders = Field(default_factory=Borders)
    shadows: Shadows = Field(default_factory=Shadows)

    # Metadata
    industry: Optional[str] = None
    style: Optional[DesignStyle] = None
    description: Optional[str] = None


# ===========================================
# Industry Design Profiles
# ===========================================

INDUSTRY_PROFILES = {
    "technology": {
        "primary": "#3B82F6",
        "secondary": "#6366F1",
        "accent": "#06B6D4",
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "style": DesignStyle.MODERN,
        "radius": "8px",
    },
    "healthcare": {
        "primary": "#0D9488",
        "secondary": "#0891B2",
        "accent": "#10B981",
        "heading_font": "Source Sans Pro, system-ui, sans-serif",
        "body_font": "Source Sans Pro, system-ui, sans-serif",
        "style": DesignStyle.CLASSIC,
        "radius": "12px",
    },
    "finance": {
        "primary": "#1E3A8A",
        "secondary": "#1E40AF",
        "accent": "#0369A1",
        "heading_font": "IBM Plex Sans, system-ui, sans-serif",
        "body_font": "IBM Plex Sans, system-ui, sans-serif",
        "style": DesignStyle.CLASSIC,
        "radius": "4px",
    },
    "ecommerce": {
        "primary": "#7C3AED",
        "secondary": "#8B5CF6",
        "accent": "#EC4899",
        "heading_font": "Poppins, system-ui, sans-serif",
        "body_font": "Open Sans, system-ui, sans-serif",
        "style": DesignStyle.BOLD,
        "radius": "12px",
    },
    "food": {
        "primary": "#EA580C",
        "secondary": "#DC2626",
        "accent": "#FBBF24",
        "heading_font": "Playfair Display, serif",
        "body_font": "Lato, system-ui, sans-serif",
        "style": DesignStyle.ORGANIC,
        "radius": "8px",
    },
    "fitness": {
        "primary": "#DC2626",
        "secondary": "#F97316",
        "accent": "#22C55E",
        "heading_font": "Montserrat, system-ui, sans-serif",
        "body_font": "Roboto, system-ui, sans-serif",
        "style": DesignStyle.BOLD,
        "radius": "8px",
    },
    "education": {
        "primary": "#2563EB",
        "secondary": "#7C3AED",
        "accent": "#10B981",
        "heading_font": "Nunito, system-ui, sans-serif",
        "body_font": "Open Sans, system-ui, sans-serif",
        "style": DesignStyle.PLAYFUL,
        "radius": "16px",
    },
    "travel": {
        "primary": "#0EA5E9",
        "secondary": "#06B6D4",
        "accent": "#F97316",
        "heading_font": "Poppins, system-ui, sans-serif",
        "body_font": "Nunito, system-ui, sans-serif",
        "style": DesignStyle.MODERN,
        "radius": "12px",
    },
    "real_estate": {
        "primary": "#059669",
        "secondary": "#0D9488",
        "accent": "#D97706",
        "heading_font": "Playfair Display, serif",
        "body_font": "Source Sans Pro, system-ui, sans-serif",
        "style": DesignStyle.ELEGANT,
        "radius": "4px",
    },
    "creative": {
        "primary": "#EC4899",
        "secondary": "#8B5CF6",
        "accent": "#FBBF24",
        "heading_font": "Space Grotesk, system-ui, sans-serif",
        "body_font": "DM Sans, system-ui, sans-serif",
        "style": DesignStyle.PLAYFUL,
        "radius": "16px",
    },
    "default": {
        "primary": "#6366F1",
        "secondary": "#8B5CF6",
        "accent": "#EC4899",
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "style": DesignStyle.MODERN,
        "radius": "8px",
    }
}


# Font pairings database
FONT_PAIRINGS = {
    "modern": [
        ("Inter", "Inter"),
        ("Poppins", "Inter"),
        ("DM Sans", "DM Sans"),
        ("Outfit", "Inter"),
    ],
    "classic": [
        ("Playfair Display", "Source Sans Pro"),
        ("Merriweather", "Open Sans"),
        ("Lora", "Roboto"),
        ("Cormorant Garamond", "Montserrat"),
    ],
    "playful": [
        ("Nunito", "Nunito"),
        ("Quicksand", "Open Sans"),
        ("Comfortaa", "Poppins"),
        ("Baloo 2", "Nunito"),
    ],
    "minimal": [
        ("DM Sans", "DM Sans"),
        ("Manrope", "Manrope"),
        ("Space Grotesk", "Space Grotesk"),
        ("Satoshi", "Satoshi"),
    ],
    "bold": [
        ("Montserrat", "Roboto"),
        ("Bebas Neue", "Open Sans"),
        ("Oswald", "Lato"),
        ("Anton", "Roboto"),
    ],
    "elegant": [
        ("Cormorant", "Mulish"),
        ("Playfair Display", "Raleway"),
        ("Libre Baskerville", "Source Sans Pro"),
        ("Crimson Pro", "Work Sans"),
    ],
    "tech": [
        ("JetBrains Mono", "Inter"),
        ("Space Mono", "Work Sans"),
        ("IBM Plex Mono", "IBM Plex Sans"),
        ("Fira Code", "Fira Sans"),
    ],
}


# ===========================================
# Color Utilities
# ===========================================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color"""
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex to HSL"""
    r, g, b = hex_to_rgb(hex_color)
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s * 100, l * 100)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert HSL to hex"""
    h, s, l = h / 360, s / 100, l / 100
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))


def lighten_color(hex_color: str, amount: float = 0.2) -> str:
    """Lighten a color by amount (0-1)"""
    h, s, l = hex_to_hsl(hex_color)
    l = min(100, l + (100 - l) * amount)
    return hsl_to_hex(h, s, l)


def darken_color(hex_color: str, amount: float = 0.2) -> str:
    """Darken a color by amount (0-1)"""
    h, s, l = hex_to_hsl(hex_color)
    l = max(0, l * (1 - amount))
    return hsl_to_hex(h, s, l)


def generate_neutral_palette(base_color: str = "#6B7280") -> Dict[str, str]:
    """Generate a neutral color palette"""
    h, s, _ = hex_to_hsl(base_color)
    # Reduce saturation for neutrals
    s = min(s, 10)

    return {
        "50": hsl_to_hex(h, s, 98),
        "100": hsl_to_hex(h, s, 96),
        "200": hsl_to_hex(h, s, 90),
        "300": hsl_to_hex(h, s, 83),
        "400": hsl_to_hex(h, s, 64),
        "500": hsl_to_hex(h, s, 45),
        "600": hsl_to_hex(h, s, 32),
        "700": hsl_to_hex(h, s, 25),
        "800": hsl_to_hex(h, s, 15),
        "900": hsl_to_hex(h, s, 9),
    }


def get_complementary_color(hex_color: str) -> str:
    """Get complementary color (opposite on color wheel)"""
    h, s, l = hex_to_hsl(hex_color)
    h = (h + 180) % 360
    return hsl_to_hex(h, s, l)


def get_analogous_colors(hex_color: str, angle: float = 30) -> Tuple[str, str]:
    """Get analogous colors (adjacent on color wheel)"""
    h, s, l = hex_to_hsl(hex_color)
    color1 = hsl_to_hex((h - angle) % 360, s, l)
    color2 = hsl_to_hex((h + angle) % 360, s, l)
    return (color1, color2)


def get_triadic_colors(hex_color: str) -> Tuple[str, str]:
    """Get triadic colors (120 degrees apart)"""
    h, s, l = hex_to_hsl(hex_color)
    color1 = hsl_to_hex((h + 120) % 360, s, l)
    color2 = hsl_to_hex((h + 240) % 360, s, l)
    return (color1, color2)


# ===========================================
# Design Generator
# ===========================================

class DesignGenerator:
    """Generate complete design systems"""

    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai

    async def generate(
        self,
        business_idea: str,
        industry: Optional[str] = None,
        style: Optional[DesignStyle] = None,
        primary_color: Optional[str] = None,
    ) -> DesignSystem:
        """
        Generate a complete design system.

        Args:
            business_idea: Description of the business/project
            industry: Industry type (technology, healthcare, etc.)
            style: Design style preference
            primary_color: Optional specific primary color to use

        Returns:
            Complete DesignSystem
        """
        # Detect industry from business idea if not provided
        if not industry:
            industry = self._detect_industry(business_idea)

        # Get industry profile
        profile = INDUSTRY_PROFILES.get(industry, INDUSTRY_PROFILES["default"])

        # Use provided style or profile default
        design_style = style or profile["style"]

        # Generate color palette
        colors = self._generate_color_palette(
            primary=primary_color or profile["primary"],
            secondary=profile["secondary"],
            accent=profile["accent"],
            style=design_style,
        )

        # Generate typography
        typography = self._generate_typography(
            heading_font=profile["heading_font"],
            body_font=profile["body_font"],
            style=design_style,
        )

        # Generate borders based on style
        borders = self._generate_borders(profile.get("radius", "8px"), design_style)

        return DesignSystem(
            name=f"{business_idea[:30]} Design System",
            colors=colors,
            typography=typography,
            spacing=Spacing(),
            borders=borders,
            shadows=Shadows(),
            industry=industry,
            style=design_style,
            description=f"Design system generated for {business_idea}",
        )

    def _detect_industry(self, business_idea: str) -> str:
        """Detect industry from business idea text"""
        idea_lower = business_idea.lower()

        industry_keywords = {
            "technology": ["app", "software", "saas", "tech", "platform", "api", "cloud", "ai"],
            "healthcare": ["health", "medical", "wellness", "doctor", "patient", "hospital", "clinic"],
            "finance": ["finance", "bank", "invest", "insurance", "payment", "money", "trading"],
            "ecommerce": ["shop", "store", "commerce", "retail", "buy", "sell", "marketplace"],
            "food": ["food", "restaurant", "cafe", "coffee", "delivery", "recipe", "meal"],
            "fitness": ["fitness", "gym", "workout", "exercise", "sport", "training"],
            "education": ["education", "learn", "school", "course", "student", "teach", "tutor"],
            "travel": ["travel", "hotel", "flight", "booking", "vacation", "trip", "tourism"],
            "real_estate": ["real estate", "property", "house", "apartment", "rent", "mortgage"],
            "creative": ["design", "art", "photo", "creative", "portfolio", "studio"],
        }

        for industry, keywords in industry_keywords.items():
            if any(kw in idea_lower for kw in keywords):
                return industry

        return "default"

    def _generate_color_palette(
        self,
        primary: str,
        secondary: str,
        accent: str,
        style: DesignStyle,
    ) -> ColorPalette:
        """Generate a complete color palette"""
        # Generate neutral palette based on primary color
        neutrals = generate_neutral_palette(primary)

        return ColorPalette(
            primary=primary,
            primary_light=lighten_color(primary, 0.3),
            primary_dark=darken_color(primary, 0.3),
            secondary=secondary,
            secondary_light=lighten_color(secondary, 0.3),
            secondary_dark=darken_color(secondary, 0.3),
            accent=accent,
            neutral_50=neutrals["50"],
            neutral_100=neutrals["100"],
            neutral_200=neutrals["200"],
            neutral_300=neutrals["300"],
            neutral_400=neutrals["400"],
            neutral_500=neutrals["500"],
            neutral_600=neutrals["600"],
            neutral_700=neutrals["700"],
            neutral_800=neutrals["800"],
            neutral_900=neutrals["900"],
            background="#FFFFFF" if style != DesignStyle.TECH else "#0F172A",
            surface="#F8FAFC" if style != DesignStyle.TECH else "#1E293B",
            text_primary=neutrals["900"] if style != DesignStyle.TECH else "#F1F5F9",
            text_secondary=neutrals["600"] if style != DesignStyle.TECH else "#94A3B8",
        )

    def _generate_typography(
        self,
        heading_font: str,
        body_font: str,
        style: DesignStyle,
    ) -> Typography:
        """Generate typography settings"""
        # Optionally use font pairings based on style
        style_key = style.value if style else "modern"
        pairings = FONT_PAIRINGS.get(style_key, FONT_PAIRINGS["modern"])

        # Use provided fonts or pick from pairings
        if not heading_font or not body_font:
            heading_font, body_font = pairings[0]

        return Typography(
            heading_font=heading_font,
            body_font=body_font,
        )

    def _generate_borders(self, base_radius: str, style: DesignStyle) -> Borders:
        """Generate border settings based on style"""
        # Extract numeric value from radius
        radius_match = re.search(r'(\d+)', base_radius)
        base_px = int(radius_match.group(1)) if radius_match else 8

        # Adjust based on style
        if style == DesignStyle.MINIMAL:
            base_px = 4
        elif style == DesignStyle.PLAYFUL:
            base_px = 16
        elif style == DesignStyle.CLASSIC:
            base_px = 4

        return Borders(
            radius_sm=f"{base_px // 2}px",
            radius_default=f"{base_px}px",
            radius_md=f"{int(base_px * 1.5)}px",
            radius_lg=f"{base_px * 2}px",
            radius_xl=f"{base_px * 3}px",
            radius_2xl=f"{base_px * 4}px",
        )


# ===========================================
# Export Functions
# ===========================================

def export_to_css_variables(design_system: DesignSystem) -> str:
    """Export design system to CSS custom properties"""
    colors = design_system.colors
    typography = design_system.typography
    spacing = design_system.spacing
    borders = design_system.borders
    shadows = design_system.shadows

    css = f"""/* {design_system.name} - Generated Design System */
:root {{
  /* Brand Colors */
  --color-primary: {colors.primary};
  --color-primary-light: {colors.primary_light};
  --color-primary-dark: {colors.primary_dark};
  --color-secondary: {colors.secondary};
  --color-secondary-light: {colors.secondary_light};
  --color-secondary-dark: {colors.secondary_dark};
  --color-accent: {colors.accent};

  /* Neutral Colors */
  --color-neutral-50: {colors.neutral_50};
  --color-neutral-100: {colors.neutral_100};
  --color-neutral-200: {colors.neutral_200};
  --color-neutral-300: {colors.neutral_300};
  --color-neutral-400: {colors.neutral_400};
  --color-neutral-500: {colors.neutral_500};
  --color-neutral-600: {colors.neutral_600};
  --color-neutral-700: {colors.neutral_700};
  --color-neutral-800: {colors.neutral_800};
  --color-neutral-900: {colors.neutral_900};

  /* Semantic Colors */
  --color-success: {colors.success};
  --color-warning: {colors.warning};
  --color-error: {colors.error};
  --color-info: {colors.info};

  /* Background Colors */
  --color-background: {colors.background};
  --color-surface: {colors.surface};
  --color-surface-elevated: {colors.surface_elevated};

  /* Text Colors */
  --color-text-primary: {colors.text_primary};
  --color-text-secondary: {colors.text_secondary};
  --color-text-muted: {colors.text_muted};
  --color-text-inverse: {colors.text_inverse};

  /* Typography */
  --font-heading: {typography.heading_font};
  --font-body: {typography.body_font};
  --font-mono: {typography.mono_font};

  /* Font Sizes */
  --font-size-xs: {typography.size_xs};
  --font-size-sm: {typography.size_sm};
  --font-size-base: {typography.size_base};
  --font-size-lg: {typography.size_lg};
  --font-size-xl: {typography.size_xl};
  --font-size-2xl: {typography.size_2xl};
  --font-size-3xl: {typography.size_3xl};
  --font-size-4xl: {typography.size_4xl};
  --font-size-5xl: {typography.size_5xl};

  /* Font Weights */
  --font-weight-light: {typography.weight_light};
  --font-weight-normal: {typography.weight_normal};
  --font-weight-medium: {typography.weight_medium};
  --font-weight-semibold: {typography.weight_semibold};
  --font-weight-bold: {typography.weight_bold};

  /* Line Heights */
  --line-height-tight: {typography.line_tight};
  --line-height-normal: {typography.line_normal};
  --line-height-relaxed: {typography.line_relaxed};

  /* Border Radius */
  --radius-none: {borders.radius_none};
  --radius-sm: {borders.radius_sm};
  --radius-default: {borders.radius_default};
  --radius-md: {borders.radius_md};
  --radius-lg: {borders.radius_lg};
  --radius-xl: {borders.radius_xl};
  --radius-2xl: {borders.radius_2xl};
  --radius-full: {borders.radius_full};

  /* Shadows */
  --shadow-sm: {shadows.sm};
  --shadow-default: {shadows.default};
  --shadow-md: {shadows.md};
  --shadow-lg: {shadows.lg};
  --shadow-xl: {shadows.xl};
  --shadow-inner: {shadows.inner};

  /* Spacing */
  --spacing-unit: {spacing.unit};
}}
"""
    return css


def export_to_tailwind_config(design_system: DesignSystem) -> str:
    """Export design system to Tailwind CSS config"""
    colors = design_system.colors
    typography = design_system.typography
    borders = design_system.borders

    # Extract font family name
    heading_font = typography.heading_font.split(",")[0].strip().strip("'\"")
    body_font = typography.body_font.split(",")[0].strip().strip("'\"")

    config = f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: ["./src/**/*.{{js,ts,jsx,tsx,html}}"],
  theme: {{
    extend: {{
      colors: {{
        primary: {{
          DEFAULT: '{colors.primary}',
          light: '{colors.primary_light}',
          dark: '{colors.primary_dark}',
        }},
        secondary: {{
          DEFAULT: '{colors.secondary}',
          light: '{colors.secondary_light}',
          dark: '{colors.secondary_dark}',
        }},
        accent: '{colors.accent}',
        neutral: {{
          50: '{colors.neutral_50}',
          100: '{colors.neutral_100}',
          200: '{colors.neutral_200}',
          300: '{colors.neutral_300}',
          400: '{colors.neutral_400}',
          500: '{colors.neutral_500}',
          600: '{colors.neutral_600}',
          700: '{colors.neutral_700}',
          800: '{colors.neutral_800}',
          900: '{colors.neutral_900}',
        }},
        success: '{colors.success}',
        warning: '{colors.warning}',
        error: '{colors.error}',
        info: '{colors.info}',
        background: '{colors.background}',
        surface: '{colors.surface}',
      }},
      fontFamily: {{
        heading: ['{heading_font}', 'sans-serif'],
        body: ['{body_font}', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }},
      borderRadius: {{
        sm: '{borders.radius_sm}',
        DEFAULT: '{borders.radius_default}',
        md: '{borders.radius_md}',
        lg: '{borders.radius_lg}',
        xl: '{borders.radius_xl}',
        '2xl': '{borders.radius_2xl}',
      }},
    }},
  }},
  plugins: [],
}}
"""
    return config


def export_to_figma_tokens(design_system: DesignSystem) -> Dict:
    """Export design system as Figma-compatible JSON tokens"""
    colors = design_system.colors
    typography = design_system.typography

    return {
        "colors": {
            "primary": {"value": colors.primary, "type": "color"},
            "primary-light": {"value": colors.primary_light, "type": "color"},
            "primary-dark": {"value": colors.primary_dark, "type": "color"},
            "secondary": {"value": colors.secondary, "type": "color"},
            "accent": {"value": colors.accent, "type": "color"},
            "success": {"value": colors.success, "type": "color"},
            "warning": {"value": colors.warning, "type": "color"},
            "error": {"value": colors.error, "type": "color"},
            "info": {"value": colors.info, "type": "color"},
            "background": {"value": colors.background, "type": "color"},
            "surface": {"value": colors.surface, "type": "color"},
            "text-primary": {"value": colors.text_primary, "type": "color"},
            "text-secondary": {"value": colors.text_secondary, "type": "color"},
        },
        "typography": {
            "heading": {"value": typography.heading_font, "type": "fontFamily"},
            "body": {"value": typography.body_font, "type": "fontFamily"},
            "mono": {"value": typography.mono_font, "type": "fontFamily"},
        },
        "spacing": {
            "unit": {"value": "4", "type": "spacing"},
        },
    }


# ===========================================
# Convenience Functions
# ===========================================

_generator: Optional[DesignGenerator] = None


def get_design_generator() -> DesignGenerator:
    """Get the default design generator instance"""
    global _generator
    if _generator is None:
        _generator = DesignGenerator()
    return _generator


async def generate_design_system(
    business_idea: str,
    industry: Optional[str] = None,
    style: Optional[DesignStyle] = None,
    primary_color: Optional[str] = None,
) -> DesignSystem:
    """Generate a design system for a business idea"""
    generator = get_design_generator()
    return await generator.generate(
        business_idea=business_idea,
        industry=industry,
        style=style,
        primary_color=primary_color,
    )
