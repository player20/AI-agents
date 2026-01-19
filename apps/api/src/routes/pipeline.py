"""
Unified Pipeline API Routes

Orchestrates the complete Research → Design → Build pipeline.
Combines market research, design system generation, and prototype building
into a single, cohesive workflow.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid
import logging
import asyncio

from ..ai.research_models import (
    ResearchRequest,
    ResearchReport,
    MarketSegment,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


# ===========================================
# Pipeline Models
# ===========================================

class PipelinePhase(str, Enum):
    """Pipeline execution phases"""
    INPUT = "input"
    RESEARCH = "research"
    DESIGN = "design"
    BUILD = "build"
    COMPLETE = "complete"
    ERROR = "error"


class DesignTokens(BaseModel):
    """Generated design system tokens"""
    # Colors
    primary_color: str = Field(description="Primary brand color (hex)")
    secondary_color: str = Field(description="Secondary color (hex)")
    accent_color: str = Field(description="Accent/highlight color (hex)")
    background_color: str = Field(description="Background color (hex)")
    surface_color: str = Field(description="Surface/card color (hex)")
    text_color: str = Field(description="Primary text color (hex)")
    text_secondary_color: str = Field(description="Secondary text color (hex)")
    error_color: str = Field(default="#DC2626", description="Error state color")
    success_color: str = Field(default="#16A34A", description="Success state color")
    warning_color: str = Field(default="#D97706", description="Warning state color")

    # Typography
    heading_font: str = Field(description="Font family for headings")
    body_font: str = Field(description="Font family for body text")
    font_size_base: str = Field(default="16px", description="Base font size")

    # Spacing
    spacing_unit: str = Field(default="4px", description="Base spacing unit")
    border_radius: str = Field(default="8px", description="Default border radius")

    # Shadows
    shadow_sm: str = Field(default="0 1px 2px rgba(0,0,0,0.05)")
    shadow_md: str = Field(default="0 4px 6px rgba(0,0,0,0.1)")
    shadow_lg: str = Field(default="0 10px 15px rgba(0,0,0,0.1)")

    # Industry context
    industry: Optional[str] = None
    style_notes: Optional[str] = None


class PrototypeFile(BaseModel):
    """A generated prototype file"""
    path: str
    content: str
    language: str


class PrototypeOutput(BaseModel):
    """Generated prototype output"""
    files: List[PrototypeFile]
    entry_point: str = Field(default="index.html")
    preview_url: Optional[str] = None
    download_url: Optional[str] = None


class PipelineRequest(BaseModel):
    """Request to start the full pipeline"""
    business_idea: str = Field(..., min_length=10, description="Business idea to analyze and prototype")
    industry: Optional[str] = Field(default=None, description="Industry hint for better results")
    target_market: Optional[MarketSegment] = None
    platform: str = Field(default="web", description="'web', 'mobile', 'both'")
    style_preference: Optional[str] = Field(default=None, description="Design style preference")
    include_prototype: bool = Field(default=True, description="Generate interactive prototype")


class PipelineStatus(BaseModel):
    """Status of a pipeline execution"""
    id: str
    phase: PipelinePhase
    progress: int = Field(ge=0, le=100)
    current_task: str
    phases_completed: List[str]
    error: Optional[str] = None
    started_at: datetime
    estimated_completion: Optional[datetime] = None


class PipelineResponse(BaseModel):
    """Complete pipeline response"""
    id: str
    status: PipelinePhase
    business_idea: str

    # Outputs
    research_report: Optional[ResearchReport] = None
    design_tokens: Optional[DesignTokens] = None
    prototype: Optional[PrototypeOutput] = None

    # Metadata
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Export URLs
    report_pdf_url: Optional[str] = None
    report_html_url: Optional[str] = None
    prototype_zip_url: Optional[str] = None
    figma_export_url: Optional[str] = None


# ===========================================
# Pipeline Storage
# ===========================================

_pipeline_jobs: Dict[str, Dict[str, Any]] = {}


# ===========================================
# Industry Design Profiles
# ===========================================

INDUSTRY_DESIGN_PROFILES = {
    "technology": {
        "primary_color": "#3B82F6",
        "secondary_color": "#1E40AF",
        "accent_color": "#06B6D4",
        "background_color": "#F8FAFC",
        "surface_color": "#FFFFFF",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "border_radius": "8px",
        "style_notes": "Clean, modern, professional"
    },
    "healthcare": {
        "primary_color": "#0D9488",
        "secondary_color": "#115E59",
        "accent_color": "#2DD4BF",
        "background_color": "#F0FDFA",
        "surface_color": "#FFFFFF",
        "text_color": "#134E4A",
        "text_secondary_color": "#5EEAD4",
        "heading_font": "Source Sans Pro, system-ui, sans-serif",
        "body_font": "Source Sans Pro, system-ui, sans-serif",
        "border_radius": "12px",
        "style_notes": "Trustworthy, calming, accessible"
    },
    "finance": {
        "primary_color": "#1E3A8A",
        "secondary_color": "#1E40AF",
        "accent_color": "#F59E0B",
        "background_color": "#F8FAFC",
        "surface_color": "#FFFFFF",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "heading_font": "IBM Plex Sans, system-ui, sans-serif",
        "body_font": "IBM Plex Sans, system-ui, sans-serif",
        "border_radius": "4px",
        "style_notes": "Professional, trustworthy, sophisticated"
    },
    "ecommerce": {
        "primary_color": "#7C3AED",
        "secondary_color": "#5B21B6",
        "accent_color": "#F472B6",
        "background_color": "#FAF5FF",
        "surface_color": "#FFFFFF",
        "text_color": "#1F2937",
        "text_secondary_color": "#6B7280",
        "heading_font": "Poppins, system-ui, sans-serif",
        "body_font": "Open Sans, system-ui, sans-serif",
        "border_radius": "16px",
        "style_notes": "Vibrant, engaging, conversion-focused"
    },
    "food": {
        "primary_color": "#EA580C",
        "secondary_color": "#C2410C",
        "accent_color": "#FACC15",
        "background_color": "#FFFBEB",
        "surface_color": "#FFFFFF",
        "text_color": "#1C1917",
        "text_secondary_color": "#78716C",
        "heading_font": "Playfair Display, serif",
        "body_font": "Lato, system-ui, sans-serif",
        "border_radius": "8px",
        "style_notes": "Warm, appetizing, inviting"
    },
    "fitness": {
        "primary_color": "#DC2626",
        "secondary_color": "#991B1B",
        "accent_color": "#22C55E",
        "background_color": "#F9FAFB",
        "surface_color": "#FFFFFF",
        "text_color": "#111827",
        "text_secondary_color": "#6B7280",
        "heading_font": "Montserrat, system-ui, sans-serif",
        "body_font": "Roboto, system-ui, sans-serif",
        "border_radius": "8px",
        "style_notes": "Energetic, motivating, bold"
    },
    "education": {
        "primary_color": "#2563EB",
        "secondary_color": "#1D4ED8",
        "accent_color": "#10B981",
        "background_color": "#F0F9FF",
        "surface_color": "#FFFFFF",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "heading_font": "Nunito, system-ui, sans-serif",
        "body_font": "Open Sans, system-ui, sans-serif",
        "border_radius": "12px",
        "style_notes": "Friendly, approachable, clear"
    },
    "default": {
        "primary_color": "#6366F1",
        "secondary_color": "#4338CA",
        "accent_color": "#EC4899",
        "background_color": "#F8FAFC",
        "surface_color": "#FFFFFF",
        "text_color": "#1E293B",
        "text_secondary_color": "#64748B",
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "border_radius": "8px",
        "style_notes": "Modern, versatile, professional"
    }
}


# ===========================================
# Pipeline Execution Logic
# ===========================================

async def _run_pipeline(job_id: str, request: PipelineRequest):
    """
    Execute the complete Research → Design → Build pipeline.
    """
    job = _pipeline_jobs[job_id]

    try:
        # ===========================================
        # PHASE 1: Research
        # ===========================================
        job["phase"] = PipelinePhase.RESEARCH
        job["current_task"] = "Analyzing market and competitors"
        job["progress"] = 5

        # Run research analysis
        from .research import (
            _generate_market_research,
            _generate_competitor_analysis,
            _generate_feature_recommendations,
            _generate_gtm_strategy,
            _generate_swot_analysis,
            _compile_research_report,
        )

        # Market Research
        job["current_task"] = "Conducting market research"
        job["progress"] = 10
        market = await _generate_market_research(request.business_idea)

        # Competitor Analysis
        job["current_task"] = "Analyzing competitors"
        job["progress"] = 20
        competitors = await _generate_competitor_analysis(request.business_idea, market)

        # Feature Recommendations
        job["current_task"] = "Generating feature recommendations"
        job["progress"] = 30
        features = await _generate_feature_recommendations(
            request.business_idea, market, competitors
        )

        # GTM Strategy
        job["current_task"] = "Creating go-to-market strategy"
        job["progress"] = 35
        gtm = await _generate_gtm_strategy(
            request.business_idea, market, competitors, features
        )

        # SWOT Analysis
        job["current_task"] = "Conducting SWOT analysis"
        job["progress"] = 40
        swot = await _generate_swot_analysis(
            request.business_idea, market, competitors, features, gtm
        )

        # Compile Research Report
        job["current_task"] = "Compiling research report"
        job["progress"] = 45
        research_report = await _compile_research_report(
            job_id, request.business_idea, market, competitors, features, gtm, swot
        )

        job["research_report"] = research_report
        job["phases_completed"].append("research")

        # ===========================================
        # PHASE 2: Design
        # ===========================================
        job["phase"] = PipelinePhase.DESIGN
        job["current_task"] = "Generating design system"
        job["progress"] = 50

        # Determine industry from research
        industry = request.industry or market.industry_vertical.lower()
        industry_key = _match_industry(industry)

        # Generate design tokens
        design_tokens = await _generate_design_tokens(
            request.business_idea,
            industry_key,
            request.style_preference
        )

        job["design_tokens"] = design_tokens
        job["progress"] = 60
        job["phases_completed"].append("design")

        # ===========================================
        # PHASE 3: Build (if requested)
        # ===========================================
        if request.include_prototype:
            job["phase"] = PipelinePhase.BUILD
            job["current_task"] = "Generating prototype"
            job["progress"] = 65

            prototype = await _generate_prototype(
                request.business_idea,
                features,
                design_tokens,
                request.platform
            )

            job["prototype"] = prototype
            job["progress"] = 95
            job["phases_completed"].append("build")

        # ===========================================
        # Complete
        # ===========================================
        job["phase"] = PipelinePhase.COMPLETE
        job["current_task"] = "Pipeline complete"
        job["progress"] = 100
        job["completed_at"] = datetime.now()

    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}")
        job["phase"] = PipelinePhase.ERROR
        job["error"] = str(e)


def _match_industry(industry: str) -> str:
    """Match industry string to design profile key"""
    industry_lower = industry.lower()

    if any(kw in industry_lower for kw in ["tech", "software", "saas", "app"]):
        return "technology"
    elif any(kw in industry_lower for kw in ["health", "medical", "wellness"]):
        return "healthcare"
    elif any(kw in industry_lower for kw in ["finance", "bank", "insurance", "invest"]):
        return "finance"
    elif any(kw in industry_lower for kw in ["shop", "store", "commerce", "retail"]):
        return "ecommerce"
    elif any(kw in industry_lower for kw in ["food", "restaurant", "cafe", "coffee"]):
        return "food"
    elif any(kw in industry_lower for kw in ["fitness", "gym", "sport", "health"]):
        return "fitness"
    elif any(kw in industry_lower for kw in ["education", "learn", "school", "course"]):
        return "education"
    else:
        return "default"


async def _generate_design_tokens(
    business_idea: str,
    industry: str,
    style_preference: Optional[str] = None
) -> DesignTokens:
    """Generate design tokens based on industry and preferences"""
    try:
        from ..ai.structured_output import get_structured_client

        client = get_structured_client()

        # Get base profile
        base_profile = INDUSTRY_DESIGN_PROFILES.get(industry, INDUSTRY_DESIGN_PROFILES["default"])

        system = """You are an expert UI/UX designer specializing in design systems.
        Generate a cohesive color palette and typography system that matches the business
        and industry. Return colors as hex values. Choose fonts that are web-safe or
        available on Google Fonts."""

        style_hint = f"\nStyle preference: {style_preference}" if style_preference else ""

        return await client.generate(
            response_model=DesignTokens,
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Generate design tokens for: {business_idea}

Industry: {industry}
Base palette suggestion: Primary {base_profile['primary_color']}, Secondary {base_profile['secondary_color']}
{style_hint}

Create a modern, accessible design system."""
            }],
            temperature=0.8
        )

    except Exception as e:
        logger.warning(f"AI design generation failed, using industry defaults: {e}")
        profile = INDUSTRY_DESIGN_PROFILES.get(industry, INDUSTRY_DESIGN_PROFILES["default"])
        return DesignTokens(
            primary_color=profile["primary_color"],
            secondary_color=profile["secondary_color"],
            accent_color=profile["accent_color"],
            background_color=profile["background_color"],
            surface_color=profile["surface_color"],
            text_color=profile["text_color"],
            text_secondary_color=profile["text_secondary_color"],
            heading_font=profile["heading_font"],
            body_font=profile["body_font"],
            border_radius=profile["border_radius"],
            industry=industry,
            style_notes=profile["style_notes"]
        )


async def _generate_prototype(
    business_idea: str,
    features: Any,
    design_tokens: DesignTokens,
    platform: str
) -> PrototypeOutput:
    """Generate a basic interactive prototype"""

    # Generate CSS from design tokens
    css_content = f"""/* Generated Design System */
:root {{
  /* Colors */
  --color-primary: {design_tokens.primary_color};
  --color-secondary: {design_tokens.secondary_color};
  --color-accent: {design_tokens.accent_color};
  --color-background: {design_tokens.background_color};
  --color-surface: {design_tokens.surface_color};
  --color-text: {design_tokens.text_color};
  --color-text-secondary: {design_tokens.text_secondary_color};
  --color-error: {design_tokens.error_color};
  --color-success: {design_tokens.success_color};
  --color-warning: {design_tokens.warning_color};

  /* Typography */
  --font-heading: {design_tokens.heading_font};
  --font-body: {design_tokens.body_font};
  --font-size-base: {design_tokens.font_size_base};

  /* Spacing */
  --spacing-unit: {design_tokens.spacing_unit};
  --border-radius: {design_tokens.border_radius};

  /* Shadows */
  --shadow-sm: {design_tokens.shadow_sm};
  --shadow-md: {design_tokens.shadow_md};
  --shadow-lg: {design_tokens.shadow_lg};
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  color: var(--color-text);
  background-color: var(--color-background);
  line-height: 1.6;
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-heading);
  font-weight: 600;
  color: var(--color-text);
}}

.container {{
  max-width: 1200px;
  margin: 0 auto;
  padding: calc(var(--spacing-unit) * 4);
}}

/* Buttons */
.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: calc(var(--spacing-unit) * 3) calc(var(--spacing-unit) * 6);
  border: none;
  border-radius: var(--border-radius);
  font-family: var(--font-body);
  font-size: var(--font-size-base);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}}

.btn-primary {{
  background-color: var(--color-primary);
  color: white;
}}

.btn-primary:hover {{
  filter: brightness(1.1);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}}

.btn-secondary {{
  background-color: var(--color-surface);
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
}}

/* Cards */
.card {{
  background-color: var(--color-surface);
  border-radius: var(--border-radius);
  padding: calc(var(--spacing-unit) * 6);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}}

.card:hover {{
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}}

/* Header */
.header {{
  background-color: var(--color-surface);
  box-shadow: var(--shadow-sm);
  padding: calc(var(--spacing-unit) * 4);
}}

.nav {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
}}

.nav-links {{
  display: flex;
  gap: calc(var(--spacing-unit) * 6);
  list-style: none;
}}

.nav-links a {{
  color: var(--color-text);
  text-decoration: none;
  font-weight: 500;
}}

.nav-links a:hover {{
  color: var(--color-primary);
}}

/* Hero Section */
.hero {{
  text-align: center;
  padding: calc(var(--spacing-unit) * 20) calc(var(--spacing-unit) * 4);
}}

.hero h1 {{
  font-size: 3rem;
  margin-bottom: calc(var(--spacing-unit) * 4);
}}

.hero p {{
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: calc(var(--spacing-unit) * 8);
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}}

/* Features Grid */
.features {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: calc(var(--spacing-unit) * 6);
  padding: calc(var(--spacing-unit) * 10) calc(var(--spacing-unit) * 4);
}}

.feature-icon {{
  width: 48px;
  height: 48px;
  background-color: var(--color-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: calc(var(--spacing-unit) * 4);
  color: white;
  font-size: 1.5rem;
}}

/* Footer */
.footer {{
  background-color: var(--color-text);
  color: white;
  padding: calc(var(--spacing-unit) * 10);
  text-align: center;
}}
"""

    # Generate feature items for HTML
    feature_items = ""
    if hasattr(features, 'mvp_features'):
        for i, feature in enumerate(features.mvp_features[:6]):
            icons = ["🚀", "⚡", "🔒", "📊", "🎯", "✨"]
            icon = icons[i % len(icons)]
            feature_items += f"""
      <div class="card">
        <div class="feature-icon">{icon}</div>
        <h3>{feature.name}</h3>
        <p>{feature.description}</p>
      </div>"""

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{business_idea}</title>
  <link rel="stylesheet" href="styles.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
  <header class="header">
    <nav class="nav">
      <div class="logo">
        <h2 style="color: var(--color-primary);">{business_idea.split()[0] if business_idea else 'Brand'}</h2>
      </div>
      <ul class="nav-links">
        <li><a href="#features">Features</a></li>
        <li><a href="#pricing">Pricing</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#contact">Contact</a></li>
      </ul>
      <div class="nav-actions">
        <a href="#" class="btn btn-secondary">Login</a>
        <a href="#" class="btn btn-primary">Get Started</a>
      </div>
    </nav>
  </header>

  <main>
    <section class="hero">
      <h1>Welcome to the Future</h1>
      <p>{business_idea}</p>
      <div style="display: flex; gap: 16px; justify-content: center;">
        <a href="#" class="btn btn-primary">Get Started Free</a>
        <a href="#" class="btn btn-secondary">Learn More</a>
      </div>
    </section>

    <section id="features" class="container">
      <h2 style="text-align: center; margin-bottom: 48px;">Key Features</h2>
      <div class="features">
        {feature_items if feature_items else '''
        <div class="card">
          <div class="feature-icon">🚀</div>
          <h3>Fast & Efficient</h3>
          <p>Built for speed and performance from the ground up.</p>
        </div>
        <div class="card">
          <div class="feature-icon">⚡</div>
          <h3>Easy to Use</h3>
          <p>Intuitive interface that anyone can master quickly.</p>
        </div>
        <div class="card">
          <div class="feature-icon">🔒</div>
          <h3>Secure</h3>
          <p>Enterprise-grade security to protect your data.</p>
        </div>
        '''}
      </div>
    </section>

    <section id="cta" class="container" style="text-align: center; padding: 80px 20px;">
      <h2>Ready to get started?</h2>
      <p style="color: var(--color-text-secondary); margin: 20px 0 40px;">Join thousands of users already using our platform.</p>
      <a href="#" class="btn btn-primary">Start Free Trial</a>
    </section>
  </main>

  <footer class="footer">
    <p>&copy; 2024 {business_idea.split()[0] if business_idea else 'Company'}. All rights reserved.</p>
  </footer>
</body>
</html>
"""

    # Generate Tailwind config
    tailwind_config = f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: ["./**/*.html", "./**/*.js"],
  theme: {{
    extend: {{
      colors: {{
        primary: '{design_tokens.primary_color}',
        secondary: '{design_tokens.secondary_color}',
        accent: '{design_tokens.accent_color}',
        background: '{design_tokens.background_color}',
        surface: '{design_tokens.surface_color}',
        'text-primary': '{design_tokens.text_color}',
        'text-secondary': '{design_tokens.text_secondary_color}',
      }},
      fontFamily: {{
        heading: ['{design_tokens.heading_font.split(",")[0]}', 'sans-serif'],
        body: ['{design_tokens.body_font.split(",")[0]}', 'sans-serif'],
      }},
      borderRadius: {{
        DEFAULT: '{design_tokens.border_radius}',
      }},
    }},
  }},
  plugins: [],
}}
"""

    return PrototypeOutput(
        files=[
            PrototypeFile(path="index.html", content=html_content, language="html"),
            PrototypeFile(path="styles.css", content=css_content, language="css"),
            PrototypeFile(path="tailwind.config.js", content=tailwind_config, language="javascript"),
        ],
        entry_point="index.html"
    )


# ===========================================
# API Endpoints
# ===========================================

@router.post("/start", response_model=PipelineStatus, status_code=202)
async def start_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """
    Start the full Research → Design → Build pipeline.

    This initiates a comprehensive process that:
    1. **Research Phase**: Market analysis, competitor research, feature recommendations, GTM strategy, SWOT
    2. **Design Phase**: Generate design system (colors, typography, spacing)
    3. **Build Phase**: Generate interactive prototype with live preview

    Returns a job ID to track progress and retrieve results.
    """
    job_id = str(uuid.uuid4())

    _pipeline_jobs[job_id] = {
        "id": job_id,
        "phase": PipelinePhase.INPUT,
        "progress": 0,
        "current_task": "Initializing pipeline",
        "phases_completed": [],
        "request": request.model_dump(),
        "research_report": None,
        "design_tokens": None,
        "prototype": None,
        "error": None,
        "started_at": datetime.now(),
        "completed_at": None,
    }

    # Start background pipeline
    background_tasks.add_task(_run_pipeline, job_id, request)

    return PipelineStatus(
        id=job_id,
        phase=PipelinePhase.INPUT,
        progress=0,
        current_task="Initializing pipeline",
        phases_completed=[],
        started_at=_pipeline_jobs[job_id]["started_at"]
    )


@router.get("/{job_id}", response_model=PipelineResponse)
async def get_pipeline(job_id: str):
    """
    Get the full results of a pipeline execution.

    Returns all outputs: research report, design tokens, and prototype files.
    """
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    job = _pipeline_jobs[job_id]

    return PipelineResponse(
        id=job_id,
        status=job["phase"],
        business_idea=job["request"]["business_idea"],
        research_report=job.get("research_report"),
        design_tokens=job.get("design_tokens"),
        prototype=job.get("prototype"),
        started_at=job["started_at"],
        completed_at=job.get("completed_at")
    )


@router.get("/{job_id}/status", response_model=PipelineStatus)
async def get_pipeline_status(job_id: str):
    """
    Get just the status of a pipeline (lightweight endpoint for polling).
    """
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    job = _pipeline_jobs[job_id]

    return PipelineStatus(
        id=job_id,
        phase=job["phase"],
        progress=job["progress"],
        current_task=job["current_task"],
        phases_completed=job["phases_completed"],
        error=job.get("error"),
        started_at=job["started_at"]
    )


@router.get("/{job_id}/research", response_model=Optional[ResearchReport])
async def get_pipeline_research(job_id: str):
    """Get just the research report from a pipeline."""
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    report = _pipeline_jobs[job_id].get("research_report")
    if not report:
        raise HTTPException(status_code=404, detail="Research not yet complete")

    return report


@router.get("/{job_id}/design", response_model=Optional[DesignTokens])
async def get_pipeline_design(job_id: str):
    """Get just the design tokens from a pipeline."""
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    tokens = _pipeline_jobs[job_id].get("design_tokens")
    if not tokens:
        raise HTTPException(status_code=404, detail="Design not yet complete")

    return tokens


@router.get("/{job_id}/prototype", response_model=Optional[PrototypeOutput])
async def get_pipeline_prototype(job_id: str):
    """Get just the prototype files from a pipeline."""
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    prototype = _pipeline_jobs[job_id].get("prototype")
    if not prototype:
        raise HTTPException(status_code=404, detail="Prototype not yet complete")

    return prototype


@router.delete("/{job_id}", status_code=204)
async def cancel_pipeline(job_id: str):
    """Cancel a pipeline execution."""
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    _pipeline_jobs[job_id]["phase"] = PipelinePhase.ERROR
    _pipeline_jobs[job_id]["error"] = "Cancelled by user"
    return None


@router.get("/", response_model=List[PipelineStatus])
async def list_pipelines(
    phase: Optional[PipelinePhase] = None,
    limit: int = 20
):
    """List all pipeline executions with optional phase filter."""
    jobs = list(_pipeline_jobs.values())

    if phase:
        jobs = [j for j in jobs if j["phase"] == phase]

    # Sort by started_at descending
    jobs.sort(key=lambda j: j["started_at"], reverse=True)

    return [
        PipelineStatus(
            id=j["id"],
            phase=j["phase"],
            progress=j["progress"],
            current_task=j["current_task"],
            phases_completed=j["phases_completed"],
            error=j.get("error"),
            started_at=j["started_at"]
        )
        for j in jobs[:limit]
    ]
