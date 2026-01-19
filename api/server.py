"""
FastAPI server that bridges the Next.js frontend to the Python weaver CLI backend.
Run with: uvicorn api.server:app --reload --port 8000
"""

import asyncio
import json
import os
import re
import sys
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from html import escape
import logging

# AI imports for idea validation
try:
    import instructor
    import anthropic
    import openai  # For Grok (xAI uses OpenAI-compatible API)
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI packages not available - falling back to simulated idea validation")

logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Pydantic Models
# ============================================================================

class AuditRequest(BaseModel):
    url: str
    full: bool = False
    users: int = 3
    max_pages: int = 10
    analytics_path: Optional[str] = None


class AuditResult(BaseModel):
    url: str
    timestamp: str
    mode: str
    scores: dict
    score_feedback: Optional[dict] = None
    issues: list
    recommendations: list
    confidence: dict
    funnel_analysis: Optional[dict] = None
    analytics: Optional[dict] = None
    pages_crawled: Optional[list] = None
    total_pages: Optional[int] = None


class CodeAuditRequest(BaseModel):
    repo_url: str


class ProjectCreate(BaseModel):
    name: str
    description: str
    platform: str = "web"


class Project(BaseModel):
    id: str
    name: str
    description: str
    platform: str
    status: str
    created_at: str
    updated_at: str


class ABTestCreate(BaseModel):
    name: str
    project_id: str
    variants: List[dict]
    target_metric: str


class MarketResearchRequest(BaseModel):
    query: str
    competitors: Optional[List[str]] = None
    industry: Optional[str] = None


class IdeaValidationRequest(BaseModel):
    """Beginner-friendly business idea validation - just describe your idea"""
    idea: str  # The ONLY required field - "I want to build an app that..."
    problem: Optional[str] = None  # What frustration does it solve?
    target_users: Optional[str] = None  # Who would use this?
    # Optional - only if they already know these
    known_competitors: Optional[List[str]] = None
    industry_guess: Optional[str] = None
    # AI Provider selection: "claude" for deep analysis, "grok" for real-time trends, None for auto
    provider: Optional[str] = None  # "claude", "grok", or None (auto-detect)


class DiscoveredCompetitor(BaseModel):
    """A competitor discovered through analysis"""
    name: str
    description: str
    website: Optional[str] = None
    strengths: List[str]
    weaknesses: List[str]
    similarity_score: float  # 0-1, how similar to your idea
    funding_stage: Optional[str] = None  # seed, series-a, etc.


class IdeaValidationResult(BaseModel):
    """Complete idea validation with discovered insights"""
    id: str
    idea: str
    timestamp: str

    # DISCOVERED by system (not provided by user)
    discovered_industry: str
    industry_category: str  # e.g., "Health & Wellness > Meal Planning > Family"
    discovered_competitors: List[dict]

    # PROBLEM VALIDATION
    problem_exists: bool
    problem_severity: str  # "hair-on-fire", "significant", "nice-to-have"
    search_volume: Optional[str] = None  # "high", "medium", "low"
    problem_evidence: List[str]  # Evidence the problem exists

    # VIABILITY ANALYSIS
    viability_score: int  # 0-100
    viability_breakdown: dict  # {problem: 80, timing: 70, competition: 60, ...}

    # DIFFERENTIATION
    differentiation_opportunities: List[dict]  # {opportunity, difficulty, impact}
    unique_angles: List[str]  # Ways to be different

    # MARKET ANALYSIS
    market_timing: str  # "excellent", "good", "challenging", "poor"
    market_timing_reasons: List[str]
    market_saturation: str  # "blue-ocean", "growing", "crowded", "saturated"
    estimated_tam: Optional[str] = None  # Total addressable market

    # VERDICT
    go_no_go: str  # "GO", "CAUTION", "PIVOT", "STOP"
    verdict: str  # One sentence summary
    verdict_reasons: List[str]

    # ACTIONABLE NEXT STEPS
    next_steps: List[dict]  # {step, why, priority}
    pivot_suggestions: Optional[List[str]] = None  # If PIVOT recommended


class ExportRequest(BaseModel):
    """Audit data to export as HTML report"""
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields from AuditResult (mode, analytics)

    url: str
    timestamp: str
    scores: dict
    score_feedback: Optional[dict] = None
    issues: list
    recommendations: list
    confidence: dict
    funnel_analysis: Optional[dict] = None
    pages_crawled: Optional[list] = None
    total_pages: Optional[int] = None
    # Company personalization fields
    company_name: str  # Required - used throughout report
    industry: str = "general"  # e-commerce, saas, b2b, content, other
    monthly_visitors: Optional[int] = None  # For ROI calculations


class FunnelStep(BaseModel):
    """A step in a user flow funnel"""
    name: str
    screen_name: Optional[str] = None
    users_entered: int
    users_completed: int
    drop_off_rate: Optional[float] = None  # Calculated if not provided


class ScreenMetrics(BaseModel):
    """Analytics metrics for a specific screen"""
    screen_name: str
    avg_time_spent_seconds: Optional[float] = None
    bounce_rate: Optional[float] = None
    rage_taps: Optional[int] = None  # Frustrated repeated taps
    scroll_depth: Optional[float] = None  # 0-100%
    error_rate: Optional[float] = None
    crash_count: Optional[int] = None


class UserPersona(BaseModel):
    """Target user persona"""
    name: str
    description: str
    goals: List[str]
    pain_points: Optional[List[str]] = None
    tech_savviness: Optional[str] = None  # low, medium, high
    age_range: Optional[str] = None
    accessibility_needs: Optional[List[str]] = None  # e.g., ["color_blind", "motor_impaired"]


class BusinessGoals(BaseModel):
    """Business goals and KPIs for the app"""
    primary_goal: str  # e.g., "increase trial signups", "reduce cart abandonment"
    target_metric: Optional[str] = None  # e.g., "conversion_rate"
    current_value: Optional[float] = None  # e.g., 2.5 (%)
    target_value: Optional[float] = None  # e.g., 4.0 (%)
    monthly_active_users: Optional[int] = None
    average_revenue_per_user: Optional[float] = None


class AnalyticsData(BaseModel):
    """Analytics data for deeper analysis"""
    funnel_data: Optional[List[FunnelStep]] = None
    screen_metrics: Optional[List[ScreenMetrics]] = None
    top_user_complaints: Optional[List[str]] = None
    crash_screens: Optional[List[str]] = None  # Screens with highest crash rates
    session_recording_urls: Optional[List[str]] = None  # URLs to session recordings


class MobileAppAuditRequest(BaseModel):
    """Request for mobile app audit via screenshots"""
    app_name: str
    platform: str = "ios"  # ios, android, or both
    screenshots: List[str]  # Base64 encoded images
    screen_names: Optional[List[str]] = None  # Optional names for each screenshot
    app_store_url: Optional[str] = None
    description: Optional[str] = None

    # Enhanced inputs for deeper analysis
    analytics: Optional[AnalyticsData] = None
    user_personas: Optional[List[UserPersona]] = None
    business_goals: Optional[BusinessGoals] = None
    screen_recordings: Optional[List[str]] = None  # Base64 encoded videos or URLs
    competitor_apps: Optional[List[str]] = None  # Names or URLs of competitor apps


class MobileScreenAnalysis(BaseModel):
    """Analysis of a single mobile screen"""
    screen_name: str
    issues: List[Dict[str, Any]]
    positive_aspects: List[str]
    accessibility_score: float
    ui_consistency_score: float
    platform_compliance_score: float
    # Analytics-informed fields
    analytics_insights: Optional[List[str]] = None
    drop_off_correlation: Optional[str] = None
    priority_level: Optional[str] = None  # Based on funnel position


class MobileAppAuditResult(BaseModel):
    """Complete mobile app audit result"""
    app_name: str
    platform: str
    timestamp: str
    overall_score: float
    scores: Dict[str, float]  # ui_ux, accessibility, platform_compliance, navigation, visual_design
    screen_analyses: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    summary: str
    confidence: Dict[str, Any]
    # Enhanced output
    funnel_analysis: Optional[Dict[str, Any]] = None
    roi_projection: Optional[Dict[str, Any]] = None
    persona_impact: Optional[List[Dict[str, Any]]] = None
    priority_matrix: Optional[Dict[str, Any]] = None  # Issues mapped by impact vs effort


# ============================================================================
# In-memory storage
# ============================================================================

projects_db: dict = {}
audit_results_db: dict = {}
ab_tests_db: dict = {}
market_research_db: dict = {}


# ============================================================================
# Issue Impact Mappings for Professional Reports
# ============================================================================

INDUSTRY_IMPACTS = {
    "e-commerce": {
        "slow_load": "Every 1 second delay = 7% fewer conversions. With your estimated traffic, this directly impacts sales.",
        "console_errors": "Broken checkout or 'Add to Cart' buttons mean immediate lost sales. Users won't wait - they'll buy from a competitor.",
        "missing_alt": "Product images without alt text can't be found in Google Image search - a major source of e-commerce traffic.",
        "missing_labels": "Checkout form issues cause cart abandonment. Clear form labels reduce friction in the purchase flow.",
        "missing_h1": "Search engines can't understand your product pages. This hurts ranking for product-related searches.",
        "missing_title": "Your products won't stand out in search results, reducing click-through from Google.",
        "missing_meta": "Without meta descriptions, Google pulls random text - often not your best selling points.",
    },
    "saas": {
        "slow_load": "Slow demos lose signups. 40% of SaaS prospects abandon during slow loading sequences.",
        "console_errors": "App errors during free trials mean users never convert to paid. Each lost trial impacts lifetime value.",
        "missing_labels": "Form accessibility issues reduce trial signups by 15-20% from users with disabilities.",
        "missing_alt": "Screen reader users can't understand your product screenshots, limiting accessibility.",
        "missing_h1": "Landing pages without clear headings confuse visitors about what your product does.",
        "missing_title": "Your SaaS solution won't rank for problem-solving searches users make.",
        "missing_meta": "Feature pages without descriptions don't attract the right users from search.",
    },
    "b2b": {
        "slow_load": "B2B buyers research 70% of their decision before contacting sales. A slow site loses them to competitors.",
        "console_errors": "Technical errors signal unreliability. B2B buyers won't trust their business to a vendor with a broken website.",
        "missing_meta": "Missing SEO elements mean your competitors rank higher. B2B buyers start with Google.",
        "missing_alt": "Case study images without descriptions reduce the impact of your success stories.",
        "missing_labels": "Contact form issues mean lost leads. Every form abandonment is a potential deal lost.",
        "missing_h1": "Service pages without clear headings don't communicate value propositions effectively.",
        "missing_title": "Your services won't appear when buyers search for solutions you offer.",
    },
    "content": {
        "missing_alt": "15% of your readers have visual impairments. Missing alt text excludes them AND violates ADA requirements.",
        "missing_h1": "Without proper headings, screen reader users can't navigate your content. Article structure matters.",
        "slow_load": "Readers bounce from slow pages. Your bounce rate directly impacts ad revenue and engagement metrics.",
        "console_errors": "Interactive elements that break frustrate readers and reduce time-on-site metrics.",
        "missing_meta": "Articles without descriptions get fewer clicks from search results.",
        "missing_title": "Headlines don't appear correctly in search results, reducing traffic.",
        "missing_labels": "Newsletter signup forms that are hard to use mean fewer subscribers.",
    },
    "general": {
        "slow_load": "53% of users abandon pages taking more than 3 seconds to load.",
        "console_errors": "JavaScript errors can break interactive features, frustrating users.",
        "missing_alt": "Images without alt text are invisible to screen readers and hurt SEO.",
        "missing_labels": "Form fields without labels are difficult for all users, especially those with disabilities.",
        "missing_h1": "Pages without H1 headings lack clear structure for users and search engines.",
        "missing_title": "Missing page titles hurt SEO and make browser tabs confusing.",
        "missing_meta": "Without meta descriptions, search engines may display random page content.",
    }
}

ISSUE_IMPACTS = {
    "missing_alt": {
        "title": "Images Missing Alt Text",
        "what": "Screen readers cannot describe these images to visually impaired users.",
        "impact": "~15% of users have some form of visual impairment. Also hurts SEO - Google cannot index image content.",
        "fix": "Add descriptive alt=\"...\" attributes to all <img> tags describing what the image shows.",
        "effort": "Easy",
        "category": "accessibility"
    },
    "missing_title": {
        "title": "Page Missing Title Tag",
        "what": "Browser tabs show generic text, search results show URL instead of a descriptive title.",
        "impact": "50% lower click-through from search results. Users can't find your tab among others.",
        "fix": "Add unique, descriptive <title> tags to each page (50-60 characters recommended).",
        "effort": "Easy",
        "category": "seo"
    },
    "console_errors": {
        "title": "JavaScript Console Errors",
        "what": "JavaScript code is crashing, potentially breaking interactive features like buttons, forms, and navigation.",
        "impact": "Users may experience broken functionality - buttons that don't work, forms that won't submit, features that fail.",
        "fix": "Open browser DevTools (F12), check the Console tab, identify error sources, and fix the JavaScript bugs.",
        "effort": "Medium",
        "category": "ux"
    },
    "missing_labels": {
        "title": "Form Inputs Without Labels",
        "what": "Form fields don't have associated labels for screen readers to announce.",
        "impact": "Blind users can't tell what information to enter. May cause form abandonment for all users.",
        "fix": "Add <label for='id'> elements linking to each input field.",
        "effort": "Easy",
        "category": "accessibility"
    },
    "missing_h1": {
        "title": "No H1 Heading",
        "what": "Page has no main heading defining its primary topic.",
        "impact": "Search engines can't understand page topic. Screen reader users miss important context.",
        "fix": "Add exactly one H1 heading that clearly describes the main page content.",
        "effort": "Easy",
        "category": "seo"
    },
    "slow_load": {
        "title": "Slow Page Load Time",
        "what": "Page takes too long to become interactive for users.",
        "impact": "53% of users abandon pages taking >3 seconds. Every 1s delay = 7% fewer conversions.",
        "fix": "Optimize images, enable browser caching, reduce JavaScript bundle size, use a CDN.",
        "effort": "Medium",
        "category": "performance"
    },
    "missing_meta": {
        "title": "Missing Meta Description",
        "what": "No description for search engines to display in results.",
        "impact": "Lower click-through rates from search. Google may pull random text from your page.",
        "fix": "Add <meta name='description' content='...'> with a compelling 150-160 character summary.",
        "effort": "Easy",
        "category": "seo"
    },
    "missing_skip_link": {
        "title": "No Skip-to-Content Link",
        "what": "Keyboard users must tab through entire navigation on every page.",
        "impact": "Frustrating for users who can't use a mouse. Required for WCAG accessibility compliance.",
        "fix": "Add a visually hidden 'Skip to main content' link at the top of each page.",
        "effort": "Easy",
        "category": "accessibility"
    },
    "buttons_no_name": {
        "title": "Buttons Without Accessible Names",
        "what": "Icon-only buttons have no text for screen readers to announce.",
        "impact": "Blind users hear 'button' with no indication of what it does.",
        "fix": "Add aria-label='Description' or visible text to all buttons.",
        "effort": "Easy",
        "category": "accessibility"
    },
    "missing_viewport": {
        "title": "Missing Viewport Meta Tag",
        "what": "Page doesn't have responsive viewport configuration.",
        "impact": "Mobile users see a tiny, unreadable page. Over 50% of web traffic is mobile.",
        "fix": "Add <meta name='viewport' content='width=device-width, initial-scale=1'>.",
        "effort": "Easy",
        "category": "ux"
    },
    "multiple_h1": {
        "title": "Multiple H1 Headings",
        "what": "Page has more than one H1 heading, confusing document structure.",
        "impact": "Search engines may not understand the primary topic. Screen readers announce multiple 'main' headings.",
        "fix": "Keep exactly one H1 per page. Use H2-H6 for subheadings.",
        "effort": "Easy",
        "category": "seo"
    }
}


def calculate_roi(industry: str, monthly_visitors: Optional[int], issues: list) -> Dict[str, Any]:
    """Calculate estimated revenue impact based on industry benchmarks"""
    if not monthly_visitors or monthly_visitors <= 0:
        return None

    # Industry benchmarks
    BENCHMARKS = {
        "e-commerce": {
            "conversion_rate": 0.025,  # 2.5%
            "avg_order_value": 75,
        },
        "saas": {
            "trial_conversion": 0.15,  # 15% trial to paid
            "ltv": 500,
        },
        "b2b": {
            "lead_value": 250,
            "form_conversion": 0.03,  # 3%
        },
        "content": {
            "rpm": 5,  # $5 per 1000 views
        },
        "general": {
            "conversion_rate": 0.02,
            "avg_value": 50,
        }
    }

    bench = BENCHMARKS.get(industry, BENCHMARKS["general"])

    # Count critical/high issues
    critical_count = sum(1 for i in issues if "critical" in str(i).lower() or "console error" in str(i).lower())
    high_count = sum(1 for i in issues if "missing" in str(i).lower() and "critical" not in str(i).lower())

    # Calculate impact based on industry
    if industry == "e-commerce":
        baseline_revenue = monthly_visitors * bench["conversion_rate"] * bench["avg_order_value"]
        loss_rate = 0.05 + (critical_count * 0.02) + (high_count * 0.005)
        estimated_recovery = baseline_revenue * min(loss_rate, 0.25)
    elif industry == "saas":
        baseline_trials = monthly_visitors * 0.05
        baseline_revenue = baseline_trials * bench["trial_conversion"] * bench["ltv"]
        loss_rate = 0.03 + (critical_count * 0.015) + (high_count * 0.005)
        estimated_recovery = baseline_revenue * min(loss_rate, 0.20)
    elif industry == "b2b":
        baseline_leads = monthly_visitors * bench["form_conversion"]
        baseline_revenue = baseline_leads * bench["lead_value"]
        loss_rate = 0.04 + (critical_count * 0.02) + (high_count * 0.005)
        estimated_recovery = baseline_revenue * min(loss_rate, 0.25)
    elif industry == "content":
        baseline_revenue = (monthly_visitors / 1000) * bench["rpm"]
        loss_rate = 0.10 + (critical_count * 0.05)
        estimated_recovery = baseline_revenue * min(loss_rate, 0.30)
    else:
        baseline_revenue = monthly_visitors * bench["conversion_rate"] * bench["avg_value"]
        loss_rate = 0.05 + (critical_count * 0.02) + (high_count * 0.005)
        estimated_recovery = baseline_revenue * min(loss_rate, 0.20)

    return {
        "estimated_revenue_recovery": int(estimated_recovery),
        "conversion_improvement": round(loss_rate * 100, 1),
        "users_impacted": int(monthly_visitors * 0.15)
    }


def get_score_color(score: float) -> str:
    """Get color class for score value"""
    if score >= 8:
        return "#10B981"  # Green
    elif score >= 5:
        return "#F59E0B"  # Yellow/Orange
    else:
        return "#EF4444"  # Red


def get_score_label(score: float) -> str:
    """Get label for score value"""
    if score >= 8:
        return "Good"
    elif score >= 5:
        return "Needs Work"
    else:
        return "Critical"


def categorize_issue(issue_text: str) -> Dict[str, str]:
    """Categorize an issue and get its impact info"""
    issue_lower = issue_text.lower()

    if "console error" in issue_lower or "javascript" in issue_lower:
        return {**ISSUE_IMPACTS["console_errors"], "severity": "critical"}
    elif "missing alt" in issue_lower or "alt text" in issue_lower:
        return {**ISSUE_IMPACTS["missing_alt"], "severity": "high"}
    elif "missing title" in issue_lower or "title tag" in issue_lower:
        return {**ISSUE_IMPACTS["missing_title"], "severity": "high"}
    elif "missing meta" in issue_lower or "meta description" in issue_lower:
        return {**ISSUE_IMPACTS["missing_meta"], "severity": "medium"}
    elif "no h1" in issue_lower or "missing h1" in issue_lower:
        return {**ISSUE_IMPACTS["missing_h1"], "severity": "medium"}
    elif "multiple h1" in issue_lower:
        return {**ISSUE_IMPACTS["multiple_h1"], "severity": "low"}
    elif "label" in issue_lower and ("form" in issue_lower or "input" in issue_lower):
        return {**ISSUE_IMPACTS["missing_labels"], "severity": "high"}
    elif "skip" in issue_lower:
        return {**ISSUE_IMPACTS["missing_skip_link"], "severity": "medium"}
    elif "button" in issue_lower and ("aria" in issue_lower or "accessible" in issue_lower or "name" in issue_lower):
        return {**ISSUE_IMPACTS["buttons_no_name"], "severity": "medium"}
    elif "viewport" in issue_lower:
        return {**ISSUE_IMPACTS["missing_viewport"], "severity": "high"}
    elif "slow" in issue_lower or "load time" in issue_lower:
        return {**ISSUE_IMPACTS["slow_load"], "severity": "high"}
    else:
        return {
            "title": "Issue Detected",
            "what": issue_text,
            "impact": "This issue may affect user experience or site performance.",
            "fix": "Review and address this issue based on best practices.",
            "effort": "Varies",
            "category": "general",
            "severity": "medium"
        }


def generate_comprehensive_report(data: ExportRequest) -> str:
    """Generate a comprehensive, personalized HTML audit report"""

    company_name = escape(data.company_name)
    industry = data.industry or "general"
    url = escape(data.url)
    timestamp = data.timestamp
    scores = data.scores if isinstance(data.scores, dict) else {}
    # Ensure score_feedback is a dict, not a list
    score_feedback = data.score_feedback if isinstance(data.score_feedback, dict) else {}
    issues = data.issues if isinstance(data.issues, list) else []
    recommendations = data.recommendations if isinstance(data.recommendations, list) else []
    confidence = data.confidence if isinstance(data.confidence, dict) else {"level": "Medium", "score": 75, "color": "yellow"}
    # Ensure pages_crawled is a list of dicts
    pages_crawled = [p for p in (data.pages_crawled or []) if isinstance(p, dict)]
    total_pages = data.total_pages or len(pages_crawled)
    monthly_visitors = data.monthly_visitors

    # Calculate ROI if visitors provided
    roi = calculate_roi(industry, monthly_visitors, issues)

    # Get industry-specific impacts
    industry_impacts = INDUSTRY_IMPACTS.get(industry, INDUSTRY_IMPACTS["general"])

    # Format date
    try:
        date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        formatted_date = date_obj.strftime("%B %d, %Y")
    except:
        formatted_date = timestamp[:10]

    # Categorize and sort issues
    categorized_issues = []
    for issue in issues:
        if isinstance(issue, str):
            cat = categorize_issue(issue)
            cat["original"] = issue
            # Extract page URL if present
            if issue.startswith("[") and "]" in issue:
                page_url = issue[1:issue.index("]")]
                cat["page"] = page_url
            categorized_issues.append(cat)

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    categorized_issues.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 2))

    # Count by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in categorized_issues:
        sev = issue.get("severity", "medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # Generate score breakdown HTML
    def score_breakdown_html(category: str, score: float, feedback: list) -> str:
        color = get_score_color(score)
        html = f'''
        <div class="score-detail">
            <div class="score-header">
                <span class="score-name">{category}</span>
                <span class="score-value" style="color: {color}">{score}/10</span>
            </div>
            <div class="score-bar">
                <div class="score-fill" style="width: {score * 10}%; background: {color}"></div>
            </div>
        '''
        if feedback:
            html += '<ul class="deductions">'
            for item in feedback:
                # Handle different feedback formats
                if isinstance(item, dict):
                    deduction = item.get("deduction", "")
                    reason = item.get("reason", "")
                    html += f'<li>{deduction} pts: {escape(str(reason))}</li>'
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    # Handle [deduction, reason] format
                    html += f'<li>{item[0]} pts: {escape(str(item[1]))}</li>'
                elif isinstance(item, str):
                    # Handle string format
                    html += f'<li>{escape(item)}</li>'
            html += '</ul>'
        html += '</div>'
        return html

    # Generate issue cards HTML
    def issue_card_html(issue: dict, idx: int) -> str:
        severity = issue.get("severity", "medium")
        severity_colors = {
            "critical": "#EF4444",
            "high": "#F97316",
            "medium": "#F59E0B",
            "low": "#10B981"
        }
        color = severity_colors.get(severity, "#F59E0B")

        # Get industry-specific impact if available
        issue_type = None
        for key in ["console_errors", "missing_alt", "missing_title", "missing_meta", "missing_h1", "missing_labels", "slow_load"]:
            if key in issue.get("title", "").lower().replace(" ", "_") or key.replace("_", " ") in issue.get("title", "").lower():
                issue_type = key
                break

        industry_impact = ""
        if issue_type and issue_type in industry_impacts:
            industry_impact = f'<p class="industry-impact"><strong>For your {industry.replace("-", " ")} business:</strong> {industry_impacts[issue_type]}</p>'

        page_info = ""
        if issue.get("page"):
            page_info = f'<span class="issue-location">Found on: {escape(issue["page"])}</span>'

        return f'''
        <div class="issue-card" style="border-left: 4px solid {color}">
            <div class="issue-header">
                <span class="severity-badge" style="background: {color}">{severity.upper()}</span>
                <span class="issue-title">{escape(issue.get("title", "Issue"))}</span>
            </div>
            <div class="issue-body">
                <p class="issue-what"><strong>What this means:</strong> {escape(issue.get("what", ""))}</p>
                <p class="issue-impact"><strong>Business Impact for {company_name}:</strong> {escape(issue.get("impact", ""))}</p>
                {industry_impact}
            </div>
            <div class="issue-meta">
                {page_info}
                <span class="issue-effort">Fix Effort: {issue.get("effort", "Medium")}</span>
            </div>
            <div class="issue-fix">
                <strong>How to fix:</strong> {escape(issue.get("fix", ""))}
            </div>
        </div>
        '''

    # Generate recommendation cards HTML
    def rec_card_html(rec: str, idx: int) -> str:
        return f'''
        <div class="rec-card">
            <div class="rec-number">{idx + 1}</div>
            <div class="rec-content">
                <p class="rec-text">{escape(rec)}</p>
            </div>
        </div>
        '''

    # Generate pages table HTML
    pages_html = ""
    if pages_crawled:
        pages_html = '''
        <table class="data-table">
            <thead>
                <tr>
                    <th>Page</th>
                    <th>Title</th>
                    <th>Load Time</th>
                    <th>Issues</th>
                </tr>
            </thead>
            <tbody>
        '''
        for page in pages_crawled[:20]:  # Limit to 20 pages
            load_time = page.get("load_time_ms", 0)
            load_color = "#10B981" if load_time < 2000 else "#F59E0B" if load_time < 4000 else "#EF4444"
            pages_html += f'''
                <tr>
                    <td class="page-url">{escape(page.get("url", "")[-50:])}</td>
                    <td>{escape(page.get("title", "No title")[:40])}</td>
                    <td style="color: {load_color}">{load_time:.0f}ms</td>
                    <td>{page.get("issues_count", 0)}</td>
                </tr>
            '''
        pages_html += '</tbody></table>'

    # ROI section HTML
    roi_html = ""
    if roi:
        roi_html = f'''
        <section class="section" id="roi">
            <h2>Estimated ROI for {company_name}</h2>
            <div class="roi-callout">
                <p class="roi-headline">Potential Monthly Impact</p>
                <div class="roi-stats">
                    <div class="roi-stat">
                        <div class="roi-value">${roi["estimated_revenue_recovery"]:,}</div>
                        <div class="roi-label">Potential Recovery</div>
                    </div>
                    <div class="roi-stat">
                        <div class="roi-value">{roi["conversion_improvement"]}%</div>
                        <div class="roi-label">Conversion Lift</div>
                    </div>
                    <div class="roi-stat">
                        <div class="roi-value">{roi["users_impacted"]:,}</div>
                        <div class="roi-label">Users Affected</div>
                    </div>
                </div>
                <p class="roi-methodology">
                    <strong>How we calculated this:</strong> Based on {monthly_visitors:,} monthly visitors,
                    industry benchmarks for {industry.replace("-", " ")} websites, and the severity of issues found.
                </p>
            </div>
        </section>
        '''

    # Bottom line message based on scores and issues
    avg_score = (scores.get("ux", 0) + scores.get("performance", 0) + scores.get("accessibility", 0) + scores.get("seo", 0)) / 4
    if avg_score >= 8:
        bottom_line = f"{company_name}'s website performs well overall. Focus on the {len(issues)} minor improvements identified to achieve excellence."
    elif avg_score >= 6:
        bottom_line = f"{company_name}'s website has solid foundations but {severity_counts['critical'] + severity_counts['high']} significant issues need attention. Addressing these will improve user experience and conversions."
    else:
        bottom_line = f"{company_name}'s website has {severity_counts['critical']} critical and {severity_counts['high']} high-priority issues that are likely impacting business metrics. Immediate action is recommended."

    # Generate the full HTML report
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UX & Performance Audit - {company_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #F8FAFC;
            color: #1E293B;
            line-height: 1.6;
        }}

        /* Navigation */
        .nav {{
            position: sticky;
            top: 0;
            background: #0F172A;
            padding: 16px 24px;
            display: flex;
            gap: 24px;
            z-index: 100;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        .nav a {{
            color: #94A3B8;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: color 0.2s;
        }}
        .nav a:hover {{ color: #F8FAFC; }}

        /* Cover */
        .cover {{
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: white;
            padding: 80px 40px;
            text-align: center;
        }}
        .cover-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #EF4444, #F97316);
            color: white;
            padding: 8px 24px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 24px;
        }}
        .cover h1 {{
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 8px;
        }}
        .cover h1 span {{
            display: block;
            font-size: 24px;
            font-weight: 400;
            color: #94A3B8;
            margin-top: 8px;
        }}
        .cover-subtitle {{
            color: #64748B;
            margin-bottom: 48px;
        }}
        .cover-stats {{
            display: flex;
            justify-content: center;
            gap: 32px;
            flex-wrap: wrap;
        }}
        .cover-stat {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px 40px;
            min-width: 140px;
        }}
        .cover-stat-value {{
            font-size: 42px;
            font-weight: 800;
        }}
        .cover-stat-label {{
            color: #94A3B8;
            font-size: 14px;
            margin-top: 4px;
        }}

        /* Sections */
        .section {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 60px 24px;
        }}
        .section h2 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 24px;
            color: #0F172A;
        }}
        .section-intro {{
            color: #64748B;
            margin-bottom: 24px;
        }}

        /* Bottom Line Box */
        .bottom-line {{
            background: linear-gradient(135deg, #FEF3C7, #FDE68A);
            border-left: 4px solid #F59E0B;
            padding: 24px;
            border-radius: 0 12px 12px 0;
            margin: 32px 0;
        }}
        .bottom-line.success {{
            background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
            border-left-color: #10B981;
        }}
        .bottom-line h4 {{
            font-size: 18px;
            margin-bottom: 8px;
        }}

        /* Data Tables */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .data-table th, .data-table td {{
            padding: 16px;
            text-align: left;
            border-bottom: 1px solid #E2E8F0;
        }}
        .data-table th {{
            background: #F1F5F9;
            font-weight: 600;
            color: #475569;
            font-size: 14px;
        }}
        .data-table td {{ font-size: 14px; }}
        .page-url {{
            font-family: monospace;
            font-size: 12px;
            color: #64748B;
        }}

        /* Score Details */
        .scores-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin: 24px 0;
        }}
        .score-detail {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .score-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .score-name {{
            font-weight: 600;
            font-size: 16px;
        }}
        .score-value {{
            font-size: 24px;
            font-weight: 800;
        }}
        .score-bar {{
            height: 8px;
            background: #E2E8F0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .score-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        .deductions {{
            margin-top: 16px;
            padding-left: 20px;
            font-size: 13px;
            color: #64748B;
        }}
        .deductions li {{ margin-bottom: 4px; }}

        /* Issue Cards */
        .issue-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .issue-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .severity-badge {{
            color: white;
            padding: 4px 12px;
            border-radius: 100px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .issue-title {{
            font-weight: 600;
            font-size: 18px;
        }}
        .issue-body p {{
            margin-bottom: 12px;
            color: #475569;
        }}
        .industry-impact {{
            background: #FEF3C7;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
        }}
        .issue-meta {{
            display: flex;
            gap: 24px;
            margin: 16px 0;
            font-size: 13px;
            color: #64748B;
        }}
        .issue-fix {{
            background: #F1F5F9;
            padding: 16px;
            border-radius: 8px;
            font-size: 14px;
        }}

        /* Recommendation Cards */
        .rec-card {{
            display: flex;
            gap: 16px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            align-items: flex-start;
        }}
        .rec-number {{
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #EF4444, #F97316);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex-shrink: 0;
        }}
        .rec-text {{
            color: #334155;
            font-size: 15px;
        }}

        /* ROI Section */
        .roi-callout {{
            background: linear-gradient(135deg, #0F172A, #1E293B);
            color: white;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
        }}
        .roi-headline {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #94A3B8;
            margin-bottom: 24px;
        }}
        .roi-stats {{
            display: flex;
            justify-content: center;
            gap: 48px;
            flex-wrap: wrap;
            margin-bottom: 24px;
        }}
        .roi-stat {{ text-align: center; }}
        .roi-value {{
            font-size: 36px;
            font-weight: 800;
            color: #10B981;
        }}
        .roi-label {{
            color: #94A3B8;
            font-size: 14px;
            margin-top: 4px;
        }}
        .roi-methodology {{
            color: #64748B;
            font-size: 13px;
            max-width: 600px;
            margin: 0 auto;
        }}

        /* KPI Table */
        .kpi-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
        }}
        .kpi-table th, .kpi-table td {{
            padding: 16px;
            text-align: center;
            border-bottom: 1px solid #E2E8F0;
        }}
        .kpi-table th {{ background: #F1F5F9; font-weight: 600; }}
        .kpi-current {{ color: #EF4444; font-weight: 600; }}
        .kpi-target {{ color: #10B981; font-weight: 600; }}

        /* Footer */
        .footer {{
            background: #0F172A;
            color: #94A3B8;
            text-align: center;
            padding: 40px 24px;
            font-size: 14px;
        }}
        .footer a {{
            color: #F97316;
            text-decoration: none;
        }}

        /* Chart Container */
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin: 24px 0;
        }}

        /* Print Styles */
        @media print {{
            .nav {{ display: none; }}
            .cover {{ padding: 40px 20px; }}
            .section {{ padding: 30px 20px; }}
            .issue-card, .rec-card {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <a href="#summary">Summary</a>
        <a href="#scores">Scores</a>
        <a href="#issues">Issues</a>
        <a href="#recommendations">Action Plan</a>
        {"<a href='#roi'>ROI</a>" if roi else ""}
        <a href="#pages">Pages</a>
    </nav>

    <section class="cover">
        <div class="cover-badge">Data-Driven UX Audit</div>
        <h1>{company_name}<span>Website Performance Analysis</span></h1>
        <p class="cover-subtitle">Prepared exclusively for {company_name} | {formatted_date}</p>
        <div class="cover-stats">
            <div class="cover-stat">
                <div class="cover-stat-value" style="color: {get_score_color(scores.get('ux', 0))}">{scores.get('ux', 0)}/10</div>
                <div class="cover-stat-label">UX Score</div>
            </div>
            <div class="cover-stat">
                <div class="cover-stat-value" style="color: {get_score_color(scores.get('performance', 0))}">{scores.get('performance', 0)}/10</div>
                <div class="cover-stat-label">Performance</div>
            </div>
            <div class="cover-stat">
                <div class="cover-stat-value" style="color: {get_score_color(scores.get('accessibility', 0))}">{scores.get('accessibility', 0)}/10</div>
                <div class="cover-stat-label">Accessibility</div>
            </div>
            <div class="cover-stat">
                <div class="cover-stat-value" style="color: {get_score_color(scores.get('seo', 0))}">{scores.get('seo', 0)}/10</div>
                <div class="cover-stat-label">SEO</div>
            </div>
        </div>
    </section>

    <section class="section" id="summary">
        <h2>Executive Summary for {company_name}</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Score</th>
                    <th>Assessment</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>User Experience (UX)</td>
                    <td style="color: {get_score_color(scores.get('ux', 0))}; font-weight: 600">{scores.get('ux', 0)}/10</td>
                    <td>{get_score_label(scores.get('ux', 0))}</td>
                </tr>
                <tr>
                    <td>Performance</td>
                    <td style="color: {get_score_color(scores.get('performance', 0))}; font-weight: 600">{scores.get('performance', 0)}/10</td>
                    <td>{get_score_label(scores.get('performance', 0))}</td>
                </tr>
                <tr>
                    <td>Accessibility</td>
                    <td style="color: {get_score_color(scores.get('accessibility', 0))}; font-weight: 600">{scores.get('accessibility', 0)}/10</td>
                    <td>{get_score_label(scores.get('accessibility', 0))}</td>
                </tr>
                <tr>
                    <td>SEO</td>
                    <td style="color: {get_score_color(scores.get('seo', 0))}; font-weight: 600">{scores.get('seo', 0)}/10</td>
                    <td>{get_score_label(scores.get('seo', 0))}</td>
                </tr>
            </tbody>
        </table>

        <div class="bottom-line">
            <h4>The Bottom Line for {company_name}</h4>
            <p>{bottom_line}</p>
        </div>
    </section>

    <section class="section" id="scores">
        <h2>Score Breakdown</h2>
        <div class="chart-container">
            <canvas id="scoresChart" height="200"></canvas>
        </div>
        <div class="scores-grid">
            {score_breakdown_html("User Experience", scores.get("ux", 0), score_feedback.get("ux", []))}
            {score_breakdown_html("Performance", scores.get("performance", 0), score_feedback.get("performance", []))}
            {score_breakdown_html("Accessibility", scores.get("accessibility", 0), score_feedback.get("accessibility", []))}
            {score_breakdown_html("SEO", scores.get("seo", 0), score_feedback.get("seo", []))}
        </div>
    </section>

    <section class="section" id="issues">
        <h2>Issues Found on {company_name}'s Website ({len(categorized_issues)} total)</h2>
        <p class="section-intro">
            We found <strong style="color: #EF4444">{severity_counts['critical']} critical</strong>,
            <strong style="color: #F97316">{severity_counts['high']} high</strong>,
            <strong style="color: #F59E0B">{severity_counts['medium']} medium</strong>, and
            <strong style="color: #10B981">{severity_counts['low']} low</strong> priority issues.
        </p>
        {''.join(issue_card_html(issue, i) for i, issue in enumerate(categorized_issues[:15]))}
        {f'<p class="section-intro"><em>...and {len(categorized_issues) - 15} more issues</em></p>' if len(categorized_issues) > 15 else ''}
    </section>

    <section class="section" id="recommendations">
        <h2>Action Plan for {company_name}</h2>
        <p class="section-intro">Based on our analysis, here are the prioritized actions to improve your website:</p>
        {''.join(rec_card_html(rec, i) for i, rec in enumerate(recommendations[:10]))}
    </section>

    {roi_html}

    <section class="section" id="pages">
        <h2>Pages Analyzed ({total_pages})</h2>
        {pages_html if pages_html else '<p>Single page analyzed.</p>'}
    </section>

    <section class="section">
        <h2>Success Metrics for {company_name}</h2>
        <table class="data-table kpi-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Current</th>
                    <th>30-Day Target</th>
                    <th>90-Day Target</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>UX Score</td>
                    <td class="kpi-current">{scores.get('ux', 0)}/10</td>
                    <td class="kpi-target">{min(10, scores.get('ux', 0) + 1.5):.1f}/10</td>
                    <td class="kpi-target">{min(10, scores.get('ux', 0) + 3):.1f}/10</td>
                </tr>
                <tr>
                    <td>Performance Score</td>
                    <td class="kpi-current">{scores.get('performance', 0)}/10</td>
                    <td class="kpi-target">{min(10, scores.get('performance', 0) + 1):.1f}/10</td>
                    <td class="kpi-target">{min(10, scores.get('performance', 0) + 2):.1f}/10</td>
                </tr>
                <tr>
                    <td>Accessibility Score</td>
                    <td class="kpi-current">{scores.get('accessibility', 0)}/10</td>
                    <td class="kpi-target">{min(10, scores.get('accessibility', 0) + 2):.1f}/10</td>
                    <td class="kpi-target">{min(10, scores.get('accessibility', 0) + 3.5):.1f}/10</td>
                </tr>
                <tr>
                    <td>SEO Score</td>
                    <td class="kpi-current">{scores.get('seo', 0)}/10</td>
                    <td class="kpi-target">{min(10, scores.get('seo', 0) + 1.5):.1f}/10</td>
                    <td class="kpi-target">{min(10, scores.get('seo', 0) + 2.5):.1f}/10</td>
                </tr>
                <tr>
                    <td>Critical Issues</td>
                    <td class="kpi-current">{severity_counts['critical']}</td>
                    <td class="kpi-target">0</td>
                    <td class="kpi-target">0</td>
                </tr>
            </tbody>
        </table>

        <div class="bottom-line success">
            <h4>Recommended Next Step</h4>
            <p>{recommendations[0] if recommendations else 'Review the issues identified and prioritize fixes based on business impact.'}</p>
        </div>
    </section>

    <footer class="footer">
        <p>Generated by <a href="#">Weaver Pro</a> | {formatted_date}</p>
        <p>Confidence: {confidence.get('level', 'Medium')} ({confidence.get('score', 75)}%)</p>
        <p style="margin-top: 16px; font-size: 12px; color: #64748B;">
            This report was prepared exclusively for {company_name}. Analysis based on {total_pages} page(s) crawled from {url}.
        </p>
    </footer>

    <script>
        // Scores Chart
        const ctx = document.getElementById('scoresChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: ['UX', 'Performance', 'Accessibility', 'SEO'],
                datasets: [{{
                    label: 'Score',
                    data: [{scores.get('ux', 0)}, {scores.get('performance', 0)}, {scores.get('accessibility', 0)}, {scores.get('seo', 0)}],
                    backgroundColor: [
                        '{get_score_color(scores.get("ux", 0))}',
                        '{get_score_color(scores.get("performance", 0))}',
                        '{get_score_color(scores.get("accessibility", 0))}',
                        '{get_score_color(scores.get("seo", 0))}'
                    ],
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 10,
                        grid: {{ color: '#E2E8F0' }}
                    }},
                    x: {{
                        grid: {{ display: false }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    return html


# ============================================================================
# Real Website Audit Functions
# ============================================================================

def analyze_single_page(page, url: str, parsed_base_url) -> Dict[str, Any]:
    """Analyze a single page that's already loaded in Playwright"""
    page_data = {
        "url": url,
        "title": None,
        "meta_description": None,
        "headings": {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0},
        "links": {"internal": [], "external": 0},
        "images": {"total": 0, "missing_alt": 0},
        "forms": {"total": 0, "missing_labels": 0},
        "buttons": {"total": 0, "missing_aria": 0},
        "navigation": [],
        "console_errors": [],
        "load_time_ms": 0,
    }
    issues = []
    recommendations = []

    # Get page title
    page_data["title"] = page.title()
    if not page_data["title"]:
        issues.append(f"[{url}] Page is missing a title tag")
        recommendations.append("Add a descriptive <title> tag for better SEO and browser tab display")

    # Check meta description
    meta_desc = page.query_selector('meta[name="description"]')
    if meta_desc:
        page_data["meta_description"] = meta_desc.get_attribute("content")
    else:
        issues.append(f"[{url}] Page is missing meta description")
        recommendations.append("Add a <meta name='description'> tag to improve search engine snippets")

    # Analyze headings
    for level in range(1, 7):
        headings = page.query_selector_all(f"h{level}")
        page_data["headings"][f"h{level}"] = len(headings)

    if page_data["headings"]["h1"] == 0:
        issues.append(f"[{url}] Page has no H1 heading")
        recommendations.append("Add exactly one H1 heading to define the main topic of each page")
    elif page_data["headings"]["h1"] > 1:
        issues.append(f"[{url}] Page has {page_data['headings']['h1']} H1 headings (should have exactly 1)")
        recommendations.append("Use only one H1 heading per page - use H2-H6 for subheadings")

    # Analyze links and collect internal URLs for crawling
    links = page.query_selector_all("a[href]")
    internal_urls = set()
    for link in links:
        href = link.get_attribute("href")
        if href:
            # Normalize URL
            if href.startswith("/"):
                full_url = f"{parsed_base_url.scheme}://{parsed_base_url.netloc}{href}"
                internal_urls.add(full_url.split("#")[0].split("?")[0])  # Remove fragments and query
            elif parsed_base_url.netloc in href and href.startswith("http"):
                internal_urls.add(href.split("#")[0].split("?")[0])
            elif href.startswith("http"):
                page_data["links"]["external"] += 1

    page_data["links"]["internal"] = list(internal_urls)

    # Analyze images for alt text
    images = page.query_selector_all("img")
    page_data["images"]["total"] = len(images)
    for img in images:
        alt = img.get_attribute("alt")
        if not alt or alt.strip() == "":
            page_data["images"]["missing_alt"] += 1

    if page_data["images"]["missing_alt"] > 0:
        issues.append(f"[{url}] {page_data['images']['missing_alt']} images missing alt text")
        recommendations.append(f"Add descriptive alt text to {page_data['images']['missing_alt']} images for better accessibility and SEO")

    # Analyze forms
    forms = page.query_selector_all("form")
    page_data["forms"]["total"] = len(forms)
    inputs = page.query_selector_all("input:not([type='hidden']):not([type='submit'])")
    for inp in inputs:
        input_id = inp.get_attribute("id")
        if input_id:
            label = page.query_selector(f'label[for="{input_id}"]')
            if not label:
                page_data["forms"]["missing_labels"] += 1

    if page_data["forms"]["missing_labels"] > 0:
        issues.append(f"[{url}] {page_data['forms']['missing_labels']} form inputs missing labels")
        recommendations.append(f"Add <label> elements to {page_data['forms']['missing_labels']} form inputs for better accessibility")

    # Analyze buttons for aria-labels
    buttons = page.query_selector_all("button")
    page_data["buttons"]["total"] = len(buttons)
    for btn in buttons:
        text = btn.inner_text()
        aria_label = btn.get_attribute("aria-label")
        if (not text or text.strip() == "") and not aria_label:
            page_data["buttons"]["missing_aria"] += 1

    if page_data["buttons"]["missing_aria"] > 0:
        issues.append(f"[{url}] {page_data['buttons']['missing_aria']} buttons without accessible names")
        recommendations.append(f"Add aria-label or visible text to {page_data['buttons']['missing_aria']} buttons for screen reader users")

    # Find navigation elements
    nav_elements = page.query_selector_all("nav a, [role='navigation'] a, header a, aside a, [data-sidebar] a, .sidebar a")
    nav_items = []
    for nav in nav_elements[:10]:
        text = nav.inner_text()
        href = nav.get_attribute("href")
        if text and text.strip():
            nav_items.append({"text": text.strip(), "href": href})
    page_data["navigation"] = nav_items

    # Check for skip link (only on first/main page)
    skip_link = page.query_selector('a[href="#main"], a[href="#content"], .skip-link, [class*="skip"]')
    if not skip_link:
        issues.append(f"[{url}] No skip-to-content link found")
        recommendations.append("Add a skip-to-content link for keyboard navigation accessibility")

    # Check for viewport meta
    viewport = page.query_selector('meta[name="viewport"]')
    if not viewport:
        issues.append(f"[{url}] Missing viewport meta tag")
        recommendations.append("Add <meta name='viewport'> tag for mobile responsiveness")

    return {
        "page_data": page_data,
        "issues": issues,
        "recommendations": recommendations,
        "internal_urls": list(internal_urls)
    }


def analyze_page_sync(url: str, full: bool = False, max_pages: int = 10) -> Dict[str, Any]:
    """Synchronously crawl and analyze a webpage (or full site) using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "Playwright not installed. Run: pip install playwright && python -m playwright install chromium"}

    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
        print(f"[Crawl] Added https:// prefix, URL is now: {url}")

    all_issues = []
    all_recommendations = []
    pages_crawled = []

    # Aggregated page data
    aggregated_data = {
        "title": None,
        "meta_description": None,
        "headings": {"h1": 0, "h2": 0, "h3": 0, "h4": 0, "h5": 0, "h6": 0},
        "links": {"internal": 0, "external": 0, "broken": []},
        "images": {"total": 0, "missing_alt": 0},
        "forms": {"total": 0, "missing_labels": 0},
        "buttons": {"total": 0, "missing_aria": 0},
        "navigation": [],
        "console_errors": [],
        "load_time_ms": 0,
        "accessibility_issues": [],
        "pages_crawled": 0,
    }

    parsed_base_url = urlparse(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="WeaverPro-Audit/1.0"
        )
        page = context.new_page()

        # Track console errors across all pages with details
        console_errors = []
        def handle_console(msg):
            if msg.type == "error":
                error_info = {
                    "message": msg.text[:200],  # Limit length
                    "url": page.url,
                    "type": msg.type
                }
                console_errors.append(error_info)
        page.on("console", handle_console)

        # URLs to crawl and already visited
        urls_to_crawl = [url]
        visited_urls = set()

        # Determine max pages based on full mode
        crawl_limit = max_pages if full else 1

        print(f"[Crawl] Starting crawl with full={full}, max_pages={max_pages}, crawl_limit={crawl_limit}")
        print(f"[Crawl] Initial URLs to crawl: {urls_to_crawl}")

        try:
            while urls_to_crawl and len(visited_urls) < crawl_limit:
                current_url = urls_to_crawl.pop(0)
                print(f"[Crawl] Processing: {current_url} (visited: {len(visited_urls)}/{crawl_limit})")

                # Skip if already visited
                if current_url in visited_urls:
                    print(f"[Crawl] Skipping (already visited): {current_url}")
                    continue

                # Skip non-HTML resources
                if any(current_url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.svg', '.css', '.js', '.ico']):
                    print(f"[Crawl] Skipping (non-HTML): {current_url}")
                    continue

                visited_urls.add(current_url)

                try:
                    start_time = datetime.now()
                    # Use domcontentloaded for faster initial check, then wait for networkidle
                    try:
                        page.goto(current_url, wait_until="domcontentloaded", timeout=15000)
                        # Give a bit more time for network requests but don't wait forever
                        page.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        # If networkidle times out, just proceed with domcontentloaded
                        pass
                    load_time = (datetime.now() - start_time).total_seconds() * 1000

                    # Analyze the page
                    result = analyze_single_page(page, current_url, parsed_base_url)

                    # Store page info
                    pages_crawled.append({
                        "url": current_url,
                        "title": result["page_data"]["title"],
                        "load_time_ms": load_time,
                        "issues_count": len(result["issues"])
                    })

                    # Aggregate data
                    pg = result["page_data"]
                    if aggregated_data["title"] is None:
                        aggregated_data["title"] = pg["title"]
                        aggregated_data["meta_description"] = pg["meta_description"]
                        aggregated_data["navigation"] = pg["navigation"]

                    # Sum up counts
                    for h in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        aggregated_data["headings"][h] += pg["headings"][h]
                    aggregated_data["links"]["internal"] += len(pg["links"]["internal"])
                    aggregated_data["links"]["external"] += pg["links"]["external"]
                    aggregated_data["images"]["total"] += pg["images"]["total"]
                    aggregated_data["images"]["missing_alt"] += pg["images"]["missing_alt"]
                    aggregated_data["forms"]["total"] += pg["forms"]["total"]
                    aggregated_data["forms"]["missing_labels"] += pg["forms"]["missing_labels"]
                    aggregated_data["buttons"]["total"] += pg["buttons"]["total"]
                    aggregated_data["buttons"]["missing_aria"] += pg["buttons"]["missing_aria"]
                    aggregated_data["load_time_ms"] += load_time

                    # Collect issues
                    all_issues.extend(result["issues"])
                    all_recommendations.extend(result["recommendations"])

                    # Add discovered internal URLs to crawl queue (if full mode)
                    if full:
                        new_urls_added = 0
                        for internal_url in result["internal_urls"]:
                            if internal_url not in visited_urls and internal_url not in urls_to_crawl:
                                urls_to_crawl.append(internal_url)
                                new_urls_added += 1
                        print(f"[Crawl] Discovered {len(result['internal_urls'])} internal links, added {new_urls_added} new URLs to queue")
                        print(f"[Crawl] Queue now has {len(urls_to_crawl)} URLs pending")
                    else:
                        print(f"[Crawl] Full mode is OFF - not adding discovered links to queue")

                except Exception as e:
                    all_issues.append(f"[{current_url}] Error loading page: {str(e)[:100]}")

            aggregated_data["pages_crawled"] = len(visited_urls)
            aggregated_data["console_errors"] = console_errors
            print(f"[Crawl] COMPLETE: Crawled {len(visited_urls)} pages total")

            # Add console errors to issues with details
            if console_errors:
                all_issues.append(f"{len(console_errors)} JavaScript console errors detected across {len(visited_urls)} pages:")
                # Add unique error messages (deduplicated)
                seen_errors = set()
                for err in console_errors:
                    msg = err["message"]
                    if msg not in seen_errors and len(seen_errors) < 10:  # Limit to 10 unique errors
                        seen_errors.add(msg)
                        all_issues.append(f"  → JS Error: {msg}")
                if len(console_errors) > len(seen_errors):
                    all_issues.append(f"  → ... and {len(console_errors) - len(seen_errors)} more similar errors")
                all_recommendations.append("Fix JavaScript console errors to improve user experience and prevent broken functionality")

            # Deduplicate recommendations
            unique_recommendations = list(dict.fromkeys(all_recommendations))

        except Exception as e:
            all_issues.append(f"Error during site crawl: {str(e)[:100]}")
        finally:
            browser.close()

    return {
        "page_data": aggregated_data,
        "issues": all_issues,
        "recommendations": unique_recommendations,
        "pages_crawled": pages_crawled
    }


async def analyze_page_with_playwright(url: str, full: bool = False, max_pages: int = 20) -> Dict[str, Any]:
    """Run Playwright analysis in a thread to avoid event loop conflicts"""
    import concurrent.futures
    from functools import partial

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        func = partial(analyze_page_sync, url, full, max_pages)
        result = await loop.run_in_executor(pool, func)
    return result


def calculate_scores(page_data: Dict, issues: List[str], recommendations: List[str]) -> Dict[str, Any]:
    """Calculate audit scores based on real page analysis with detailed feedback"""

    # Track score breakdowns for feedback
    score_feedback = {
        "ux": [],
        "performance": [],
        "accessibility": [],
        "seo": []
    }

    # UX Score based on navigation, forms, and structure
    ux_score = 10.0
    if page_data["headings"]["h1"] == 0:
        ux_score -= 1.0
        score_feedback["ux"].append({"deduction": -1.0, "reason": "No H1 heading for document structure"})
    if page_data["headings"]["h1"] > 1:
        ux_score -= 0.5
        score_feedback["ux"].append({"deduction": -0.5, "reason": f"Multiple H1 headings ({page_data['headings']['h1']}) - should have exactly 1"})

    nav_count = len(page_data.get("navigation", []))
    if nav_count == 0:
        ux_score -= 1.5
        score_feedback["ux"].append({"deduction": -1.5, "reason": "No navigation links detected"})
        if "No clear navigation structure detected" not in issues:
            issues.append("No clear navigation structure detected")
            recommendations.append("Add a nav element with clear navigation links for better UX")
    elif nav_count < 3:
        ux_score -= 0.5
        score_feedback["ux"].append({"deduction": -0.5, "reason": f"Limited navigation (only {nav_count} links found)"})

    if page_data["forms"]["missing_labels"] > 0:
        deduction = min(2.0, page_data["forms"]["missing_labels"] * 0.5)
        ux_score -= deduction
        score_feedback["ux"].append({"deduction": -deduction, "reason": f"{page_data['forms']['missing_labels']} form inputs without labels"})

    if page_data["console_errors"]:
        deduction = min(2.0, len(page_data["console_errors"]) * 0.3)
        ux_score -= deduction
        score_feedback["ux"].append({"deduction": -deduction, "reason": f"{len(page_data['console_errors'])} JavaScript console errors"})

    # Performance Score based on load time
    perf_score = 10.0
    load_time = page_data.get("load_time_ms", 0)
    if load_time > 5000:
        perf_score -= 3.0
        score_feedback["performance"].append({"deduction": -3.0, "reason": f"Very slow load time ({load_time:.0f}ms)"})
        recommendations.append("Optimize page load time - consider lazy loading, code splitting, and image compression")
    elif load_time > 3000:
        perf_score -= 2.0
        score_feedback["performance"].append({"deduction": -2.0, "reason": f"Slow load time ({load_time:.0f}ms)"})
        recommendations.append("Improve page speed by optimizing images and reducing JavaScript bundle size")
    elif load_time > 2000:
        perf_score -= 1.0
        score_feedback["performance"].append({"deduction": -1.0, "reason": f"Moderate load time ({load_time:.0f}ms)"})
        recommendations.append("Consider performance optimizations like caching and CDN usage")
    elif load_time > 1000:
        perf_score -= 0.5
        score_feedback["performance"].append({"deduction": -0.5, "reason": f"Load time could be faster ({load_time:.0f}ms)"})

    # Accessibility Score
    a11y_score = 10.0
    if page_data["images"]["missing_alt"] > 0:
        deduction = min(3.0, page_data["images"]["missing_alt"] * 0.3)
        a11y_score -= deduction
        score_feedback["accessibility"].append({"deduction": -deduction, "reason": f"{page_data['images']['missing_alt']} images missing alt text"})
    if page_data["buttons"]["missing_aria"] > 0:
        deduction = min(2.0, page_data["buttons"]["missing_aria"] * 0.4)
        a11y_score -= deduction
        score_feedback["accessibility"].append({"deduction": -deduction, "reason": f"{page_data['buttons']['missing_aria']} buttons without accessible names"})
    if page_data["forms"]["missing_labels"] > 0:
        deduction = min(2.0, page_data["forms"]["missing_labels"] * 0.4)
        a11y_score -= deduction
        score_feedback["accessibility"].append({"deduction": -deduction, "reason": f"{page_data['forms']['missing_labels']} form inputs without labels"})
    # Check for skip link issue
    if any("skip" in issue.lower() for issue in issues):
        a11y_score -= 1.0
        score_feedback["accessibility"].append({"deduction": -1.0, "reason": "No skip-to-content link for keyboard users"})

    # SEO Score
    seo_score = 10.0
    if not page_data["title"]:
        seo_score -= 2.0
        score_feedback["seo"].append({"deduction": -2.0, "reason": "Missing page title"})
    if not page_data["meta_description"]:
        seo_score -= 2.0
        score_feedback["seo"].append({"deduction": -2.0, "reason": "Missing meta description"})
    if page_data["headings"]["h1"] == 0:
        seo_score -= 1.5
        score_feedback["seo"].append({"deduction": -1.5, "reason": "No H1 heading"})
    if page_data["images"]["missing_alt"] > 0:
        deduction = min(1.5, page_data["images"]["missing_alt"] * 0.2)
        seo_score -= deduction
        score_feedback["seo"].append({"deduction": -deduction, "reason": f"{page_data['images']['missing_alt']} images without alt text"})

    return {
        "scores": {
            "ux": max(0, min(10, round(ux_score, 1))),
            "performance": max(0, min(10, round(perf_score, 1))),
            "accessibility": max(0, min(10, round(a11y_score, 1))),
            "seo": max(0, min(10, round(seo_score, 1)))
        },
        "feedback": score_feedback
    }


def analyze_navigation_flow(page_data: Dict) -> Dict[str, Any]:
    """Analyze the navigation/funnel based on actual page elements"""
    nav_items = page_data.get("navigation", [])

    # Identify key flows based on navigation
    key_pages = []
    for item in nav_items:
        text = item.get("text", "").lower()
        if any(keyword in text for keyword in ["home", "about", "contact", "sign", "log", "register", "pricing", "product", "service"]):
            key_pages.append(item["text"])

    # Calculate completion rate based on page quality
    total_issues = len(page_data.get("console_errors", []))
    total_issues += page_data["images"]["missing_alt"]
    total_issues += page_data["forms"]["missing_labels"]
    total_issues += page_data["buttons"]["missing_aria"]

    # Higher quality = higher completion rate estimate
    base_rate = 85
    completion_rate = max(40, base_rate - (total_issues * 2))

    # Identify biggest drop-off based on actual page structure
    drop_off_step = None
    drop_off_pct = 0

    if page_data["forms"]["total"] > 0 and page_data["forms"]["missing_labels"] > 0:
        drop_off_step = "form_submission"
        drop_off_pct = int(page_data["forms"]["missing_labels"] / max(1, page_data["forms"]["total"]) * 30)
    elif page_data["console_errors"]:
        drop_off_step = "page_interaction"
        drop_off_pct = min(25, len(page_data["console_errors"]) * 5)
    elif page_data["buttons"]["missing_aria"] > 0:
        drop_off_step = "button_click"
        drop_off_pct = min(20, page_data["buttons"]["missing_aria"] * 3)

    result = {
        "completion_rate": completion_rate,
        "key_pages": key_pages[:5],
        "total_nav_items": len(nav_items)
    }

    if drop_off_step:
        result["biggest_drop_off"] = {
            "step": drop_off_step,
            "percentage": drop_off_pct
        }

    return result


# ============================================================================
# GitHub Code Audit Functions
# ============================================================================

async def analyze_github_repo(repo_url: str) -> Dict[str, Any]:
    """Analyze a GitHub repository for code quality and security"""
    # Parse GitHub URL
    match = re.match(r'https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/?', repo_url)
    if not match:
        return {"error": "Invalid GitHub URL format"}

    owner, repo = match.groups()
    repo = repo.rstrip('.git')

    async with httpx.AsyncClient() as client:
        # Fetch repo info
        try:
            repo_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=30.0
            )
            if repo_response.status_code == 404:
                return {"error": f"Repository not found: {owner}/{repo}"}
            repo_data = repo_response.json()
        except Exception as e:
            return {"error": f"Failed to fetch repository: {str(e)[:100]}"}

        # Fetch languages
        try:
            lang_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/languages",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=30.0
            )
            languages = list(lang_response.json().keys()) if lang_response.status_code == 200 else []
        except:
            languages = []

        # Fetch file tree (limited)
        try:
            tree_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{repo_data.get('default_branch', 'main')}?recursive=1",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=30.0
            )
            tree_data = tree_response.json() if tree_response.status_code == 200 else {"tree": []}
            files = [f for f in tree_data.get("tree", []) if f.get("type") == "blob"]
        except:
            files = []

        # Analyze for common issues
        issues = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        security_findings = []
        recommendations = []

        # Check for common security issues based on file names
        sensitive_files = []
        for f in files:
            path = f.get("path", "").lower()

            # Check for potential secrets
            if path.endswith(('.env', '.env.local', '.env.production')):
                if not path.startswith('.env.example'):
                    issues["critical"] += 1
                    security_findings.append({
                        "severity": "critical",
                        "title": "Potential secrets in repository",
                        "file": f.get("path"),
                        "description": "Environment files may contain sensitive credentials and should not be committed"
                    })

            if any(secret in path for secret in ['secret', 'credential', 'password', 'key.json', 'serviceaccount']):
                issues["high"] += 1
                security_findings.append({
                    "severity": "high",
                    "title": "Potentially sensitive file",
                    "file": f.get("path"),
                    "description": "File name suggests it may contain sensitive information"
                })

            # Check for lack of security configs
            if path in ['security.md', '.github/security.md', 'security_policy.md']:
                sensitive_files.append('security_policy')

        # Check for missing security policy
        if 'security_policy' not in sensitive_files and len(files) > 10:
            issues["low"] += 1
            recommendations.append("Add a SECURITY.md file to document security policies and vulnerability reporting")

        # Check for package lock files (dependency management)
        has_lock = any(f.get("path", "").lower() in ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'cargo.lock', 'go.sum'] for f in files)
        if not has_lock and len(files) > 5:
            issues["medium"] += 1
            recommendations.append("Add a lock file (package-lock.json, yarn.lock, etc.) for reproducible builds")

        # Check for tests
        has_tests = any('test' in f.get("path", "").lower() or 'spec' in f.get("path", "").lower() for f in files)
        if not has_tests and len(files) > 10:
            issues["medium"] += 1
            recommendations.append("Add automated tests to improve code quality and catch bugs early")

        # Check for CI/CD
        has_ci = any(f.get("path", "").startswith('.github/workflows/') or f.get("path", "") in ['.travis.yml', '.circleci/config.yml', 'Jenkinsfile'] for f in files)
        if not has_ci and len(files) > 10:
            issues["low"] += 1
            recommendations.append("Set up CI/CD pipelines for automated testing and deployment")

        # Check for README
        has_readme = any(f.get("path", "").lower() in ['readme.md', 'readme.txt', 'readme'] for f in files)
        if not has_readme:
            issues["low"] += 1
            recommendations.append("Add a README.md file to document the project")

        # Calculate scores
        total_files = len(files)
        lines_of_code = repo_data.get("size", 0) * 10  # Rough estimate

        # Security score
        security_score = 10.0
        security_score -= issues["critical"] * 2.5
        security_score -= issues["high"] * 1.5
        security_score -= issues["medium"] * 0.5
        security_score -= issues["low"] * 0.2

        # Code quality score
        quality_score = 10.0
        if not has_tests:
            quality_score -= 2.0
        if not has_ci:
            quality_score -= 1.0
        if not has_readme:
            quality_score -= 1.0
        if not has_lock:
            quality_score -= 1.0

        # Architecture score based on structure
        arch_score = 10.0
        if total_files < 3:
            arch_score -= 2.0
        if len(languages) == 0:
            arch_score -= 1.0

        # Performance score (based on repo metrics)
        perf_score = 10.0
        if repo_data.get("size", 0) > 100000:  # Very large repo
            perf_score -= 1.5
            recommendations.append("Consider splitting large codebase into smaller modules")

        return {
            "repo_url": repo_url,
            "repo_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "scores": {
                "security": max(0, min(10, round(security_score, 1))),
                "code_quality": max(0, min(10, round(quality_score, 1))),
                "architecture": max(0, min(10, round(arch_score, 1))),
                "performance": max(0, min(10, round(perf_score, 1)))
            },
            "summary": {
                "total_files": total_files,
                "languages": languages[:5],
                "lines_of_code": lines_of_code,
                "has_tests": has_tests,
                "has_ci": has_ci
            },
            "issues": issues,
            "security_findings": security_findings[:10],
            "recommendations": recommendations[:10]
        }


# ============================================================================
# App Setup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Weaver Pro API starting...")
    yield
    print("Weaver Pro API shutting down...")


app = FastAPI(
    title="Weaver Pro API",
    description="Backend API for Weaver Pro - Audit, Optimize, Build platforms",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# Website Audit Endpoints
# ============================================================================

@app.post("/api/audit", response_model=AuditResult)
async def run_audit(request: AuditRequest):
    """Run a real weaver audit on the specified URL"""
    url = request.url.strip()
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    # Ensure full is a boolean
    full_mode = bool(request.full)
    print(f"[Audit] URL: {url}, Full mode: {full_mode}, Max pages: {request.max_pages}")

    # Run real analysis
    analysis = await analyze_page_with_playwright(url, full_mode, request.max_pages)

    if "error" in analysis:
        raise HTTPException(status_code=500, detail=analysis["error"])

    page_data = analysis["page_data"]
    issues = analysis["issues"]
    recommendations = analysis["recommendations"]
    pages_crawled = analysis.get("pages_crawled", [])

    # Calculate real scores with feedback
    score_result = calculate_scores(page_data, issues, recommendations)
    scores = score_result["scores"]
    score_feedback = score_result["feedback"]

    # Analyze real navigation flow
    funnel = analyze_navigation_flow(page_data)

    # Determine confidence based on crawl depth
    total_pages = len(pages_crawled)
    confidence_score = min(95, 70 + (total_pages * 2.5))

    results = {
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "mode": "comprehensive" if full_mode else "quick",
        "scores": scores,
        "score_feedback": score_feedback,
        "issues": issues,
        "recommendations": recommendations,
        "confidence": {
            "score": int(confidence_score),
            "level": "High" if confidence_score >= 85 else "Medium" if confidence_score >= 70 else "Low",
            "color": "green" if confidence_score >= 85 else "yellow" if confidence_score >= 70 else "orange",
            "has_real_data": True
        },
        "funnel_analysis": funnel,
        "analytics": None,
        "pages_crawled": pages_crawled,
        "total_pages": total_pages
    }

    audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    audit_results_db[audit_id] = results
    return results


@app.get("/api/audit/stream")
async def stream_audit(
    url: str = Query(..., description="URL to audit"),
    full: str = Query("false", description="Run comprehensive audit (true/false)"),
    users: int = Query(3, description="Number of simulated users"),
    max_pages: int = Query(10, description="Maximum pages to crawl")
):
    """Stream audit progress as Server-Sent Events"""

    # Explicitly parse boolean from string to handle JavaScript true/false
    full_mode = full.lower() in ('true', '1', 'yes', 'on')
    print(f"[Stream Audit] URL: {url}, full param: '{full}', full_mode: {full_mode}, max_pages: {max_pages}")

    async def generate():
        try:
            crawl_mode = f"full site (max {max_pages} pages)" if full_mode else "single page"
            yield f"data: {json.dumps({'type': 'start', 'message': f'Starting {crawl_mode} audit...'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'crawl', 'message': f'Crawling {url} ({crawl_mode})...'})}\n\n"

            # Run real analysis
            try:
                analysis = await analyze_page_with_playwright(url, full_mode, max_pages=max_pages)
            except Exception as analysis_error:
                import traceback
                error_msg = f"{type(analysis_error).__name__}: {str(analysis_error)[:150]}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return

            if "error" in analysis:
                yield f"data: {json.dumps({'type': 'error', 'message': analysis['error']})}\n\n"
                return

            pages_crawled = analysis.get("pages_crawled", [])
            total_pages = len(pages_crawled)
            yield f"data: {json.dumps({'type': 'progress', 'step': 'crawl', 'message': f'Crawled {total_pages} page(s) successfully'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'analyze', 'message': 'Analyzing page structure...'})}\n\n"

            page_data = analysis["page_data"]
            issues = analysis["issues"]
            recommendations = analysis["recommendations"]

            yield f"data: {json.dumps({'type': 'progress', 'step': 'analyze', 'message': f'Found {len(issues)} issues across {total_pages} pages'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'recommend', 'message': 'Generating recommendations...'})}\n\n"

            score_result = calculate_scores(page_data, issues, recommendations)
            scores = score_result["scores"]
            score_feedback = score_result["feedback"]
            funnel = analyze_navigation_flow(page_data)

            # Determine confidence based on crawl depth
            confidence_score = min(95, 70 + (total_pages * 2.5))

            result = {
                "type": "complete",
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "scores": scores,
                "score_feedback": score_feedback,
                "confidence": {
                    "score": int(confidence_score),
                    "level": "High" if confidence_score >= 85 else "Medium" if confidence_score >= 70 else "Low",
                    "color": "green" if confidence_score >= 85 else "yellow" if confidence_score >= 70 else "orange",
                    "has_real_data": True
                },
                "recommendations": recommendations,
                "funnel_analysis": funnel,
                "issues": issues,
                "pages_crawled": pages_crawled,
                "total_pages": total_pages
            }
            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)[:150]}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/audits")
async def list_audits():
    """List all audit results"""
    return list(audit_results_db.values())


@app.post("/api/audit/export")
async def export_audit_report(data: ExportRequest):
    """Generate a comprehensive, personalized HTML audit report for download"""
    try:
        html = generate_comprehensive_report(data)
        # Create safe filename from company name
        safe_company_name = "".join(c if c.isalnum() or c in " -_" else "" for c in data.company_name)
        safe_company_name = safe_company_name.replace(" ", "-")[:50]
        filename = f"{safe_company_name}-audit-report-{datetime.now().strftime('%Y%m%d')}.html"

        return Response(
            content=html,
            media_type="text/html",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Export error: {tb}")  # Log to console
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================================================================
# Mobile App Audit Endpoints
# ============================================================================

# Platform-specific guidelines for analysis
MOBILE_PLATFORM_GUIDELINES = {
    "ios": {
        "name": "iOS Human Interface Guidelines",
        "touch_target_min": 44,  # 44x44 points minimum
        "font_size_min": 11,
        "navigation_patterns": ["tab_bar", "navigation_controller", "modal", "page_sheet"],
        "key_elements": ["safe_area", "status_bar", "home_indicator", "notch_handling"],
        "colors": {
            "system_blue": "#007AFF",
            "destructive_red": "#FF3B30",
            "success_green": "#34C759"
        }
    },
    "android": {
        "name": "Material Design Guidelines",
        "touch_target_min": 48,  # 48dp minimum
        "font_size_min": 12,
        "navigation_patterns": ["bottom_navigation", "navigation_drawer", "top_app_bar", "floating_action_button"],
        "key_elements": ["system_bars", "edge_to_edge", "gesture_navigation", "back_button"],
        "colors": {
            "primary": "#6200EE",
            "secondary": "#03DAC6",
            "error": "#B00020"
        }
    }
}

MOBILE_ISSUE_CATEGORIES = {
    "accessibility": {
        "low_contrast": {
            "title": "Low Color Contrast",
            "description": "Text or interactive elements don't meet WCAG contrast requirements (4.5:1 for normal text, 3:1 for large text).",
            "impact": "Users with visual impairments may not be able to read content.",
            "severity": "high"
        },
        "small_touch_target": {
            "title": "Touch Target Too Small",
            "description": "Interactive elements appear smaller than platform minimum (iOS: 44pt, Android: 48dp).",
            "impact": "Users with motor impairments or fat fingers will struggle to tap accurately.",
            "severity": "high"
        },
        "missing_labels": {
            "title": "Missing Accessibility Labels",
            "description": "Visual elements lack text descriptions for screen readers.",
            "impact": "Blind users won't understand what buttons or images represent.",
            "severity": "critical"
        },
        "poor_focus_indicators": {
            "title": "Missing Focus Indicators",
            "description": "No visible focus state for keyboard/switch control navigation.",
            "impact": "Users navigating without touch can't see which element is selected.",
            "severity": "medium"
        }
    },
    "ui_ux": {
        "inconsistent_spacing": {
            "title": "Inconsistent Spacing",
            "description": "Margins and padding vary inconsistently across the screen.",
            "impact": "Creates visual noise and makes the app feel unpolished.",
            "severity": "medium"
        },
        "cluttered_layout": {
            "title": "Cluttered Layout",
            "description": "Too many elements competing for attention without clear visual hierarchy.",
            "impact": "Users feel overwhelmed and may miss important actions.",
            "severity": "high"
        },
        "unclear_cta": {
            "title": "Unclear Call-to-Action",
            "description": "Primary action button doesn't stand out or is hard to identify.",
            "impact": "Users may not complete desired actions, reducing conversion.",
            "severity": "high"
        },
        "poor_navigation": {
            "title": "Confusing Navigation",
            "description": "Navigation structure is unclear or inconsistent.",
            "impact": "Users get lost and may abandon the app.",
            "severity": "critical"
        },
        "missing_feedback": {
            "title": "Missing User Feedback",
            "description": "No loading states, success confirmations, or error messages visible.",
            "impact": "Users don't know if their actions were successful.",
            "severity": "medium"
        }
    },
    "platform_compliance": {
        "non_native_controls": {
            "title": "Non-Native UI Controls",
            "description": "Custom controls that don't match platform conventions.",
            "impact": "Users must relearn how to interact with familiar patterns.",
            "severity": "medium"
        },
        "wrong_navigation_pattern": {
            "title": "Incorrect Navigation Pattern",
            "description": "Using navigation patterns not typical for this platform.",
            "impact": "Feels foreign to users and increases cognitive load.",
            "severity": "medium"
        },
        "missing_platform_features": {
            "title": "Missing Platform Features",
            "description": "Not utilizing expected platform features like haptics, shortcuts, or widgets.",
            "impact": "App feels less integrated with the device.",
            "severity": "low"
        }
    },
    "visual_design": {
        "poor_typography": {
            "title": "Typography Issues",
            "description": "Font sizes too small, poor readability, or too many font styles.",
            "impact": "Content is hard to read and looks unprofessional.",
            "severity": "medium"
        },
        "color_inconsistency": {
            "title": "Inconsistent Color Usage",
            "description": "Colors used inconsistently for similar actions or elements.",
            "impact": "Users can't build mental models of what colors mean.",
            "severity": "medium"
        },
        "poor_image_quality": {
            "title": "Low Quality Images",
            "description": "Images appear blurry, pixelated, or poorly cropped.",
            "impact": "Makes the app look cheap and unprofessional.",
            "severity": "medium"
        }
    }
}


async def analyze_mobile_screenshot(screenshot_base64: str, platform: str, screen_index: int, app_name: str) -> Dict[str, Any]:
    """Analyze a single mobile app screenshot using AI vision"""

    guidelines = MOBILE_PLATFORM_GUIDELINES.get(platform, MOBILE_PLATFORM_GUIDELINES["ios"])

    # Simulated analysis (in production, use Claude Vision API)
    # This provides realistic mock data for demonstration

    import random
    import hashlib

    # Use hash of screenshot to generate consistent "random" results
    hash_seed = int(hashlib.md5(screenshot_base64[:100].encode()).hexdigest()[:8], 16)
    random.seed(hash_seed)

    screen_names = [
        "Home Screen", "Login Screen", "Profile Screen", "Settings Screen",
        "Product List", "Product Detail", "Checkout Flow", "Search Results",
        "Onboarding", "Dashboard", "Notifications", "Chat/Messages"
    ]

    screen_name = screen_names[screen_index % len(screen_names)]

    # Generate issues based on random selection
    potential_issues = []
    all_issues = []
    for category, issues in MOBILE_ISSUE_CATEGORIES.items():
        for issue_key, issue_data in issues.items():
            all_issues.append({**issue_data, "category": category, "key": issue_key})

    # Randomly select 1-4 issues per screen
    num_issues = random.randint(1, 4)
    selected_issues = random.sample(all_issues, min(num_issues, len(all_issues)))

    # Add location and screen context to issues
    for issue in selected_issues:
        issue["screen"] = screen_name
        issue["location"] = random.choice([
            "Top navigation area", "Center content area", "Bottom action bar",
            "Header section", "Form fields", "Button row", "Card component"
        ])

    # Generate positive aspects
    positive_aspects = random.sample([
        "Good use of whitespace for visual breathing room",
        "Clear visual hierarchy guides the eye",
        "Primary action button is prominent",
        "Color scheme is consistent with brand",
        "Typography is readable and well-sized",
        "Native platform controls used appropriately",
        "Proper safe area handling for device notch",
        "Loading states provide good feedback",
        "Touch targets are adequately sized",
        "Navigation pattern follows platform conventions"
    ], random.randint(2, 4))

    # Calculate scores with some variation
    base_score = random.uniform(6.0, 9.0)

    return {
        "screen_name": screen_name,
        "screen_index": screen_index,
        "issues": selected_issues,
        "positive_aspects": positive_aspects,
        "accessibility_score": round(max(5.0, base_score - random.uniform(0, 2)), 1),
        "ui_consistency_score": round(max(5.0, base_score - random.uniform(0, 1.5)), 1),
        "platform_compliance_score": round(max(5.0, base_score - random.uniform(0, 1)), 1),
        "visual_design_score": round(max(5.0, base_score - random.uniform(0, 1.5)), 1)
    }


def analyze_funnel_data(funnel_data: List[Dict], screen_analyses: List[Dict], issues: List[Dict]) -> Dict[str, Any]:
    """Analyze funnel data and correlate with UX issues"""
    if not funnel_data:
        return None

    funnel_analysis = {
        "total_steps": len(funnel_data),
        "overall_conversion": 0,
        "biggest_drop_off": None,
        "steps": [],
        "issue_correlations": []
    }

    for i, step in enumerate(funnel_data):
        drop_off = step.get("drop_off_rate")
        if drop_off is None and step.get("users_entered", 0) > 0:
            drop_off = round((1 - step.get("users_completed", 0) / step["users_entered"]) * 100, 1)

        step_analysis = {
            "name": step.get("name"),
            "screen": step.get("screen_name"),
            "users_entered": step.get("users_entered", 0),
            "users_completed": step.get("users_completed", 0),
            "drop_off_rate": drop_off,
            "is_problem_area": drop_off and drop_off > 20
        }
        funnel_analysis["steps"].append(step_analysis)

        # Track biggest drop-off
        if drop_off and (funnel_analysis["biggest_drop_off"] is None or
                         drop_off > funnel_analysis["biggest_drop_off"]["drop_off_rate"]):
            funnel_analysis["biggest_drop_off"] = {
                "step": step.get("name"),
                "screen": step.get("screen_name"),
                "drop_off_rate": drop_off
            }

        # Correlate issues with this funnel step
        screen_name = step.get("screen_name", "").lower()
        for issue in issues:
            issue_screen = issue.get("screen", "").lower()
            if screen_name and screen_name in issue_screen:
                funnel_analysis["issue_correlations"].append({
                    "funnel_step": step.get("name"),
                    "issue": issue.get("title"),
                    "severity": issue.get("severity"),
                    "drop_off_rate": drop_off,
                    "correlation": "High drop-off may be caused by this UX issue"
                })

    # Calculate overall conversion
    if funnel_data and funnel_data[0].get("users_entered", 0) > 0:
        first_users = funnel_data[0]["users_entered"]
        last_users = funnel_data[-1].get("users_completed", 0)
        funnel_analysis["overall_conversion"] = round((last_users / first_users) * 100, 1)

    return funnel_analysis


def calculate_mobile_roi(business_goals: Dict, issues: List[Dict], funnel_analysis: Optional[Dict]) -> Dict[str, Any]:
    """Calculate ROI projection based on business goals and identified issues"""
    if not business_goals:
        return None

    mau = business_goals.get("monthly_active_users", 10000)
    arpu = business_goals.get("average_revenue_per_user", 5.0)
    current_value = business_goals.get("current_value", 2.0)  # Current conversion %
    target_value = business_goals.get("target_value", 4.0)  # Target conversion %

    # Count issues by severity
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    high_count = sum(1 for i in issues if i.get("severity") == "high")

    # Estimate improvement potential (conservative)
    # Each critical fix: 0.3-0.5% improvement
    # Each high fix: 0.1-0.2% improvement
    potential_improvement = min(
        (critical_count * 0.4) + (high_count * 0.15),
        target_value - current_value  # Cap at target
    )

    # Calculate revenue impact
    current_revenue = mau * (current_value / 100) * arpu
    projected_revenue = mau * ((current_value + potential_improvement) / 100) * arpu
    monthly_gain = projected_revenue - current_revenue
    annual_gain = monthly_gain * 12

    # Factor in funnel improvements
    funnel_improvement = 0
    if funnel_analysis and funnel_analysis.get("biggest_drop_off"):
        drop_off = funnel_analysis["biggest_drop_off"]["drop_off_rate"]
        # If we can reduce drop-off by 20% of current rate
        funnel_improvement = (drop_off * 0.2 / 100) * mau * arpu

    return {
        "current_monthly_revenue": round(current_revenue),
        "projected_monthly_revenue": round(projected_revenue + funnel_improvement),
        "monthly_gain": round(monthly_gain + funnel_improvement),
        "annual_gain": round(annual_gain + (funnel_improvement * 12)),
        "conversion_improvement": round(potential_improvement, 2),
        "issues_addressed": critical_count + high_count,
        "assumptions": [
            f"Based on {mau:,} monthly active users",
            f"Average revenue per user: ${arpu:.2f}",
            f"Current conversion: {current_value}%",
            f"Fixing {critical_count} critical and {high_count} high issues",
            "Conservative estimate: 0.4% per critical, 0.15% per high issue"
        ]
    }


def analyze_persona_impact(personas: List[Dict], issues: List[Dict]) -> List[Dict[str, Any]]:
    """Analyze how issues impact different user personas"""
    if not personas:
        return None

    persona_impacts = []

    for persona in personas:
        impact = {
            "persona_name": persona.get("name"),
            "description": persona.get("description"),
            "affected_issues": [],
            "severity_score": 0,
            "recommendations": []
        }

        accessibility_needs = persona.get("accessibility_needs", [])
        tech_savviness = persona.get("tech_savviness", "medium")
        goals = persona.get("goals", [])

        for issue in issues:
            affected = False
            reason = ""

            # Check accessibility needs
            if accessibility_needs:
                if "color_blind" in accessibility_needs and "contrast" in issue.get("title", "").lower():
                    affected = True
                    reason = "Color contrast issues affect color-blind users"
                if "motor_impaired" in accessibility_needs and "touch" in issue.get("title", "").lower():
                    affected = True
                    reason = "Small touch targets affect motor-impaired users"
                if any(need in ["blind", "screen_reader"] for need in accessibility_needs):
                    if "label" in issue.get("title", "").lower() or "accessibility" in issue.get("category", ""):
                        affected = True
                        reason = "Accessibility issues affect screen reader users"

            # Check tech savviness impact
            if tech_savviness == "low":
                if "navigation" in issue.get("category", "") or "unclear" in issue.get("title", "").lower():
                    affected = True
                    reason = "Navigation issues particularly affect less tech-savvy users"

            # Check if issue blocks user goals
            for goal in goals:
                if any(keyword in issue.get("screen", "").lower() for keyword in goal.lower().split()):
                    affected = True
                    reason = f"Issue on screen related to user goal: {goal}"

            if affected:
                severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                impact["affected_issues"].append({
                    "issue": issue.get("title"),
                    "severity": issue.get("severity"),
                    "reason": reason
                })
                impact["severity_score"] += severity_weight.get(issue.get("severity", "medium"), 2)

        # Generate persona-specific recommendations
        if impact["affected_issues"]:
            if any("accessibility" in i.get("reason", "").lower() for i in impact["affected_issues"]):
                impact["recommendations"].append(f"Prioritize accessibility fixes for {persona.get('name')}")
            if impact["severity_score"] > 5:
                impact["recommendations"].append(f"Critical: {persona.get('name')} experience is severely impacted")

        persona_impacts.append(impact)

    return persona_impacts


def build_priority_matrix(issues: List[Dict], analytics: Optional[Dict]) -> Dict[str, Any]:
    """Build impact vs effort priority matrix for issues"""
    matrix = {
        "quick_wins": [],      # High impact, Low effort
        "major_projects": [],  # High impact, High effort
        "fill_ins": [],        # Low impact, Low effort
        "thankless_tasks": []  # Low impact, High effort
    }

    # Effort mapping
    effort_map = {
        "accessibility": {"missing_labels": "low", "low_contrast": "low", "small_touch_target": "medium"},
        "ui_ux": {"unclear_cta": "low", "cluttered_layout": "medium", "poor_navigation": "high"},
        "platform_compliance": {"non_native_controls": "high", "wrong_navigation_pattern": "medium"},
        "visual_design": {"poor_typography": "low", "color_inconsistency": "low", "poor_image_quality": "low"}
    }

    # Impact is based on severity + analytics correlation
    for issue in issues:
        severity = issue.get("severity", "medium")
        category = issue.get("category", "general")
        key = issue.get("key", "")

        # Determine effort
        effort = effort_map.get(category, {}).get(key, "medium")

        # Determine impact (severity-based, boosted by analytics)
        impact = "high" if severity in ["critical", "high"] else "low"

        # Check if this issue correlates with analytics problems
        if analytics:
            screen_metrics = analytics.get("screen_metrics") or []
            for metric in screen_metrics:
                if metric.get("screen_name", "").lower() in issue.get("screen", "").lower():
                    if metric.get("bounce_rate", 0) > 50 or metric.get("rage_taps", 0) > 10:
                        impact = "high"  # Boost impact if analytics show problems

        # Categorize into matrix
        issue_entry = {
            "title": issue.get("title"),
            "screen": issue.get("screen"),
            "severity": severity,
            "effort": effort,
            "impact": impact
        }

        if impact == "high" and effort == "low":
            matrix["quick_wins"].append(issue_entry)
        elif impact == "high" and effort in ["medium", "high"]:
            matrix["major_projects"].append(issue_entry)
        elif impact == "low" and effort == "low":
            matrix["fill_ins"].append(issue_entry)
        else:
            matrix["thankless_tasks"].append(issue_entry)

    return matrix


async def analyze_mobile_app(request: MobileAppAuditRequest) -> Dict[str, Any]:
    """Analyze a mobile app from screenshots with optional analytics data"""

    screen_analyses = []
    all_issues = []

    # Get screen names if provided
    screen_names = request.screen_names or []

    # Analyze each screenshot
    for idx, screenshot in enumerate(request.screenshots):
        # Use provided screen name or generate one
        custom_screen_name = screen_names[idx] if idx < len(screen_names) else None

        analysis = await analyze_mobile_screenshot(
            screenshot,
            request.platform,
            idx,
            request.app_name
        )

        # Override screen name if provided
        if custom_screen_name:
            analysis["screen_name"] = custom_screen_name
            for issue in analysis["issues"]:
                issue["screen"] = custom_screen_name

        # Add analytics insights if available
        if request.analytics:
            analysis["analytics_insights"] = []

            # Check screen metrics
            if request.analytics.screen_metrics:
                for metric in request.analytics.screen_metrics:
                    if metric.screen_name.lower() in analysis["screen_name"].lower():
                        if metric.bounce_rate and metric.bounce_rate > 40:
                            analysis["analytics_insights"].append(
                                f"High bounce rate ({metric.bounce_rate}%) - users leaving quickly"
                            )
                        if metric.rage_taps and metric.rage_taps > 5:
                            analysis["analytics_insights"].append(
                                f"Rage taps detected ({metric.rage_taps}) - users frustrated with unresponsive elements"
                            )
                        if metric.avg_time_spent_seconds and metric.avg_time_spent_seconds > 60:
                            analysis["analytics_insights"].append(
                                f"High time on screen ({metric.avg_time_spent_seconds}s) - users may be confused"
                            )

            # Check funnel position
            if request.analytics.funnel_data:
                for step in request.analytics.funnel_data:
                    if step.screen_name and step.screen_name.lower() in analysis["screen_name"].lower():
                        drop_off = step.drop_off_rate
                        if drop_off is None and step.users_entered > 0:
                            drop_off = round((1 - step.users_completed / step.users_entered) * 100, 1)
                        if drop_off and drop_off > 15:
                            analysis["drop_off_correlation"] = f"{drop_off}% drop-off at this step"
                            analysis["priority_level"] = "critical" if drop_off > 30 else "high"

            # Check crash data
            if request.analytics.crash_screens:
                for crash_screen in request.analytics.crash_screens:
                    if crash_screen.lower() in analysis["screen_name"].lower():
                        analysis["analytics_insights"].append("⚠️ High crash rate reported on this screen")

        screen_analyses.append(analysis)
        all_issues.extend(analysis["issues"])

    # Aggregate scores
    if screen_analyses:
        avg_accessibility = sum(s["accessibility_score"] for s in screen_analyses) / len(screen_analyses)
        avg_ui = sum(s["ui_consistency_score"] for s in screen_analyses) / len(screen_analyses)
        avg_platform = sum(s["platform_compliance_score"] for s in screen_analyses) / len(screen_analyses)
        avg_visual = sum(s["visual_design_score"] for s in screen_analyses) / len(screen_analyses)
    else:
        avg_accessibility = avg_ui = avg_platform = avg_visual = 5.0

    overall_score = round((avg_accessibility + avg_ui + avg_platform + avg_visual) / 4, 1)

    # Deduplicate and prioritize issues
    seen_issues = set()
    unique_issues = []
    for issue in all_issues:
        issue_key = (issue["key"], issue.get("screen", ""))
        if issue_key not in seen_issues:
            seen_issues.add(issue_key)
            unique_issues.append(issue)

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    unique_issues.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 2))

    # Analyze funnel data if provided
    funnel_analysis = None
    if request.analytics and request.analytics.funnel_data:
        funnel_data = [step.dict() for step in request.analytics.funnel_data]
        funnel_analysis = analyze_funnel_data(funnel_data, screen_analyses, unique_issues)

    # Calculate ROI if business goals provided
    roi_projection = None
    if request.business_goals:
        roi_projection = calculate_mobile_roi(
            request.business_goals.dict(),
            unique_issues,
            funnel_analysis
        )

    # Analyze persona impact if personas provided
    persona_impact = None
    if request.user_personas:
        personas = [p.dict() for p in request.user_personas]
        persona_impact = analyze_persona_impact(personas, unique_issues)

    # Build priority matrix
    analytics_dict = request.analytics.dict() if request.analytics else None
    priority_matrix = build_priority_matrix(unique_issues, analytics_dict)

    # Generate recommendations based on issues AND analytics
    recommendations = []
    priority = 1

    # Add analytics-driven recommendations first (highest priority)
    if funnel_analysis and funnel_analysis.get("biggest_drop_off"):
        drop_off = funnel_analysis["biggest_drop_off"]
        recommendations.append({
            "priority": priority,
            "category": "Funnel Optimization",
            "title": f"Fix Drop-off at {drop_off['step']}",
            "description": f"Analytics show {drop_off['drop_off_rate']}% of users drop off at '{drop_off['step']}'. This is your biggest conversion blocker. Review the {drop_off.get('screen', 'this')} screen for UX issues.",
            "impact": f"Could recover {drop_off['drop_off_rate'] * 0.3:.1f}% of lost users",
            "effort": "High",
            "data_driven": True
        })
        priority += 1

    # Add quick wins from priority matrix
    if priority_matrix["quick_wins"]:
        quick_win_titles = [qw["title"] for qw in priority_matrix["quick_wins"][:3]]
        recommendations.append({
            "priority": priority,
            "category": "Quick Wins",
            "title": "Address High-Impact, Low-Effort Issues",
            "description": f"Start with these easy fixes for maximum impact: {', '.join(quick_win_titles)}",
            "impact": "High - Immediate improvement with minimal effort",
            "effort": "Low",
            "data_driven": bool(request.analytics)
        })
        priority += 1

    # Group issues by category for recommendations
    issues_by_category = {}
    for issue in unique_issues:
        cat = issue.get("category", "general")
        if cat not in issues_by_category:
            issues_by_category[cat] = []
        issues_by_category[cat].append(issue)

    for category, cat_issues in issues_by_category.items():
        if category == "accessibility" and cat_issues:
            rec = {
                "priority": priority,
                "category": "Accessibility",
                "title": "Fix Accessibility Issues",
                "description": f"Found {len(cat_issues)} accessibility issues. Focus on touch targets ({MOBILE_PLATFORM_GUIDELINES[request.platform]['touch_target_min']}pt minimum) and screen reader labels.",
                "impact": "High - Affects ~15% of users",
                "effort": "Medium"
            }
            # Enhance with persona data
            if persona_impact:
                affected_personas = [p["persona_name"] for p in persona_impact
                                   if any("accessibility" in i.get("reason", "").lower()
                                         for i in p.get("affected_issues", []))]
                if affected_personas:
                    rec["description"] += f" Critical for: {', '.join(affected_personas)}"
            recommendations.append(rec)
            priority += 1

        if category == "ui_ux" and cat_issues:
            recommendations.append({
                "priority": priority,
                "category": "UX Design",
                "title": "Improve User Experience",
                "description": f"Found {len(cat_issues)} UX issues affecting user flow and clarity.",
                "impact": "High - Directly affects conversion",
                "effort": "Medium"
            })
            priority += 1

        if category == "platform_compliance" and cat_issues:
            recommendations.append({
                "priority": priority,
                "category": "Platform Compliance",
                "title": f"Align with {MOBILE_PLATFORM_GUIDELINES[request.platform]['name']}",
                "description": f"Found {len(cat_issues)} platform guideline violations.",
                "impact": "Medium - Affects perceived quality",
                "effort": "Medium"
            })
            priority += 1

    # Generate summary with analytics context
    critical_count = sum(1 for i in unique_issues if i.get("severity") == "critical")
    high_count = sum(1 for i in unique_issues if i.get("severity") == "high")

    summary_parts = []
    if overall_score >= 8:
        summary_parts.append(f"{request.app_name} demonstrates strong mobile design with a score of {overall_score}/10.")
    elif overall_score >= 6:
        summary_parts.append(f"{request.app_name} has solid foundations but needs improvement (score: {overall_score}/10).")
    else:
        summary_parts.append(f"{request.app_name} has significant usability concerns (score: {overall_score}/10).")

    summary_parts.append(f"Found {critical_count} critical and {high_count} high-priority issues.")

    if funnel_analysis:
        summary_parts.append(f"Funnel conversion: {funnel_analysis['overall_conversion']}%.")
        if funnel_analysis.get("biggest_drop_off"):
            summary_parts.append(f"Biggest leak: {funnel_analysis['biggest_drop_off']['step']} ({funnel_analysis['biggest_drop_off']['drop_off_rate']}% drop-off).")

    if roi_projection:
        summary_parts.append(f"Fixing issues could generate ${roi_projection['monthly_gain']:,}/month additional revenue.")

    summary = " ".join(summary_parts)

    # Calculate confidence (higher with more data)
    confidence_score = 55
    confidence_factors = []

    if len(request.screenshots) >= 5:
        confidence_score += 15
        confidence_factors.append(f"{len(request.screenshots)} screenshots")
    elif len(request.screenshots) >= 3:
        confidence_score += 10
        confidence_factors.append(f"{len(request.screenshots)} screenshots")

    if request.analytics:
        confidence_score += 15
        confidence_factors.append("analytics data")
    if request.user_personas:
        confidence_score += 5
        confidence_factors.append("user personas")
    if request.business_goals:
        confidence_score += 5
        confidence_factors.append("business goals")
    if request.screen_recordings:
        confidence_score += 5
        confidence_factors.append("screen recordings")

    confidence_score = min(confidence_score, 95)

    if confidence_score >= 80:
        confidence_level = "High"
        confidence_color = "green"
    elif confidence_score >= 65:
        confidence_level = "Medium-High"
        confidence_color = "green"
    elif confidence_score >= 50:
        confidence_level = "Medium"
        confidence_color = "yellow"
    else:
        confidence_level = "Low"
        confidence_color = "orange"

    confidence = {
        "level": confidence_level,
        "score": confidence_score,
        "color": confidence_color,
        "factors": confidence_factors,
        "note": f"Based on: {', '.join(confidence_factors)}" if confidence_factors else "Upload more data for higher confidence"
    }

    return {
        "app_name": request.app_name,
        "platform": request.platform,
        "timestamp": datetime.now().isoformat(),
        "overall_score": overall_score,
        "scores": {
            "accessibility": round(avg_accessibility, 1),
            "ui_ux": round(avg_ui, 1),
            "platform_compliance": round(avg_platform, 1),
            "visual_design": round(avg_visual, 1),
            "navigation": round((avg_ui + avg_platform) / 2, 1)
        },
        "screen_analyses": screen_analyses,
        "issues": unique_issues,
        "recommendations": recommendations,
        "summary": summary,
        "confidence": confidence,
        # Enhanced analytics output
        "funnel_analysis": funnel_analysis,
        "roi_projection": roi_projection,
        "persona_impact": persona_impact,
        "priority_matrix": priority_matrix
    }


@app.post("/api/audit/mobile")
async def run_mobile_app_audit(request: MobileAppAuditRequest):
    """Run a mobile app audit based on uploaded screenshots"""

    if not request.screenshots:
        raise HTTPException(status_code=400, detail="At least one screenshot is required")

    if len(request.screenshots) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 screenshots allowed")

    # Validate platform
    if request.platform not in ["ios", "android", "both"]:
        raise HTTPException(status_code=400, detail="Platform must be 'ios', 'android', or 'both'")

    try:
        result = await analyze_mobile_app(request)
        return result
    except Exception as e:
        import traceback
        print(f"Mobile audit error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Mobile audit failed: {str(e)}")


@app.get("/api/audit/mobile/stream")
async def stream_mobile_app_audit(
    app_name: str = Query(..., description="Name of the mobile app"),
    platform: str = Query("ios", description="Platform: ios, android, or both"),
):
    """Stream mobile app audit progress as Server-Sent Events"""

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting mobile app audit...'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'upload', 'message': 'Processing screenshots...'})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'type': 'step', 'step': 'analyze', 'message': 'Analyzing UI/UX patterns...'})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'type': 'step', 'step': 'accessibility', 'message': 'Checking accessibility...'})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'type': 'step', 'step': 'platform', 'message': f'Verifying {platform.upper()} guidelines compliance...'})}\n\n"
            await asyncio.sleep(0.5)

            yield f"data: {json.dumps({'type': 'step', 'step': 'report', 'message': 'Generating recommendations...'})}\n\n"

            # Note: In streaming mode, actual analysis happens in the POST endpoint
            # This is just for showing progress to the user
            yield f"data: {json.dumps({'type': 'ready', 'message': 'Ready for analysis. Submit screenshots via POST.'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:200]})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================================
# Code Audit Endpoints
# ============================================================================

@app.post("/api/audit/code")
async def run_code_audit(request: CodeAuditRequest):
    """Run a code audit on a GitHub repository"""
    result = await analyze_github_repo(request.repo_url)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    result["timestamp"] = datetime.now().isoformat()
    result["type"] = "complete"
    return result


@app.get("/api/audit/code/stream")
async def stream_code_audit(repo_url: str = Query(..., description="GitHub repository URL")):
    """Stream code audit progress as Server-Sent Events"""

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting code audit...'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'clone', 'message': 'Fetching repository metadata...'})}\n\n"

            # Parse and validate URL
            match = re.match(r'https?://(?:www\.)?github\.com/([^/]+)/([^/]+)/?', repo_url)
            if not match:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid GitHub URL format'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'step', 'step': 'analyze', 'message': 'Analyzing code structure...'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'security', 'message': 'Running security scan...'})}\n\n"

            # Run real analysis
            result = await analyze_github_repo(repo_url)

            if "error" in result:
                yield f"data: {json.dumps({'type': 'error', 'message': result['error']})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'step', 'step': 'quality', 'message': 'Checking code quality...'})}\n\n"

            yield f"data: {json.dumps({'type': 'step', 'step': 'report', 'message': 'Generating report...'})}\n\n"

            result["timestamp"] = datetime.now().isoformat()
            result["type"] = "complete"
            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:200]})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================================
# Projects Endpoints
# ============================================================================

@app.post("/api/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(projects_db)}"
    new_project = {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "platform": project.platform,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    projects_db[project_id] = new_project
    return new_project


@app.get("/api/projects")
async def list_projects():
    return list(projects_db.values())


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    del projects_db[project_id]
    return {"status": "deleted", "id": project_id}


# ============================================================================
# A/B Tests Endpoints
# ============================================================================

@app.post("/api/ab-tests")
async def create_ab_test(test: ABTestCreate):
    test_id = f"ab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    new_test = {
        "id": test_id,
        "name": test.name,
        "project_id": test.project_id,
        "variants": test.variants,
        "target_metric": test.target_metric,
        "status": "draft",
        "results": None,
        "created_at": datetime.now().isoformat()
    }
    ab_tests_db[test_id] = new_test
    return new_test


@app.get("/api/ab-tests")
async def list_ab_tests(project_id: Optional[str] = None):
    tests = list(ab_tests_db.values())
    if project_id:
        tests = [t for t in tests if t.get("project_id") == project_id]
    return tests


@app.get("/api/ab-tests/{test_id}")
async def get_ab_test(test_id: str):
    if test_id not in ab_tests_db:
        raise HTTPException(status_code=404, detail="A/B test not found")
    return ab_tests_db[test_id]


@app.post("/api/ab-tests/{test_id}/start")
async def start_ab_test(test_id: str):
    if test_id not in ab_tests_db:
        raise HTTPException(status_code=404, detail="A/B test not found")
    ab_tests_db[test_id]["status"] = "running"
    ab_tests_db[test_id]["started_at"] = datetime.now().isoformat()
    return ab_tests_db[test_id]


@app.post("/api/ab-tests/{test_id}/stop")
async def stop_ab_test(test_id: str):
    if test_id not in ab_tests_db:
        raise HTTPException(status_code=404, detail="A/B test not found")
    ab_tests_db[test_id]["status"] = "completed"
    ab_tests_db[test_id]["ended_at"] = datetime.now().isoformat()
    return ab_tests_db[test_id]


# ============================================================================
# Idea Validation (Beginner-Friendly Market Research)
# ============================================================================

# Industry detection patterns
INDUSTRY_PATTERNS = {
    "e-commerce": ["shop", "store", "buy", "sell", "marketplace", "retail", "product", "cart", "checkout"],
    "saas": ["software", "platform", "tool", "dashboard", "analytics", "automation", "workflow", "integrate"],
    "health": ["health", "fitness", "wellness", "medical", "diet", "nutrition", "exercise", "mental", "therapy"],
    "fintech": ["finance", "payment", "money", "invest", "bank", "budget", "crypto", "trading", "loan"],
    "edtech": ["learn", "education", "course", "tutor", "student", "teach", "school", "training", "skill"],
    "food": ["food", "meal", "recipe", "restaurant", "delivery", "cooking", "grocery", "eat", "diet"],
    "social": ["social", "connect", "community", "chat", "message", "share", "friend", "network", "date"],
    "productivity": ["productivity", "task", "todo", "organize", "schedule", "calendar", "time", "manage", "note"],
    "travel": ["travel", "trip", "hotel", "flight", "vacation", "booking", "destination", "tour", "adventure"],
    "real_estate": ["real estate", "property", "home", "apartment", "rent", "buy house", "mortgage", "listing"],
}

# Competitor database by industry (simulated - in production would use web search)
COMPETITOR_DATABASE = {
    "food": [
        {"name": "HelloFresh", "description": "Meal kit delivery service with pre-portioned ingredients", "website": "hellofresh.com", "funding": "public", "strengths": ["Brand recognition", "Wide variety", "Convenience"], "weaknesses": ["Expensive", "Packaging waste", "Limited customization"]},
        {"name": "Mealime", "description": "Meal planning app with grocery lists", "website": "mealime.com", "funding": "series-a", "strengths": ["Free tier", "Smart grocery lists", "Diet filters"], "weaknesses": ["Limited recipes", "No delivery", "Basic UI"]},
        {"name": "Yummly", "description": "Recipe discovery and meal planning", "website": "yummly.com", "funding": "acquired", "strengths": ["Huge recipe database", "Smart recommendations", "Kitchen integrations"], "weaknesses": ["Ad-heavy", "Overwhelming options", "Premium required"]},
        {"name": "Paprika", "description": "Recipe manager and meal planner", "website": "paprikaapp.com", "funding": "bootstrapped", "strengths": ["One-time purchase", "Web clipper", "Sync across devices"], "weaknesses": ["Dated UI", "No social features", "Manual entry"]},
        {"name": "Eat This Much", "description": "AI-powered meal planner for specific calorie goals", "website": "eatthismuch.com", "funding": "bootstrapped", "strengths": ["Automatic planning", "Macro tracking", "Grocery delivery"], "weaknesses": ["Complex interface", "Meal suggestions odd", "Expensive premium"]},
    ],
    "health": [
        {"name": "Headspace", "description": "Meditation and mindfulness app", "website": "headspace.com", "funding": "series-c", "strengths": ["Polished content", "Brand trust", "Sleep content"], "weaknesses": ["Subscription required", "Not personalized", "Limited free"]},
        {"name": "Calm", "description": "Sleep, meditation, and relaxation app", "website": "calm.com", "funding": "series-b", "strengths": ["Celebrity narrators", "Sleep stories", "Beautiful design"], "weaknesses": ["Expensive", "Generic content", "Limited offline"]},
        {"name": "Noom", "description": "Psychology-based weight loss app", "website": "noom.com", "funding": "series-f", "strengths": ["Behavior change focus", "Personal coaching", "Proven results"], "weaknesses": ["Very expensive", "Aggressive marketing", "Repetitive content"]},
        {"name": "MyFitnessPal", "description": "Calorie counter and diet tracker", "website": "myfitnesspal.com", "funding": "acquired", "strengths": ["Huge food database", "Barcode scanner", "Free tier"], "weaknesses": ["Ad-heavy", "Clunky UI", "Premium pushing"]},
    ],
    "productivity": [
        {"name": "Notion", "description": "All-in-one workspace for notes, tasks, wikis", "website": "notion.so", "funding": "series-c", "strengths": ["Extremely flexible", "Beautiful design", "Templates"], "weaknesses": ["Steep learning curve", "Slow performance", "Overwhelming"]},
        {"name": "Todoist", "description": "Task manager and to-do list", "website": "todoist.com", "funding": "bootstrapped", "strengths": ["Simple yet powerful", "Cross-platform", "Natural language"], "weaknesses": ["Limited free tier", "No time blocking", "Basic notes"]},
        {"name": "Asana", "description": "Project and task management for teams", "website": "asana.com", "funding": "public", "strengths": ["Team collaboration", "Timeline view", "Integrations"], "weaknesses": ["Complex for individuals", "Expensive", "Feature bloat"]},
    ],
    "saas": [
        {"name": "Existing B2B Tools", "description": "Various established players in the space", "website": "various", "funding": "various", "strengths": ["Established", "Feature-rich", "Enterprise-ready"], "weaknesses": ["Complex", "Expensive", "Slow to innovate"]},
    ],
    "e-commerce": [
        {"name": "Shopify", "description": "E-commerce platform for online stores", "website": "shopify.com", "funding": "public", "strengths": ["Easy setup", "App ecosystem", "Reliable"], "weaknesses": ["Transaction fees", "Limited customization", "Expensive apps"]},
        {"name": "Etsy", "description": "Marketplace for handmade and vintage items", "website": "etsy.com", "funding": "public", "strengths": ["Built-in audience", "Easy to start", "Community"], "weaknesses": ["High fees", "Competition", "Algorithm changes"]},
    ],
    "fintech": [
        {"name": "Mint", "description": "Personal finance and budgeting app", "website": "mint.com", "funding": "acquired", "strengths": ["Free", "Bank connections", "Credit score"], "weaknesses": ["Ad-supported", "Sync issues", "Being sunset"]},
        {"name": "YNAB", "description": "Zero-based budgeting software", "website": "ynab.com", "funding": "bootstrapped", "strengths": ["Proven method", "Great education", "Active community"], "weaknesses": ["Expensive", "Learning curve", "Manual effort"]},
        {"name": "Robinhood", "description": "Commission-free stock trading", "website": "robinhood.com", "funding": "public", "strengths": ["No fees", "Easy to use", "Fractional shares"], "weaknesses": ["Gamified", "Limited tools", "Reliability issues"]},
    ],
    "edtech": [
        {"name": "Coursera", "description": "Online courses from universities", "website": "coursera.com", "funding": "public", "strengths": ["University credentials", "Wide variety", "Quality content"], "weaknesses": ["Expensive certificates", "Completion rates low", "Passive learning"]},
        {"name": "Duolingo", "description": "Language learning app with gamification", "website": "duolingo.com", "funding": "public", "strengths": ["Free tier", "Gamified", "Effective"], "weaknesses": ["Limited languages", "Annoying notifications", "Repetitive"]},
        {"name": "Skillshare", "description": "Creative skills learning platform", "website": "skillshare.com", "funding": "series-d", "strengths": ["Affordable", "Creative focus", "Project-based"], "weaknesses": ["Quality varies", "No certificates", "Niche content"]},
    ],
    "social": [
        {"name": "Discord", "description": "Community chat platform", "website": "discord.com", "funding": "acquired", "strengths": ["Free", "Feature-rich", "Communities"], "weaknesses": ["Complex for beginners", "Moderation challenges", "Gaming stigma"]},
        {"name": "Slack", "description": "Team communication platform", "website": "slack.com", "funding": "acquired", "strengths": ["Work-focused", "Integrations", "Organized"], "weaknesses": ["Expensive", "Notification overload", "Channel sprawl"]},
    ],
    "travel": [
        {"name": "Airbnb", "description": "Vacation rentals and experiences", "website": "airbnb.com", "funding": "public", "strengths": ["Unique stays", "Experiences", "Global reach"], "weaknesses": ["Fees", "Inconsistent quality", "Regulations"]},
        {"name": "Booking.com", "description": "Hotel and accommodation booking", "website": "booking.com", "funding": "public", "strengths": ["Huge inventory", "Free cancellation", "Reviews"], "weaknesses": ["Cluttered UI", "Hidden fees", "Pressure tactics"]},
    ],
    "real_estate": [
        {"name": "Zillow", "description": "Real estate marketplace", "website": "zillow.com", "funding": "public", "strengths": ["Comprehensive listings", "Zestimate", "Brand recognition"], "weaknesses": ["Accuracy issues", "Lead selling", "Agent-focused"]},
        {"name": "Redfin", "description": "Tech-enabled real estate brokerage", "website": "redfin.com", "funding": "public", "strengths": ["Lower commissions", "Good tech", "Transparent"], "weaknesses": ["Limited markets", "Agent quality varies", "Aggressive growth"]},
    ],
}


# =============================================================================
# AI-Powered Idea Validation Models and Functions
# =============================================================================

class AICompetitorAnalysis(BaseModel):
    """AI-generated competitor analysis"""
    competitors: List[Dict[str, Any]] = Field(
        description="List of real competitors with name, description, website (if known), funding_stage, strengths (list), weaknesses (list), similarity_score (0-1)"
    )
    market_landscape: str = Field(description="Brief description of the competitive landscape")
    total_funding_in_space: Optional[str] = Field(default=None, description="Estimated total VC funding in this space")


class AIProblemAnalysis(BaseModel):
    """AI-generated problem validation"""
    problem_exists: bool = Field(description="Whether this is a real problem people have")
    problem_severity: str = Field(description="'hair-on-fire', 'significant', or 'nice-to-have'")
    search_volume: str = Field(description="'high', 'medium', or 'low' - estimated search volume for this problem")
    evidence: List[str] = Field(description="Evidence the problem exists (studies, statistics, trends)")
    target_audience_size: Optional[str] = Field(default=None, description="Estimated size of target audience")
    willingness_to_pay: str = Field(description="'high', 'medium', or 'low' - likelihood people would pay for a solution")


class AIMarketAnalysis(BaseModel):
    """AI-generated market analysis"""
    industry: str = Field(description="Detected industry category (e.g., 'health', 'fintech', 'productivity')")
    industry_category: str = Field(description="Full category path like 'Health & Wellness > Digital Health > Consumer'")
    market_timing: str = Field(description="'excellent', 'good', 'challenging', or 'poor'")
    market_timing_reasons: List[str] = Field(description="Why now is or isn't the right time")
    market_saturation: str = Field(description="'blue-ocean', 'growing', 'crowded', or 'saturated'")
    estimated_tam: str = Field(description="Total Addressable Market estimate like '$15B'")
    growth_rate: Optional[str] = Field(default=None, description="Industry growth rate if known")


class AIViabilityAnalysis(BaseModel):
    """AI-generated viability analysis"""
    viability_score: int = Field(ge=0, le=100, description="Overall viability score 0-100")
    viability_breakdown: Dict[str, int] = Field(
        description="Breakdown scores: problem_validation, competitive_landscape, market_timing, market_opportunity (each 0-100)"
    )
    differentiation_opportunities: List[Dict[str, str]] = Field(
        description="List of opportunities with 'opportunity', 'difficulty' (easy/medium/hard), 'impact' (high/medium/low)"
    )
    unique_angles: List[str] = Field(description="Specific ways this idea could differentiate from competitors")
    go_no_go: str = Field(description="'GO', 'CAUTION', 'PIVOT', or 'STOP'")
    verdict: str = Field(description="One sentence summary of the recommendation")
    verdict_reasons: List[str] = Field(description="3-5 reasons for the verdict")
    next_steps: List[Dict[str, str]] = Field(
        description="Prioritized next steps with 'step', 'why', 'priority' (critical/high/medium)"
    )
    pivot_suggestions: Optional[List[str]] = Field(default=None, description="Alternative directions if PIVOT recommended")


class AIFullIdeaValidation(BaseModel):
    """Complete AI-powered idea validation response"""
    # Executive Summary (NEW)
    executive_summary: str = Field(description="2-3 sentence plain English summary answering 'Should I pursue this?'")

    # Industry detection
    discovered_industry: str = Field(description="Detected industry (health, fintech, productivity, etc.)")
    industry_category: str = Field(description="Full category path")

    # Target Customer Profile (NEW)
    target_customer: Dict[str, Any] = Field(
        description="Ideal customer profile with 'demographics' (age, income, location), 'psychographics' (values, pain points), 'day_in_life' (typical scenario)"
    )

    # Competitors
    discovered_competitors: List[Dict[str, Any]] = Field(description="Real competitors with full analysis")
    market_landscape: str = Field(description="Competitive landscape description")

    # Problem validation
    problem_exists: bool
    problem_severity: str = Field(description="'hair-on-fire', 'significant', or 'nice-to-have'")
    search_volume: str = Field(description="'high', 'medium', or 'low'")
    problem_evidence: List[str]

    # Revenue Model (NEW)
    revenue_model: Dict[str, Any] = Field(
        description="Monetization strategy with 'suggested_models' (list of pricing models), 'price_range' (low/mid/high estimates), 'competitors_monetization' (how competitors charge)"
    )

    # Market analysis
    market_timing: str = Field(description="'excellent', 'good', 'challenging', or 'poor'")
    market_timing_reasons: List[str]
    market_saturation: str = Field(description="'blue-ocean', 'growing', 'crowded', or 'saturated'")
    estimated_tam: str
    market_trends: List[str] = Field(description="Key trends supporting or threatening this idea")

    # Viability
    viability_score: int = Field(ge=0, le=100)
    viability_breakdown: Dict[str, int]

    # Key Risks (NEW)
    key_risks: List[Dict[str, str]] = Field(
        description="Top risks with 'risk', 'severity' (high/medium/low), 'mitigation' (how to address)"
    )

    # Differentiation
    differentiation_opportunities: List[Dict[str, str]]
    unique_angles: List[str]

    # Validation Experiments (NEW)
    validation_experiments: List[Dict[str, str]] = Field(
        description="Pre-build tests with 'experiment', 'effort' (low/medium/high), 'what_it_proves'"
    )

    # Resource Estimate (NEW)
    resource_estimate: Dict[str, Any] = Field(
        description="What's needed: 'budget_range' (min-max), 'team_roles' (list), 'tech_stack' (list), 'timeline_to_mvp' (weeks/months)"
    )

    # Success Metrics (NEW)
    success_metrics: List[Dict[str, str]] = Field(
        description="KPIs with 'metric', 'target', 'timeframe'"
    )

    # Verdict
    go_no_go: str = Field(description="'GO', 'CAUTION', 'PIVOT', or 'STOP'")
    verdict: str
    verdict_reasons: List[str]

    # Next steps
    next_steps: List[Dict[str, str]]
    pivot_suggestions: Optional[List[str]] = None


# AI Client cache - stores clients by provider
_ai_clients: Dict[str, Any] = {}


def get_ai_client(provider: Optional[str] = None) -> tuple[Any, str, str]:
    """
    Get or create the AI client for idea validation.

    Args:
        provider: "claude", "grok", or None (auto-detect based on available API keys)

    Returns:
        tuple of (client, provider_name, model_name) or (None, None, None) if unavailable
    """
    global _ai_clients

    if not AI_AVAILABLE:
        return None, None, None

    # Auto-detect provider if not specified
    if provider is None:
        # Prefer Claude for deep analysis, but use what's available
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "claude"
        elif os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"):
            provider = "grok"
        else:
            logger.warning("No AI API keys found - falling back to simulated idea validation")
            return None, None, None

    # Return cached client if available
    if provider in _ai_clients:
        client, model = _ai_clients[provider]
        return client, provider, model

    try:
        if provider == "claude":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set")
                return None, None, None
            base_client = anthropic.Anthropic(api_key=api_key)
            client = instructor.from_anthropic(base_client)
            model = "claude-sonnet-4-20250514"
            _ai_clients[provider] = (client, model)
            logger.info(f"AI client initialized: Claude ({model})")
            return client, provider, model

        elif provider == "grok":
            api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
            if not api_key:
                logger.warning("XAI_API_KEY/GROK_API_KEY not set")
                return None, None, None
            # Grok uses OpenAI-compatible API
            base_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            client = instructor.from_openai(base_client)
            model = "grok-3-latest"
            _ai_clients[provider] = (client, model)
            logger.info(f"AI client initialized: Grok ({model})")
            return client, provider, model

        else:
            logger.warning(f"Unknown provider: {provider}")
            return None, None, None

    except Exception as e:
        logger.error(f"Failed to initialize AI client ({provider}): {e}")
        return None, None, None


async def ai_validate_idea(
    idea: str,
    problem: Optional[str],
    target_users: Optional[str],
    known_competitors: Optional[List[str]],
    provider: Optional[str] = None
) -> tuple[AIFullIdeaValidation, str, str]:
    """
    Use AI to validate a business idea with real competitor and market analysis.

    Args:
        idea: The business idea to validate
        problem: Optional problem description
        target_users: Optional target users description
        known_competitors: Optional list of known competitors
        provider: "claude", "grok", or None (auto-detect)

    Returns:
        tuple of (AIFullIdeaValidation, provider_used, model_used)
    """
    client, provider_used, model = get_ai_client(provider)
    if client is None:
        raise ValueError("AI client not available")

    # Build the prompt
    user_input = f"Business Idea: {idea}"
    if problem:
        user_input += f"\nProblem it solves: {problem}"
    if target_users:
        user_input += f"\nTarget users: {target_users}"
    if known_competitors:
        user_input += f"\nCompetitors the user already knows about: {', '.join(known_competitors)}"

    system_prompt = """You are an expert business analyst and startup advisor helping FIRST-TIME ENTREPRENEURS validate their ideas. Provide honest, actionable, data-driven analysis that helps them decide whether to pursue this idea.

## Your Analysis Must Include:

### 1. Executive Summary
Start with a 2-3 sentence plain English summary that answers: "Should I pursue this?" Be direct.

### 2. Target Customer Profile
Define the ideal customer with:
- demographics: age range, income level, location, job type
- psychographics: values, frustrations, desires, behaviors
- day_in_life: A specific scenario showing their pain point

### 3. Competitor Discovery
Find 3-5 REAL companies that compete in this space:
- Actual company names that exist (not made up)
- Their actual strengths and weaknesses
- Funding stage if known (seed, series-a, public, etc.)
- Similarity score (0-1) based on how directly they compete
- Website URL if known

### 4. Problem Validation
- "hair-on-fire" = urgent, people actively seeking solutions NOW
- "significant" = clear pain point but manageable
- "nice-to-have" = would be good but not essential
- Include search_volume: "high", "medium", or "low"
- List 3-5 pieces of evidence the problem exists

### 5. Revenue Model
Suggest how they could make money:
- suggested_models: List 2-3 pricing models (subscription, freemium, one-time, etc.)
- price_range: {"low": "$X", "mid": "$Y", "high": "$Z"} based on market
- competitors_monetization: How do competitors charge?

### 6. Market Analysis
- market_timing: "excellent", "good", "challenging", or "poor"
- market_timing_reasons: Why now is or isn't the right time
- market_saturation: "blue-ocean", "growing", "crowded", or "saturated"
- estimated_tam: Total Addressable Market estimate (e.g., "$15B")
- market_trends: 3-5 trends supporting or threatening this idea

### 7. Key Risks
Identify 3-5 top risks with:
- risk: What could go wrong
- severity: "high", "medium", or "low"
- mitigation: How to address or reduce this risk

### 8. Validation Experiments
Suggest 3-5 tests they can run BEFORE building:
- experiment: What to test (landing page, survey, interviews, etc.)
- effort: "low", "medium", or "high"
- what_it_proves: What they'll learn

### 9. Resource Estimate
What they need to get started:
- budget_range: {"min": "$X", "max": "$Y"}
- team_roles: List of roles needed (e.g., ["developer", "designer"])
- tech_stack: Suggested technologies
- timeline_to_mvp: Estimated time (e.g., "2-3 months")

### 10. Success Metrics
3-5 KPIs to track:
- metric: What to measure
- target: What number to aim for
- timeframe: By when

### 11. Viability Scoring (0-100 overall)
Breakdown scores (each 0-100):
- problem_validation: Is the problem real and painful?
- competitive_landscape: How crowded is the market?
- market_timing: Is now the right time?
- market_opportunity: Is there room to grow?

### 12. Verdict
Be honest!
- "GO" (70+): Strong opportunity, proceed with validation
- "CAUTION" (50-69): Potential but needs refinement
- "PIVOT" (35-49): Core insight is there, but approach needs change
- "STOP" (<35): Significant headwinds, consider different problem

### 13. Next Steps
5-7 specific, actionable recommendations with:
- step: What to do
- why: Why it matters
- priority: "critical", "high", or "medium"

Be brutally honest but constructive. Use real market data and actual company names. If an idea has issues, explain why and suggest pivots."""

    try:
        if provider_used == "claude":
            # Anthropic uses messages.create
            response = client.messages.create(
                model=model,
                max_tokens=8192,  # Increased for comprehensive analysis
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}],
                response_model=AIFullIdeaValidation,
            )
        else:
            # Grok/OpenAI uses chat.completions.create
            response = client.chat.completions.create(
                model=model,
                max_tokens=8192,  # Increased for comprehensive analysis
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_model=AIFullIdeaValidation,
            )
        return response, provider_used, model
    except Exception as e:
        logger.error(f"AI idea validation failed ({provider_used}): {e}")
        raise


def detect_industry(idea: str, problem: str = None, target_users: str = None) -> tuple[str, str]:
    """Detect industry from idea description"""
    text = f"{idea} {problem or ''} {target_users or ''}".lower()

    scores = {}
    for industry, keywords in INDUSTRY_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[industry] = score

    if not scores:
        return "technology", "Technology > Software > General"

    best_industry = max(scores, key=scores.get)

    # Generate category path
    category_map = {
        "food": "Consumer > Food & Beverage > Meal Planning",
        "health": "Health & Wellness > Digital Health > Consumer",
        "productivity": "Software > Productivity > Personal",
        "saas": "Software > B2B SaaS > Tools",
        "e-commerce": "Commerce > E-commerce > Platform",
        "fintech": "Finance > FinTech > Consumer",
        "edtech": "Education > EdTech > Online Learning",
        "social": "Social > Community > Platform",
        "travel": "Travel > Online Travel > Consumer",
        "real_estate": "Real Estate > PropTech > Consumer",
    }

    return best_industry, category_map.get(best_industry, f"Technology > {best_industry.title()}")


def discover_competitors(industry: str, idea: str) -> list:
    """Find competitors based on industry and idea keywords"""
    base_competitors = COMPETITOR_DATABASE.get(industry, COMPETITOR_DATABASE.get("saas", []))

    # Calculate similarity scores based on idea keywords
    idea_lower = idea.lower()
    result = []
    for comp in base_competitors:
        # Simple keyword matching for similarity
        comp_text = f"{comp['name']} {comp['description']}".lower()
        common_words = set(idea_lower.split()) & set(comp_text.split())
        similarity = min(0.95, 0.4 + (len(common_words) * 0.1))

        result.append({
            "name": comp["name"],
            "description": comp["description"],
            "website": comp.get("website"),
            "funding_stage": comp.get("funding"),
            "strengths": comp["strengths"],
            "weaknesses": comp["weaknesses"],
            "similarity_score": round(similarity, 2)
        })

    # Sort by similarity
    result.sort(key=lambda x: x["similarity_score"], reverse=True)
    return result[:5]


def analyze_problem_validity(idea: str, problem: str = None) -> dict:
    """Analyze if the problem is real and significant"""
    text = f"{idea} {problem or ''}".lower()

    # Indicators of real problems
    pain_indicators = ["frustrating", "hate", "wish", "difficult", "expensive", "time-consuming",
                       "annoying", "complicated", "forget", "miss", "lose", "waste", "struggle"]
    pain_score = sum(1 for p in pain_indicators if p in text)

    # Determine severity
    if pain_score >= 3 or "hate" in text or "waste" in text:
        severity = "hair-on-fire"
    elif pain_score >= 1:
        severity = "significant"
    else:
        severity = "nice-to-have"

    # Generate evidence (simulated - in production would use search data)
    evidence = []
    if "meal" in text or "food" in text:
        evidence.append("\"meal planning\" has 40K+ monthly searches")
        evidence.append("73% of parents report struggling with weeknight dinners")
    elif "budget" in text or "money" in text:
        evidence.append("\"budgeting app\" has 90K+ monthly searches")
        evidence.append("78% of Americans live paycheck to paycheck")
    elif "productivity" in text or "task" in text:
        evidence.append("\"productivity app\" has 60K+ monthly searches")
        evidence.append("Average worker spends 28% of time on email management")
    elif "health" in text or "fitness" in text:
        evidence.append("\"health app\" has 100K+ monthly searches")
        evidence.append("Digital health market growing at 25% CAGR")
    else:
        evidence.append("Related searches indicate active problem-solving behavior")
        evidence.append("Forum discussions show users seeking solutions")

    return {
        "exists": True,
        "severity": severity,
        "search_volume": "high" if pain_score >= 2 else "medium",
        "evidence": evidence
    }


def calculate_viability(industry: str, competitors: list, problem: dict) -> dict:
    """Calculate overall viability score"""
    # Problem score (0-100)
    problem_score = {"hair-on-fire": 90, "significant": 70, "nice-to-have": 40}.get(problem["severity"], 50)

    # Competition score (fewer/weaker = higher)
    avg_similarity = sum(c["similarity_score"] for c in competitors) / max(len(competitors), 1)
    competition_score = int(100 - (avg_similarity * 60))  # High similarity = low score

    # Timing score (based on industry trends)
    timing_scores = {
        "health": 85, "food": 80, "fintech": 75, "productivity": 70,
        "edtech": 75, "saas": 65, "e-commerce": 55, "social": 50
    }
    timing_score = timing_scores.get(industry, 60)

    # Market opportunity (inverse of saturation)
    saturation_penalty = {"saturated": 30, "crowded": 50, "growing": 70, "blue-ocean": 90}
    num_competitors = len(competitors)
    if num_competitors >= 5:
        saturation = "crowded"
    elif num_competitors >= 3:
        saturation = "growing"
    else:
        saturation = "blue-ocean"
    market_score = saturation_penalty.get(saturation, 60)

    # Calculate overall
    overall = int((problem_score * 0.35) + (competition_score * 0.25) +
                  (timing_score * 0.20) + (market_score * 0.20))

    return {
        "overall": overall,
        "breakdown": {
            "problem_validation": problem_score,
            "competitive_landscape": competition_score,
            "market_timing": timing_score,
            "market_opportunity": market_score
        },
        "saturation": saturation
    }


def generate_differentiation_opportunities(competitors: list) -> list:
    """Generate differentiation opportunities based on competitor weaknesses"""
    opportunities = []
    weakness_map = {}

    # Collect all weaknesses
    for comp in competitors:
        for weakness in comp.get("weaknesses", []):
            weakness_lower = weakness.lower()
            if weakness_lower not in weakness_map:
                weakness_map[weakness_lower] = {"count": 0, "original": weakness}
            weakness_map[weakness_lower]["count"] += 1

    # Convert common weaknesses to opportunities
    for weakness, data in sorted(weakness_map.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
        if "expensive" in weakness or "price" in weakness:
            opportunities.append({
                "opportunity": "Price disruption - offer a more affordable solution",
                "difficulty": "medium",
                "impact": "high",
                "competitors_affected": data["count"]
            })
        elif "complex" in weakness or "learning curve" in weakness or "overwhelming" in weakness:
            opportunities.append({
                "opportunity": "Simplicity focus - make it dead simple to use",
                "difficulty": "medium",
                "impact": "high",
                "competitors_affected": data["count"]
            })
        elif "limited" in weakness or "basic" in weakness:
            opportunities.append({
                "opportunity": "Feature depth - go deeper on specific use cases",
                "difficulty": "medium",
                "impact": "medium",
                "competitors_affected": data["count"]
            })
        elif "ad" in weakness or "subscription" in weakness:
            opportunities.append({
                "opportunity": "Business model innovation - one-time purchase or freemium",
                "difficulty": "low",
                "impact": "medium",
                "competitors_affected": data["count"]
            })
        else:
            opportunities.append({
                "opportunity": f"Address competitor weakness: {data['original']}",
                "difficulty": "medium",
                "impact": "medium",
                "competitors_affected": data["count"]
            })

    return opportunities[:5]


def determine_verdict(viability: dict, competitors: list, problem: dict) -> dict:
    """Determine go/no-go verdict with reasons"""
    score = viability["overall"]

    if score >= 70:
        go_no_go = "GO"
        verdict = "This idea shows strong potential. The problem is real, and there's room to differentiate."
        reasons = [
            f"Problem severity is '{problem['severity']}' - people actively need solutions",
            f"Viability score of {score}/100 indicates good opportunity",
            "Identified clear differentiation paths from existing competitors"
        ]
    elif score >= 50:
        go_no_go = "CAUTION"
        verdict = "This idea has potential but needs refinement. Consider pivoting to a specific niche."
        reasons = [
            f"Moderate viability score of {score}/100 suggests challenges ahead",
            f"Market is {viability['saturation']} - differentiation is crucial",
            "Success will depend on execution and finding your unique angle"
        ]
    elif score >= 35:
        go_no_go = "PIVOT"
        verdict = "The core problem is worth solving, but your approach needs significant changes."
        reasons = [
            f"Low viability score of {score}/100 indicates high risk",
            f"Existing competitors are well-established",
            "Consider targeting a more specific niche or different customer segment"
        ]
    else:
        go_no_go = "STOP"
        verdict = "This idea faces significant headwinds. Consider a different problem space."
        reasons = [
            "Problem may not be severe enough to drive adoption",
            "Market is saturated with funded competitors",
            "Risk/reward ratio is unfavorable"
        ]

    return {
        "go_no_go": go_no_go,
        "verdict": verdict,
        "reasons": reasons
    }


def generate_next_steps(go_no_go: str, industry: str, competitors: list) -> list:
    """Generate actionable next steps based on verdict"""
    steps = []

    if go_no_go in ["GO", "CAUTION"]:
        steps.append({
            "step": "Talk to 10 potential customers this week",
            "why": "Validate that real people have this problem and would pay for a solution",
            "priority": "critical"
        })
        steps.append({
            "step": f"Sign up for {competitors[0]['name'] if competitors else 'a competitor'} and use it for a week",
            "why": "Understand exactly what works and what's frustrating about existing solutions",
            "priority": "high"
        })
        steps.append({
            "step": "Define your unique value proposition in one sentence",
            "why": "If you can't explain why you're different, customers won't understand either",
            "priority": "high"
        })
        steps.append({
            "step": "Build a landing page and test demand with ads ($100-200 budget)",
            "why": "Measure real interest before building anything",
            "priority": "medium"
        })
    else:  # PIVOT or STOP
        steps.append({
            "step": "Interview 5 people in your target audience about their biggest frustrations",
            "why": "You may discover a different, more painful problem worth solving",
            "priority": "critical"
        })
        steps.append({
            "step": "Look for underserved niches within this space",
            "why": "A specific niche (e.g., 'meal planning for diabetic seniors') may have less competition",
            "priority": "high"
        })
        steps.append({
            "step": "Analyze why existing solutions haven't fully solved the problem",
            "why": "There may be a regulatory, technical, or behavioral barrier worth investigating",
            "priority": "medium"
        })

    return steps


def generate_pivot_suggestions(industry: str, idea: str) -> list:
    """Generate pivot suggestions if needed"""
    suggestions = []

    if industry == "food":
        suggestions = [
            "Focus on a specific diet (keto, vegan, allergy-free) instead of general meal planning",
            "Target busy professionals instead of families - different pain points",
            "Add a social/community element - cooking with friends virtually",
            "Focus on ingredient waste reduction - eco-conscious angle"
        ]
    elif industry == "health":
        suggestions = [
            "Focus on a specific condition (anxiety, sleep, chronic pain)",
            "Target corporate wellness programs - B2B instead of B2C",
            "Focus on prevention for a specific demographic (new parents, seniors)",
            "Add accountability/community features competitors lack"
        ]
    elif industry == "productivity":
        suggestions = [
            "Focus on a specific profession (lawyers, real estate agents, designers)",
            "Build for a specific workflow (client communication, invoicing, scheduling)",
            "Target teams of 2-10 people - too small for enterprise tools, too big for personal apps",
            "Focus on reducing meetings specifically"
        ]
    elif industry == "fintech":
        suggestions = [
            "Focus on a specific financial goal (house down payment, wedding, emergency fund)",
            "Target freelancers/gig workers with irregular income",
            "Focus on financial education for Gen Z specifically",
            "Build for couples managing money together"
        ]
    else:
        suggestions = [
            "Narrow down to a specific customer segment",
            "Focus on one feature done exceptionally well",
            "Consider a B2B angle instead of B2C",
            "Look for underserved geographic markets"
        ]

    return suggestions


# In-memory storage for idea validations
idea_validation_db: Dict[str, dict] = {}


@app.post("/api/idea-validation")
async def validate_idea(request: IdeaValidationRequest):
    """Validate a business idea - AI-powered when available, with fallback to simulated analysis"""
    validation_id = f"idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Try AI-powered validation first (with optional provider selection)
    client, detected_provider, model = get_ai_client(request.provider)
    if client is not None:
        try:
            logger.info(f"Using AI-powered idea validation ({detected_provider}/{model}) for: {request.idea[:50]}...")
            ai_result, provider_used, model_used = await ai_validate_idea(
                idea=request.idea,
                problem=request.problem,
                target_users=request.target_users,
                known_competitors=request.known_competitors,
                provider=request.provider
            )

            # Convert AI result to response format
            result = {
                "id": validation_id,
                "idea": request.idea,
                "timestamp": datetime.now().isoformat(),
                "ai_powered": True,  # Flag to indicate this used real AI
                "provider": provider_used,  # Which AI provider was used
                "model": model_used,  # Which model was used

                # Executive Summary (NEW)
                "executive_summary": ai_result.executive_summary,

                # From AI
                "discovered_industry": ai_result.discovered_industry,
                "industry_category": ai_result.industry_category,

                # Target Customer (NEW)
                "target_customer": ai_result.target_customer,

                # Competitors
                "discovered_competitors": ai_result.discovered_competitors,
                "market_landscape": ai_result.market_landscape,

                # Problem validation
                "problem_exists": ai_result.problem_exists,
                "problem_severity": ai_result.problem_severity,
                "search_volume": ai_result.search_volume,
                "problem_evidence": ai_result.problem_evidence,

                # Revenue Model (NEW)
                "revenue_model": ai_result.revenue_model,

                # Viability
                "viability_score": ai_result.viability_score,
                "viability_breakdown": ai_result.viability_breakdown,

                # Key Risks (NEW)
                "key_risks": ai_result.key_risks,

                # Differentiation
                "differentiation_opportunities": ai_result.differentiation_opportunities,
                "unique_angles": ai_result.unique_angles,

                # Validation Experiments (NEW)
                "validation_experiments": ai_result.validation_experiments,

                # Resource Estimate (NEW)
                "resource_estimate": ai_result.resource_estimate,

                # Success Metrics (NEW)
                "success_metrics": ai_result.success_metrics,

                # Market
                "market_timing": ai_result.market_timing,
                "market_timing_reasons": ai_result.market_timing_reasons,
                "market_saturation": ai_result.market_saturation,
                "estimated_tam": ai_result.estimated_tam,
                "market_trends": ai_result.market_trends,

                # Verdict
                "go_no_go": ai_result.go_no_go,
                "verdict": ai_result.verdict,
                "verdict_reasons": ai_result.verdict_reasons,

                # Next steps
                "next_steps": ai_result.next_steps,
                "pivot_suggestions": ai_result.pivot_suggestions
            }

            idea_validation_db[validation_id] = result
            logger.info(f"AI idea validation complete ({provider_used}): {ai_result.go_no_go} ({ai_result.viability_score}/100)")
            return result

        except Exception as e:
            logger.warning(f"AI idea validation failed, falling back to simulated: {e}")
            # Fall through to simulated version

    # Fallback: Simulated analysis (when AI is not available)
    logger.info(f"Using simulated idea validation for: {request.idea[:50]}...")

    # Detect industry
    industry, industry_category = detect_industry(request.idea, request.problem, request.target_users)

    # Discover competitors
    competitors = discover_competitors(industry, request.idea)

    # Add any known competitors the user provided
    if request.known_competitors:
        for known in request.known_competitors:
            if not any(c["name"].lower() == known.lower() for c in competitors):
                competitors.append({
                    "name": known,
                    "description": "User-provided competitor",
                    "website": None,
                    "funding_stage": "unknown",
                    "strengths": ["Market presence"],
                    "weaknesses": ["Unknown"],
                    "similarity_score": 0.7
                })

    # Validate the problem
    problem_analysis = analyze_problem_validity(request.idea, request.problem)

    # Calculate viability
    viability = calculate_viability(industry, competitors, problem_analysis)

    # Generate differentiation opportunities
    differentiation = generate_differentiation_opportunities(competitors)

    # Unique angles based on idea
    unique_angles = [
        "Focus on a specific underserved niche",
        "Superior user experience and simplicity",
        "Different business model (pricing, delivery)",
        "Better integration with existing tools",
        "Community-driven approach"
    ]

    # Market timing assessment
    timing_reasons = {
        "health": ["Post-pandemic health awareness at all-time high", "Remote work driving digital health adoption", "Insurance companies now covering digital solutions"],
        "food": ["Inflation driving home cooking interest", "Sustainability concerns rising", "Meal kit fatigue creating openings"],
        "productivity": ["Remote work is permanent for many", "Tool fatigue creating consolidation opportunity", "AI making new features possible"],
        "fintech": ["Economic uncertainty driving financial planning", "Gen Z entering workforce needs new tools", "Open banking enabling innovation"],
    }
    market_timing = "good" if viability["breakdown"]["market_timing"] >= 70 else "challenging"
    timing_explanation = timing_reasons.get(industry, ["Market conditions are stable", "Look for emerging trends to capitalize on"])

    # Determine verdict
    verdict_data = determine_verdict(viability, competitors, problem_analysis)

    # Generate next steps
    next_steps = generate_next_steps(verdict_data["go_no_go"], industry, competitors)

    # Pivot suggestions if needed
    pivot_suggestions = None
    if verdict_data["go_no_go"] in ["PIVOT", "CAUTION"]:
        pivot_suggestions = generate_pivot_suggestions(industry, request.idea)

    # TAM estimate based on industry
    tam_estimates = {
        "food": "$15B", "health": "$25B", "productivity": "$12B", "saas": "$200B",
        "fintech": "$50B", "edtech": "$8B", "e-commerce": "$500B", "social": "$100B"
    }

    result = {
        "id": validation_id,
        "idea": request.idea,
        "timestamp": datetime.now().isoformat(),
        "ai_powered": False,  # Flag to indicate this used simulated analysis
        "provider": None,  # No AI provider (simulated)
        "model": None,  # No AI model (simulated)

        # Executive Summary
        "executive_summary": f"This is a simulated analysis. {verdict_data['verdict']} Connect an AI API key for real market research.",

        # Discovered
        "discovered_industry": industry,
        "industry_category": industry_category,

        # Target Customer (simulated)
        "target_customer": {
            "demographics": "Adults 25-45, middle to upper income, urban/suburban",
            "psychographics": "Tech-savvy, values efficiency, frustrated with current solutions",
            "day_in_life": "A busy professional who encounters this problem daily and wishes for a better solution"
        },

        "discovered_competitors": competitors,
        "market_landscape": f"The {industry} market has several established players. Competition level: {viability['saturation']}.",

        # Problem validation
        "problem_exists": problem_analysis["exists"],
        "problem_severity": problem_analysis["severity"],
        "search_volume": problem_analysis["search_volume"],
        "problem_evidence": problem_analysis["evidence"],

        # Revenue Model (simulated)
        "revenue_model": {
            "suggested_models": ["Subscription (monthly/annual)", "Freemium with premium features", "Usage-based pricing"],
            "price_range": {"low": "$9/mo", "mid": "$29/mo", "high": "$99/mo"},
            "competitors_monetization": "Most competitors use subscription-based models"
        },

        # Viability
        "viability_score": viability["overall"],
        "viability_breakdown": viability["breakdown"],

        # Key Risks (simulated)
        "key_risks": [
            {"risk": "Strong existing competition", "severity": "medium", "mitigation": "Focus on underserved niche"},
            {"risk": "Customer acquisition cost", "severity": "medium", "mitigation": "Start with organic/community growth"},
            {"risk": "Technical complexity", "severity": "low", "mitigation": "Start with MVP, iterate based on feedback"}
        ],

        # Differentiation
        "differentiation_opportunities": differentiation,
        "unique_angles": unique_angles,

        # Validation Experiments (simulated)
        "validation_experiments": [
            {"experiment": "Landing page test", "effort": "low", "what_it_proves": "Demand for the solution exists"},
            {"experiment": "Customer interviews (10-15)", "effort": "medium", "what_it_proves": "Problem severity and willingness to pay"},
            {"experiment": "Competitor user interviews", "effort": "medium", "what_it_proves": "Gaps in current solutions"}
        ],

        # Resource Estimate (simulated)
        "resource_estimate": {
            "budget_range": {"min": "$5,000", "max": "$50,000"},
            "team_roles": ["Full-stack developer", "Designer (part-time)", "Founder doing sales/marketing"],
            "tech_stack": ["React/Next.js", "Node.js or Python", "PostgreSQL", "Vercel/Railway"],
            "timeline_to_mvp": "2-3 months"
        },

        # Success Metrics (simulated)
        "success_metrics": [
            {"metric": "Landing page signups", "target": "500", "timeframe": "First month"},
            {"metric": "Paid customers", "target": "50", "timeframe": "First 3 months"},
            {"metric": "Monthly recurring revenue", "target": "$2,000", "timeframe": "First 6 months"}
        ],

        # Market
        "market_timing": market_timing,
        "market_timing_reasons": timing_explanation,
        "market_saturation": viability["saturation"],
        "estimated_tam": tam_estimates.get(industry, "$10B"),
        "market_trends": [
            f"Growing interest in {industry} solutions",
            "Digital transformation accelerating adoption",
            "Increasing willingness to pay for productivity tools"
        ],

        # Verdict
        "go_no_go": verdict_data["go_no_go"],
        "verdict": verdict_data["verdict"],
        "verdict_reasons": verdict_data["reasons"],

        # Next steps
        "next_steps": next_steps,
        "pivot_suggestions": pivot_suggestions
    }

    idea_validation_db[validation_id] = result
    return result


@app.get("/api/idea-validation")
async def list_idea_validations():
    """List all idea validations"""
    return list(idea_validation_db.values())


@app.get("/api/idea-validation/{validation_id}")
async def get_idea_validation(validation_id: str):
    """Get a specific idea validation"""
    if validation_id not in idea_validation_db:
        raise HTTPException(status_code=404, detail="Validation not found")
    return idea_validation_db[validation_id]


# ============================================================================
# Market Research Endpoints (Legacy)
# ============================================================================

@app.post("/api/market-research")
async def run_market_research(request: MarketResearchRequest):
    research_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    research_result = {
        "id": research_id,
        "query": request.query,
        "competitors": request.competitors or [],
        "industry": request.industry,
        "status": "completed",
        "insights": [
            {
                "type": "trend",
                "title": "Market Growth",
                "description": f"The {request.industry or 'target'} market shows steady growth potential.",
                "confidence": 0.75
            },
            {
                "type": "opportunity",
                "title": "Feature Gap",
                "description": "Analysis suggests opportunity in underserved user segments.",
                "confidence": 0.68
            },
            {
                "type": "risk",
                "title": "Competition",
                "description": f"Identified {len(request.competitors or [])} direct competitors.",
                "confidence": 0.82
            }
        ],
        "recommendations": [
            "Focus on differentiation through superior UX",
            "Consider freemium model for market penetration",
            "Target underserved mid-market segment"
        ],
        "created_at": datetime.now().isoformat()
    }
    market_research_db[research_id] = research_result
    return research_result


@app.get("/api/market-research")
async def list_market_research():
    return list(market_research_db.values())


@app.get("/api/market-research/{research_id}")
async def get_market_research(research_id: str):
    if research_id not in market_research_db:
        raise HTTPException(status_code=404, detail="Research not found")
    return market_research_db[research_id]


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

