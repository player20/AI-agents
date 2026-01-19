"""
Design API Routes

Endpoints for generating and managing design systems.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import logging

from ..ai.design_generator import (
    DesignGenerator,
    DesignSystem,
    DesignStyle,
    ColorPalette,
    Typography,
    INDUSTRY_PROFILES,
    FONT_PAIRINGS,
    export_to_css_variables,
    export_to_tailwind_config,
    export_to_figma_tokens,
    get_complementary_color,
    get_analogous_colors,
    get_triadic_colors,
    lighten_color,
    darken_color,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/design", tags=["Design"])


# ===========================================
# Request/Response Models
# ===========================================

class DesignRequest(BaseModel):
    """Request for design system generation"""
    business_idea: str = Field(..., min_length=5, description="Business/project description")
    industry: Optional[str] = Field(default=None, description="Industry type")
    style: Optional[DesignStyle] = Field(default=None, description="Design style preference")
    primary_color: Optional[str] = Field(default=None, description="Specific primary color (hex)")


class ColorSuggestionRequest(BaseModel):
    """Request for color suggestions"""
    base_color: str = Field(..., description="Base color in hex format")
    harmony: str = Field(default="analogous", description="Color harmony: complementary, analogous, triadic")


class ColorSuggestionResponse(BaseModel):
    """Color suggestion response"""
    base: str
    suggestions: List[str]
    harmony_type: str


class ExportFormat(str, Enum):
    """Design system export formats"""
    CSS = "css"
    TAILWIND = "tailwind"
    FIGMA = "figma"
    JSON = "json"


# ===========================================
# API Endpoints
# ===========================================

@router.post("/generate", response_model=DesignSystem)
async def generate_design_system(request: DesignRequest):
    """
    Generate a complete design system for a business idea.

    Returns colors, typography, spacing, borders, and shadows tailored
    to the industry and style preferences.
    """
    try:
        generator = DesignGenerator()
        design_system = await generator.generate(
            business_idea=request.business_idea,
            industry=request.industry,
            style=request.style,
            primary_color=request.primary_color,
        )
        return design_system

    except Exception as e:
        logger.error(f"Design generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Design generation failed: {str(e)}")


@router.post("/generate/colors", response_model=ColorPalette)
async def generate_color_palette(request: DesignRequest):
    """
    Generate just a color palette for a business idea.

    Useful for quick color scheme generation without full design system.
    """
    try:
        generator = DesignGenerator()
        design_system = await generator.generate(
            business_idea=request.business_idea,
            industry=request.industry,
            style=request.style,
            primary_color=request.primary_color,
        )
        return design_system.colors

    except Exception as e:
        logger.error(f"Color palette generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Color generation failed: {str(e)}")


@router.post("/suggest/colors", response_model=ColorSuggestionResponse)
async def suggest_colors(request: ColorSuggestionRequest):
    """
    Get color suggestions based on a base color and harmony type.

    Harmony types:
    - complementary: Opposite on color wheel
    - analogous: Adjacent colors (30 degrees apart)
    - triadic: Three colors 120 degrees apart
    """
    base = request.base_color.strip()
    if not base.startswith("#"):
        base = f"#{base}"

    try:
        if request.harmony == "complementary":
            suggestions = [get_complementary_color(base)]
        elif request.harmony == "analogous":
            suggestions = list(get_analogous_colors(base))
        elif request.harmony == "triadic":
            suggestions = list(get_triadic_colors(base))
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid harmony type. Use: complementary, analogous, or triadic"
            )

        return ColorSuggestionResponse(
            base=base,
            suggestions=suggestions,
            harmony_type=request.harmony,
        )

    except Exception as e:
        logger.error(f"Color suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Color suggestion failed: {str(e)}")


@router.get("/color/lighten/{hex_color}")
async def lighten_hex_color(hex_color: str, amount: float = 0.2):
    """Lighten a color by a given amount (0-1)"""
    color = hex_color if hex_color.startswith("#") else f"#{hex_color}"
    try:
        lightened = lighten_color(color, amount)
        return {"original": color, "lightened": lightened, "amount": amount}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid color: {str(e)}")


@router.get("/color/darken/{hex_color}")
async def darken_hex_color(hex_color: str, amount: float = 0.2):
    """Darken a color by a given amount (0-1)"""
    color = hex_color if hex_color.startswith("#") else f"#{hex_color}"
    try:
        darkened = darken_color(color, amount)
        return {"original": color, "darkened": darkened, "amount": amount}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid color: {str(e)}")


@router.post("/export/{format}")
async def export_design_system(format: ExportFormat, request: DesignRequest):
    """
    Generate and export a design system in the specified format.

    Formats:
    - css: CSS custom properties (variables)
    - tailwind: Tailwind CSS config
    - figma: Figma-compatible JSON tokens
    - json: Raw JSON
    """
    try:
        generator = DesignGenerator()
        design_system = await generator.generate(
            business_idea=request.business_idea,
            industry=request.industry,
            style=request.style,
            primary_color=request.primary_color,
        )

        if format == ExportFormat.CSS:
            css = export_to_css_variables(design_system)
            return PlainTextResponse(content=css, media_type="text/css")

        elif format == ExportFormat.TAILWIND:
            config = export_to_tailwind_config(design_system)
            return PlainTextResponse(content=config, media_type="application/javascript")

        elif format == ExportFormat.FIGMA:
            tokens = export_to_figma_tokens(design_system)
            return JSONResponse(content=tokens)

        elif format == ExportFormat.JSON:
            return design_system

    except Exception as e:
        logger.error(f"Design export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/industries")
async def list_industries():
    """
    List all supported industries with their default design profiles.
    """
    industries = []
    for name, profile in INDUSTRY_PROFILES.items():
        industries.append({
            "name": name,
            "primary_color": profile["primary"],
            "secondary_color": profile["secondary"],
            "accent_color": profile["accent"],
            "heading_font": profile["heading_font"],
            "body_font": profile["body_font"],
            "style": profile["style"].value if hasattr(profile["style"], "value") else profile["style"],
        })
    return {"industries": industries}


@router.get("/styles")
async def list_styles():
    """
    List all available design styles.
    """
    return {
        "styles": [
            {"name": style.value, "description": _get_style_description(style)}
            for style in DesignStyle
        ]
    }


@router.get("/fonts")
async def list_font_pairings():
    """
    List recommended font pairings by style.
    """
    pairings = []
    for style, pairs in FONT_PAIRINGS.items():
        for heading, body in pairs:
            pairings.append({
                "style": style,
                "heading_font": heading,
                "body_font": body,
            })
    return {"pairings": pairings}


@router.get("/fonts/{style}")
async def get_fonts_for_style(style: str):
    """
    Get font pairings for a specific style.
    """
    style_lower = style.lower()
    if style_lower not in FONT_PAIRINGS:
        raise HTTPException(
            status_code=404,
            detail=f"Style not found. Available: {list(FONT_PAIRINGS.keys())}"
        )

    pairs = FONT_PAIRINGS[style_lower]
    return {
        "style": style_lower,
        "pairings": [
            {"heading": heading, "body": body}
            for heading, body in pairs
        ]
    }


# ===========================================
# Helper Functions
# ===========================================

def _get_style_description(style: DesignStyle) -> str:
    """Get description for a design style"""
    descriptions = {
        DesignStyle.MODERN: "Clean, contemporary design with current trends",
        DesignStyle.CLASSIC: "Timeless, professional styling with traditional elements",
        DesignStyle.PLAYFUL: "Fun, friendly design with rounded shapes and vibrant colors",
        DesignStyle.MINIMAL: "Stripped-back design focusing on essentials",
        DesignStyle.BOLD: "Strong, impactful design with high contrast",
        DesignStyle.ELEGANT: "Sophisticated, refined styling with premium feel",
        DesignStyle.TECH: "Technical, digital-focused design with dark themes",
        DesignStyle.ORGANIC: "Natural, flowing design with earthy tones",
    }
    return descriptions.get(style, "")
